# This file contains possible attributes and values you can use to configure sqsend,
# sets connections string, user, name which is distributed to search heads.
#
# This is an sqsend.conf in $SPLUNK_HOME/etc/sqsend/default.  To set custom configurations,
# place an sqsend.conf $SPLUNK_HOME/etc/sqsend/local.


#*******
# GENERAL SETTINGS:
# This following attribute/value pairs are valid for all stanzas.  The [sqsend] stanza
# is required. Additional stanzas can be define which can be used by user by specifying instance=<string>.
# If your environment has multiple SQS QUEUES
#*******


[sqsend]
aws_region = <AWS_REGION>
* aws region code
* EAMPLE: us-east-1
* REQUIRED

AKEY = <AWS_Access_Key_ID>
* AWS Access Key ID
* EXAMPLE: AKIAIC7V........
* REQUIRED

ASECRET = <AWS_Secret_Access_Key>
* AWS Secret Access Key
* EXAMPLE: Zre5mpFcK0X
* REQUIRED

sqsqueue = <SQS_QUEUE_NAME>
* Name of  SQS QUEUE
* EXAMPLE: myqueue
* REQUIRED
