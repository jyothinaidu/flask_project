__author__ = 'james'


import pusher

p = pusher.Pusher(
  app_id='140295',
  key='75ef3e062925ca5a618e',
  secret='1b512d861251d0e3ed77',
  ssl=True,
  port=443
)
p.trigger('test_channel', 'my_event', {'message': 'Hey is this thing on???'})

