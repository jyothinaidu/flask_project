import re
from app.users.model import *

cons_users = ConsumerUser.query.filter(ConsumerUser.email_verified == 'f').all()
s = open('api.log', 'r').read()


for c in cons_users:

    m = re.search('.*' + c.email_verification_token + '.*500.*', s, re.MULTILINE)
    if m:
        print c.email_address


