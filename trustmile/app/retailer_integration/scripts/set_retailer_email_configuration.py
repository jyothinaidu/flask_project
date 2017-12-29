# coding=UTF-8

from app import db
from app.retailer_integration.model import Retailer

website_name = 'indulgehq'

username='indulgehq@trustmile.email'
password='zBHilKT6lktiC9pYoufv'

r = Retailer.get( website_name=website_name)
r.email_server_configuration = {
        "imapServer": 'secure.emailsrvr.com',
        "imapPort": '993',
        "imapUsername": username,
        "imapPassword": password
  }

r.email_integration_configuration = {
    'from_email_addresses': ['*'],
}

parsing_set = [ #extractor_sets
    {
            'position_extractor': None,
            'repeat': False,
            'tracking_number_parsing': False,
            'extractors': [

                {
                'start': u'Items On Order #',
                'end': '\n',
                'item': 'order_id',
                'repeat': False
                }
            ]
    },
    {
            'position_extractor': {
                'start': u'Consignment #',
                'end': '\n[0-9]+?\n',
                'capture': u'(.*?)',
                'item': 'null',
                'repeat': False
            },
            'repeat': True,
            'tracking_number_parsing': False,
            'extractors': [

                {
                'start': u'.*?\n.*?\n(EBay ID:.*?\n){0,1}',
                #'end': u'(\s*-\s*?){0,1}([0-9]+(Kg|g)[^\n]*?){0,1}',
                'end': u'(-\s*?){0,1}([0-9]+(Kg|g).*?){0,1}(Road(.*?)){0,1}\n',
                'item': 'courier',
                'repeat': False
                },
                {
                'start': u'',
                'end': '\n(([0-9]+?)|(Please note:))\n',
                'item': 'tracking number',
                'repeat': False
                }


            ]
    }
]





r.email_integration_configuration['parsing_set'] = parsing_set

db.session.add(r)
db.session.commit()


