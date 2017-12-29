from app.retailer_integration.model import Retailer
from app.retailer_integration.EmailGateway import EmailGateway

r= Retailer()
r.email_server_configuration

r.email_server_configuration = {
    "imapServer": 'secure.emailsrvr.com',
    "imapPort": '993',
    "imapUsername": 'indulehq.email',
    "imapPassword": 'password1234'
}

r.email_server_configuration({"imapPassword": "zBHilKT6lktiC9pYoufv", "imapServer": "secure.emailsrvr.com", "imapPort": "993", "imapUsername": "indulgehq@trustmile.email"})

