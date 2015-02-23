import json
import sys
import os
import datetime
from platform import system
from splunk.clilib import cli_common as cli
from splunklib.searchcommands import \
    dispatch, StreamingCommand, Configuration, Option, validators

import boto.sqs
from boto.sqs.message import Message


# servicenow severity
# http://wiki.servicenow.com/index.php?title=Integrating_External_Events_with_Event_Management Using_the_Python_Script
# 1 = Critical, 2 = Major, 3 = Minor, 4 = Warning, or 0 = Clear.


def getStanza(conf, stanza):
    """
    :param conf: splunk conf file
    :param stanza: stanza (entry) from conf file
    :return: returns dictionary of setting
    """
    appdir = os.path.dirname(os.path.dirname(__file__))
    conf = "%s.conf" % conf
    apikeyconfpath = os.path.join(appdir, "default", conf)
    apikeyconf = cli.readConfFile(apikeyconfpath)
    localconfpath = os.path.join(appdir, "local", conf)
    if os.path.exists(localconfpath):
        localconf = cli.readConfFile(localconfpath)
        for name, content in localconf.items():
            if name in apikeyconf:
                apikeyconf[name].update(content)
            else:
                apikeyconf[name] = content
    return apikeyconf[stanza]


def validateSeverity(severity):
    try:
        severity = int(severity)
        if not (severity >= 1 or severity <= 5):
            self.logger.debug('SqSendCommand: %s, %s' % 'sev is less than 1 or greater than 5', self)
            exit(1)
    except Exception as e:
        self.logger.debug('SqSendCommand: %s, %s' % e, self)


class SQSClient(object):
    """
    A simple client that can submit events to SQS
    """

    def __init__(self, aws_region, aws_access_key_id, aws_secret_access_key, sqsqueue):
        self.conn = boto.sqs.connect_to_region(aws_region,
                                               aws_access_key_id=aws_access_key_id,
                                               aws_secret_access_key=aws_secret_access_key)

        self.q = self.conn.create_queue(sqsqueue)


    def submit_event(self, data):
        m = Message()
        m.set_body(data)
        self.q.write(m)


@Configuration()
class SqSendCommand(StreamingCommand):
    """ %(sqs sender)

    ##Syntax

    %(sqsend source=splunk type=\"storage\" sev=\"2\" node=host)

    ##Description

    %(sends data to from Splunk to SQS for Service Now )

    """
    source = Option(
        doc='''**Syntax:** **source=***<string>*
         **Description:** The source, or monitoring tool, that generates the event, such as Icinga. ''')

    type = Option(
        doc='''**Syntax:** **type=***<string>*
         **Description:** The type of event, such as storage or performance. ''')

    res = Option(
        doc='''**Syntax:** **resource=***<string>*
         **Description:** The resource on the node that generates the event, such as disk or database server. ''')

    sev = Option(
        doc='''**Syntax:** **sev=***<string>*
         **Description:** The severity of the event: 1 = Critical, 2 = Major, 3 = Minor, 4 = Warning, or 0 = Clear. ''')

    desc = Option(
        doc='''**Syntax:** **description=***<string>*
         **Description:** A description of the event. ''')

    addinfo = Option(
        doc='''**Syntax:** **Description=***<string>*
         **Description:** Additional information for the event. This information can be used for third-party integration or other post-alert processing. ''')

    cid = Option(
        doc='''**Syntax:** **Description=***<string>*
         **Description:** A JSON string that represents a configuration item ''')

    node = Option(
        doc='''
        **Syntax:** **node=***<value>*
        **Description:** The physical device or virtual entity that is being monitored. ''',
        require=False, validate=validators.Fieldname())

    url = Option(
        doc='''
        **Syntax:** **url=***<value>*
        **Description:** The physical device or virtual entity that is being monitored. ''',
        require=False)

    alert = Option(
        doc='''**Syntax:** **Description=***<string>*
         **Description:** A JSON string that represents a configuration item ''',
        require=True)

    group = Option(
        doc='''**Syntax:** **Description=***<string>*
         **Description:** A JSON string that represents a configuration item ''',
        require=True)

    env = Option(
        doc='''**Syntax:** **Description=***<string>*
         **Description:** A JSON string that represents a configuration item ''',
        require=True)

    feature = Option(
        doc='''**Syntax:** **Description=***<string>*
         **Description:** A JSON string that represents a configuration item ''',
        require=True)



    def stream(self, records):
        self.logger.debug('SqSendCommand: %s' % self)
        try:
            conf = getStanza('sqsend', 'sqsend')
            aws_region = conf['aws_region']
            aws_access_key_id = conf['AKEY']
            aws_secret_access_key = conf['ASECRET']
            sqsqueue = conf['sqsqueue']
        except Exception as e:
            self.logger.debug('SqSendCommand: %s, %s' % e, self)
            exit(1)

        sqs = SQSClient(aws_region=aws_region,
                        aws_access_key_id=aws_access_key_id,
                        aws_secret_access_key=aws_secret_access_key,
                        sqsqueue=sqsqueue)

        for record in records:
            if not self.source:
                source = 'splunk'
            else:
                source = self.source

            # loading fields into dict
            timeOfEvent = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            message = {}
            message['source'] = source
            message['u_source_url'] = self.url if not self.url in record else record[self.url]
            message['node'] = self.node if not self.node in record else record[self.node]
            message['severity'] = self.sev if not self.sev in record else record[self.sev]
            message['alert'] = self.alert if not self.alert in record else record[self.alert]
            message['type'] = self.type if not self.type in record else record[self.type]
            message['resource'] = self.res if not self.res in record else record[self.res]
            message['description'] = self.desc if not self.desc in record else record[self.desc]
            message['additional_info'] = self.addinfo if not self.addinfo in record else record[self.addinfo]
            message['ci_identifier'] = self.cid if not self.cid in record else record[self.cid]
            message['timeOfEvent'] = timeOfEvent

            message = {k: v for k, v in message.items() if v}

            # using json to convert dict to json and scrub non ASCII characters
            jmessage = json.dumps(json.loads(json.JSONEncoder().encode(message)),
                                  indent=4,
                                  sort_keys=True,
                                  ensure_ascii=True)
            notsent = True
            attempts = 0
            # attempting to send message
            while notsent:
                attempts += 1
                if attempts > 3:
                    break
                if (message['alert'] == "1"):
                    try:
                        sqs.submit_event(jmessage)
                        notsent = False
                        record['status'] = 'sent'
                    except Exception as e:
                        record['status'] = 'notsent'
                        record['error_message'] = e
                    record = dict(record.items() + message.items())
                else:
                    record['status'] = 'notsent'
                    record = dict(record.items() + message.items())
                    break
            yield record
            exit()

dispatch(SqSendCommand, sys.argv, sys.stdin, sys.stdout, __name__)