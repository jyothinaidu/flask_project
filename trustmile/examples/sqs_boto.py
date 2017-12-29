__author__ = 'james'

import boto.sqs
import time

conn = boto.sqs.connect_to_region(
    "ap-southeast-2",
    aws_access_key_id='AKIAJ3A42Y5D77AJTSHQ',
    aws_secret_access_key='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')

q = conn.get_queue('seal-impressions-dev')
#Queue(https://queue.amazonaws.com/411358162645/myqueue)
from boto.sqs.message import Message
# m = Message()
# m.set_body('This is my first message.')
# q.write(m)

# VGhpcyBpcyBteSBmaXJzdCBtZXNzYWdlLg==

time.sleep(10)

rs = q.get_messages()
print "Num Messages: {0}".format(len(rs))
for m in rs:
    print "Message: {0}".format(m.get_body())
    q.delete_message(m)



