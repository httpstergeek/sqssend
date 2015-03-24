Copyright (C) 2006-2015 Zillow Group, Inc. All Rights Reserved.

SQS Send - A Splunk Search Command sending data to a SQS queue
=================

SQS Send  now is a Splunk Search command which send formatted data to an SQS queue to be consumed by Service Snow
This Splunk utilizes boto python modules.

##Supports:
* Supports multiple SQS queues 





Requirements
---------

* This version has been test on 6.x and should work on 5.x.

* App is known to work on Linux,and Mac OS X, but has not been tested on other operating systems. Window should work

* App requires network access to Service Now instance

* Miminum of 2 GB RAM and 1.8 GHz CPU.



Prerequisites
---------

* Splunk version 6.x or Higher

You can download it [Splunk][splunk-download].  And see the [Splunk documentation][] for instructions on installing and more.
[Splunk]:http://www.splunk.com
[Splunk documentation]:http://docs.splunk.com/Documentation/Splunk/latest/User
[splunk-download]:http://www.splunk.com/download


Installation instructions
---------

1) copy repo into $SPLUNK_HOME/etc/apps/.

2) create $SPLUNK_HOME/etc/apps/sqsend/local/sqsend.conf.

3) configure [sqsend] stanza with url to sqs queue info.

Example Command
---------
```
...| sqsend type="Storage"  res="Disk E:" sev="1" desc="Disk is almost full" node​=host
    OR
...| sqsend type="Storage"  res="Disk E:" sev="1" desc="Disk is almost full" node​=host instance=stage
```
Recommendations
---------

It is recommend that this be installed on an Search head.
