from app.users.model import Address
from app.users.serialize import *

a = Address.query.filter(Address.id == 'bf33be67-1b8f-49de-9edc-c905fe47bb6e').first()

s = UserAddressSchema().dump(a).data

print s