from app.retailer_integration.model import Retailer
from app.retailer_integration.ParsingRulesDev import ParsingRulesDev
import json
import os

parsing_set = [ #extractor_sets
    {
            'start_position': None,
            'repeat': False,
            'tracking_number_parsing': False,
            'format': 'text', #HTML,text
            'location': 'subject',
            'extractors': [

                {
                'start': u'Items On Order #',
                'end': u'$',
                'item': 'order_id',
                'repeat': False
                }
            ]
    },
    {
            'start_position': {
                'start': u'===HREF===',
                'end': '\n',
                'capture': u'(.*?)',
                'item': 'null',
                'repeat': False
            },
            'repeat': True,
            'tracking_number_parsing': False,
            'removeTags': ['br','i','b','strong','span','font'],
            'extractors': [

                {
                'start': u'trustmile.com(.*?)courier=',
                'end': u'&',
                'item': 'courier',
                'repeat': False
                },
                {
                'start': u'trackingNumber=',
                'end': '\n',
                'item': 'tracking number',
                'repeat': False
                }


            ]
    }
]


pr = ParsingRulesDev()
pr.set_imap('indulgehq@trustmile.email', 'zBHilKT6lktiC9pYoufv', 'secure.emailsrvr.com', '993')

#we only want to read the email once, after that we will read form disk
file_prefix = 'indulgehq_'
uid = 300
file_name = file_prefix + str(uid) + '.txt'

if os.path.isfile(file_name):
    email_dict = json.load(open(file_name))
else:
    email_dict = pr.load_email(uid)
    email_dict['date'] = '' #the date format used isn't serializable by json
    json.dump(email_dict, open(file_name, 'w'))


results = []
for extractor_set in parsing_set:
    print extractor_set
    print pr.get_email_text(email_dict,extractor_set)
    result = pr.test_rules(email_dict,extractor_set)

    results.extend(result)

    print result
    print '------------------------------------------'


#print results


print pr.format_results_for_db(results)


