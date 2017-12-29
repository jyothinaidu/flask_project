import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from . import AppTest
import sys
from app.retailer_integration.model import *
from app.deliveries.model import *

from datetime import datetime
from app.retailer_integration.RetailerIntegration import RetailerIntegration
from app.retailer_integration.EmailGateway import EmailGateway
from app.retailer_integration.EmailWorker import EmailWorker
import config
import copy
from bs4 import BeautifulSoup


from app.ops.consumer_operations import AccountRegister

import mandrill
import time


#this file test V2 of retailer integration
# new parsing methods
# support multiple email servers

couriers_file_path = os.path.dirname(os.path.realpath(__file__))

test1_html = open( couriers_file_path + '/../tests/retailer_integration_case_1.html').read()
test1_subject = 'your order #N1234 - 2016-05-21'
test1_parsed = BeautifulSoup( test1_html, 'lxml').get_text( '\n', strip=True)

test1_config_1 = {

                    'parsing_set': [ #extractor_sets
                    {
                            'start_position': None,
                            'repeat': False,
                            'tracking_number_parsing': False,
                            'format': 'text', #HTML,text
                            'location': 'subject',
                            'extractors': [

                                {
                                'start': u'your order #',
                                'end': u'\s',
                                'item': 'order_id',
                                'repeat': False
                                }
                            ]
                    },
                    {
                            'start_position': None,
                            'stop_position': {
                                'start': '===HREF===',
                                'capture': '()',
                                'end': '\n',
                                'item': 'null',
                                'repeat': False
                            },


                            'repeat': False,
                            'location': 'body',
                            'extractors': [
                                {
                                'start': 'Your parcel has been dispatched via',
                                'end': '\n',
                                'item': 'courier',
                                'repeat': False
                                },
                                {
                                'start': 'Tracking Number',
                                'capture': '(.*?)',
                                'end': '\n',
                                'item': 'null',
                                'repeat': False
                                },
                                {
                                'start': '(.*?)\n',
                                'end': '\n',
                                'item': 'tracking number',
                                'repeat': True
                                }

                            ]
                    }
                    ]

   # Your parcel has been dispatched via
}



config1=    {
  "from_email_addresses": [ "retailer1@trustmile.com" ]
}
config1['parsing_set'] = test1_config_1['parsing_set']

email_server1 = {
        "imapServer": 'imap.gmail.com',
        "imapPort": '993',
        "imapUsername": 'ri_test@trustmile.com',
        "imapPassword": 'R!_Test#2'

  }






smtp_server = {
    "imapServer": 'secure.emailsrvr.com',
    "imapPort": '993',
    "imapUsername": 'smtp-test-account@trustmile.email',
    "imapPassword": 'S!_Test#2'
}

def send_email( from_address, to_address,  subject, body):

    #msg = MIMEText(body, 'html')
    msg = MIMEMultipart('alternative')
    msg.attach(MIMEText(body, 'html'))
    msg['Subject'] = subject
    #the from address needs to be fixed for the moment :/
    #msg['From'] = email_server1["imapUsername"]
    msg['From'] = from_address
    msg["To"] = to_address

    s = smtplib.SMTP('secure.emailsrvr.com:587')
    s.ehlo()
    s.starttls()
    s.login(smtp_server['imapUsername'], smtp_server['imapPassword'])

    s.sendmail(msg['From'], [msg['To'], config.RI_IMAP_USERNAME], msg.as_string())

    # mClient = mandrill.Mandrill(apikey = 'K7JgrteE5ByKHxT1gv8Xsg' )
    #
    # message = {
    #     'from_email': from_address,
    #     'to': [{'email': to_address,
    #                     'name': 'test consumer',
    #                     'type': 'to'},
    #             {'email': config.RI_IMAP_USERNAME,
    #                                     'name': 'Trust Mile RI Test Account',
    #                                     'type': 'bcc'}
    #            ],
    #     'preserve_recipients': True,
    #     'subject': subject,
    #     'html': body
    # }
    # result = mClient.messages.send( message=message, async=False)
    # print result


def clean_retailers():


    cons = db.session.query(Consignment).join(Consignment.integration_consignment).\
        filter(RetailerIntegrationConsignment.email_address == 'consumer1@trustmile.com').all()

    for c in cons:
        db.session.delete(c)

    ric = db.session.query(RetailerIntegrationConsignment).filter(RetailerIntegrationConsignment.email_address == 'consumer1@trustmile.com').all()
    for ri in ric:
        db.session.delete(ri)

    rte = db.session.query(RetailerTrackingEmail).filter( RetailerTrackingEmail.to_email_address == 'consumer1@trustmile.com').all()
    for rt in rte:
        db.session.delete(rt)

    for promotion in db.session.query(Promotion).all():
        db.session.delete(promotion)

    retailers = Retailer.get_all()
    for r in retailers:
        db.session.delete( r)


    db.session.commit()

def clean_consumer_users():
    cu1 = ConsumerUser.get('customer1@trustmile.com')
    if cu1:
        db.session.delete(cu1)
    cu2 = ConsumerUser.get('customer2@trustmile.com')
    if cu2:
        db.session.delete(cu2)
    db.session.commit()

def create_retailers():
    r1 = Retailer( 'Retailer1', 'UID1', config1)
    r1.email_server_configuration = email_server1
    r1.secret = 'acb123'
    db.session.add( r1 )
    db.session.commit()


def delete_retailers():
    r1 = Retailer.get( name="Retailer1")

    db.session.delete( r1)
    db.session.commit()

def setup_retailer_global_config():
    rgs = db.session.query( RetailerGlobalSettings ).first()
    if not rgs:
        rgs = RetailerGlobalSettings()
        db.session.add(rgs)

    rgs.tracking_number_regex = [ {'regex': '(?i)IZ[0-9]{10}', 'courier_name': 'Couriers Please'} ]
    rgs.shopify_courier_mapping = [ {'tracking_company': 'couriersplease', 'courier_name': 'Couriers PLease'}]
    db.session.commit()
class RetailerIntegrationTest(AppTest):

    @classmethod
    def setUpClass(cls):
        print "setupClass"
        couriers_file_path = os.path.dirname(os.path.realpath(__file__))
        execfile( couriers_file_path + '/../scripts/refresh_db_with_base_data.py')
        clean_retailers()
        clean_consumer_users()
        setup_retailer_global_config()

    def setUp(self):
        print "setUp"

    def tearDown(self):
        clean_retailers()
        clean_consumer_users()
        db.session.close()

    @classmethod
    def tearDownClass(cls):
        print "tearDown Class"
        db.session.close()


    def test001_EmailWorker_do_extractor(self):
        ew = EmailWorker()

        #test for courier
        start_pos, end_pos, r1 = ew.do_extractor( test1_config_1['parsing_set'][1]['extractors'][0], test1_parsed, 0, len(test1_parsed))
        self.assertIn( 'courier', r1)
        self.assertEqual( r1['courier'], ['Australia Post'])
        #test for using 'null' item.
        start_pos, end_pos, r2 = ew.do_extractor( test1_config_1['parsing_set'][1]['extractors'][1], test1_parsed, end_pos, len(test1_parsed))
        self.assertEqual( end_pos, 90)
        #test for finding the tracking number
        start_pos, end_pos, r3 = ew.do_extractor( test1_config_1['parsing_set'][1]['extractors'][2], test1_parsed, end_pos, len(test1_parsed))
        self.assertIn( 'tracking number', r3)
        self.assertIn( 'ABC123', r3['tracking number'])
        self.assertIn( 'TO1208694876', r3['tracking number'])
        self.assertIn( 'ABC456', r3['tracking number'])


        print(r1)
        print(r2)
        print(r3)

    def test002_EmailWorker_do_extractor_parsing(self):
        ew = EmailWorker()

        r1 = ew.do_extractor_parsing( test1_subject, test1_html, test1_config_1['parsing_set'])
        self.assertEqual(len(r1), 2 ) #expecting an array of order_id & courier/tracking
        self.assertIn( 'courier', r1[1])
        self.assertEqual( r1[1]['courier'], ['Australia Post'])
        self.assertIn( 'tracking number', r1[1])
        self.assertIn( 'ABC123', r1[1]['tracking number'])
        self.assertIn( 'TO1208694876', r1[1]['tracking number'])
        self.assertIn( 'ABC456', r1[1]['tracking number'])
        self.assertEqual( len(r1[1]['tracking number']), 3 )




    def test003_EndToEnd(self):

        ew = EmailWorker()
        create_retailers()


        r1 = RetailerIntegration().get_retailer( website_name="Retailer1")


        subject_date_append = ' - SendDate:' + str(datetime.now())
        #Lets start some tests
        send_email( r1.email_integration_configuration['from_email_addresses'][0],
                    'consumer1@trustmile.com',
                    'your order #N1234' + subject_date_append,
                    test1_html
                    )

        time.sleep(1)


        cu1 = ConsumerUser.create('customer1@trustmile.com', 'boundary', name='Customer One')

         # 4) call process_email
        emails_processed = ew.process_email(r1)
        self.assertEqual( emails_processed, 1)

        cons = Consignment.get_consignments( 'australia-post','ABC123')
        self.assertEqual( len(cons), 1)
        cons = Consignment.get_consignments( 'australia-post','TO1208694876')
        self.assertEqual( len(cons), 1)
        cons = Consignment.get_consignments( 'australia-post','ABC456')
        self.assertEqual( len(cons), 1)


    def test004_simple_courier_matching(self):
        email_text = ' bob IZ1234567890 '
        parsing_set = {
            'extractors': [{
                'start': 'bob ',
                'end': ' ',
                'item': 'tracking number',
                'repeat': False
            }],
            'tracking_number_parsing': True,
            'repeat': False
        }


        ew = EmailWorker()


        result = ew.do_extractor_set( parsing_set, email_text)
        self.assertEqual(1, len(result))
        self.assertIn( 'courier', result[0])
        self.assertEqual(result[0]['courier'][0], 'Couriers Please')
        self.assertIn('tracking number', result[0])
        self.assertEqual( 1, len( result[0]['tracking number']))
        self.assertEqual('IZ1234567890',result[0]['tracking number'][0])
        print result