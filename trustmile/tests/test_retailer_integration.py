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
from app.model.meta.base import close_db
import config

from app.ops.consumer_operations import AccountRegister

import mandrill
import time


#test
# 1.  test the dal layer.  creating retailers, email logs retailerintegration consignments and the methods on those objects
# 2. test the RetailerIntegration component.  This kinda wraps the DAL and also does the core processing.
# 3.  Test the EmailGateway component.   Make sure we can fetch emails
# 4. test the EmailWorker.  This will basically be the end-to-end test.  Need to test the vairow retailer parsing configuratios.

config1 = {
  "from_email_addresses": [ "retailer1@trustmile.com" ],

  "simpleParsingRules": [
    {
      "parsingRule": {
        "in": "body",
        "type": "regex",
        "rule": "L[0-9]{12}"
      },
      "courier": "toll-priority",
      "ruleOrder": 1,
      "pass": False
    }
  ],
  "parsers": [
    {
      "name": "Friendly name of parser",
      "acceptanceRule": {
        "in": "body",
        "type": "regex",
        "rule": "." #this will match on all
      },
      "parserType": "simple",
      "orderIDParser": {
          "in": "body",
          "type": "regex",
          "rule": "C[0-9]{12}"
        },
        "trackingParsingRules": [
          {
            "parsingRule": {
              "in": "body",
              "type": "regex",
              "rule": "LL[0-9]{11}"
            },
            "courier": None,
            "ruleOrder": 1,
            "pass": True
          }
        ]
    }
  ]

}
email_server1 = {
        "imapServer": 'imap.gmail.com',
        "imapPort": '993',
        "imapUsername": 'ri_test@trustmile.com',
        "imapPassword": 'R!_Test#2'

  }

config2=    {
  "from_email_addresses": [ "retailer2@trustmile.com,retailer2_1@trustmile.com" ],
  "simpleParsingRules": [
    {
      "parsingRule": {
        "in": "body",
        "type": "regex",
        "rule": "L[0-9]{12}"
      },
      "courier": "australia-post",
      "ruleOrder": 1,
      "pass": False
    }
  ],
  "parsers": [
    {
      "name": "Friendly name of parser",
      "acceptanceRule": {
        "in": "subject",
        "type": "regex",
        "rule": "Tracking Update"
      },
      "parserType": "simple",
      "orderIDParser": {
          "in": "body",
          "type": "regex",
          "rule": "C[0-9]{12}"
        },
        "trackingParsingRules": [
          {
            "parsingRule": {
              "in": "body",
              "type": "regex",
              "rule": "LL[0-9]{11}"
            },
            "courier": None,
            "ruleOrder": 1,
            "pass": True
          }
        ]
    }
  ]

}

#retailer1 email1
r1_e1 = {
    "from_address": 'retailer1@trustmile.com',
    "to_address": 'customer1@trustmile.com',
    "subject": 'Tracking from Retailer1 C',
    "body": 'Your tracking number is L123456789012 B',
    'date': datetime.now(),
    "uid": "r1_e1"
}

#retailer1 email1 parsed_data
r1_e1_pd = {
    'tracking_numbers':[
        { 'tracking_number': 'L123456789012',
          'courier': 'australia-post'}
    ],
    'email_address': 'customer1@trustmile.com'
}

#retailer1 email1
r1_e2= {
    "from_address": 'retailer1@trustmile.com',
    "to_address": 'customer2@trustmile.com',
    "subject": 'Tracking from Retailer1 D',
    "body": 'Your tracking number is L123456789013 L123456789014 order_id is C123456789012 B',
    'date': datetime.now(),
    "uid": "r1_e2"
}

#retailer1 email1 parsed_data1
r1_e2_pd = {
    'tracking_numbers':[
        { 'tracking_number': 'L123456789013',
          'courier': 'australia-post'},
        { 'tracking_number': 'L123456789014',
          'courier': 'australia-post'},

    ],
    'order_id': 'C123456789012',
    'email_address': 'customer2@trustmile.com'
}




def clean_retailers():

    tracking_numbers = []
    tracking_numbers.extend(r1_e1_pd['tracking_numbers'])
    tracking_numbers.extend(r1_e2_pd['tracking_numbers'])
    tracking_numbers.extend( [{'courier': 'toll-priority', 'tracking_number': 'L123456789012'}, {'courier': 'toll-priority', 'tracking_number': 'L123456789013'},{'courier': 'toll-priority', 'tracking_number': 'L123456789014'}])

    for tn in tracking_numbers:
        cons = Consignment.get_consignments( tn['courier'], tn['tracking_number'])
        if cons:
            db.session.delete( cons[0])

    UserConsignment.query.delete()
    Article.query.delete()
    Consignment.query.delete()
    RetailerIntegrationConsignment.query.delete()
    RetailerTrackingEmail.query.delete()

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
    r1.secret = 'abc123'
    r2 = Retailer( 'Retailer2', 'UID2', config2)
    r2.email_server_configuration = email_server1
    r2.secret = 'abc123'
    db.session.add( r1 )
    db.session.add( r2 )
    db.session.commit()


def delete_retailers():
    r1 = Retailer.get( website_name="Retailer1")
    r2 = Retailer.get( website_name="Retailer2")

    db.session.delete(r1)
    db.session.delete(r2)
    db.session.commit()



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

    s.sendmail(msg['From'], [msg['To'],config.RI_IMAP_USERNAME] , msg.as_string())

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

class RetailerIntegrationTest(AppTest):

    @classmethod
    def setUpClass(cls):
        print "setupClass"
        couriers_file_path = os.path.dirname(os.path.realpath(__file__))
        execfile( couriers_file_path + '/../scripts/refresh_db_with_base_data.py')
        clean_retailers()
        clean_consumer_users()

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


    def test001_retailer_dal(self):
        create_retailers()
        r1 = Retailer.get( website_name="Retailer1")
        self.assertIsNotNone(r1)
        r2 = Retailer.get( umbraco_id="UID2")
        self.assertIsNotNone(r2)


        #tracking emails
        r1_te = RetailerTrackingEmail()
        r1_te.retailer = r1
        r1_te.email_sent_date = datetime.now()
        r1_te.to_email_address = 'customer1@trustmile.com'
        r1_te.from_email_address = 'retailer1@trustmile.com'
        r1_te.subject = 'Tracking from Retailer1'
        r1_te.body = 'Your tracking number is L123456789012'

        db.session.add( r1_te)

        #Retailer Tracking
        r1_con = RetailerIntegrationConsignment()
        r1_con.retailer = r1
        r1_con.retailer_tracking_email = r1_te
        r1_con.email_address = 'customer1@trustmile.com'
        r1_con.tracking_number = 'L123456789012'
        r1_con.courier = Courier.retrieve_courier( 'toll-priority')

        db.session.add(r1_con)

        db.session.commit()

        #get retailer tracking
        r1_con_test = RetailerIntegrationConsignment.get_by_email_address( 'customer1@trustmile.com')
        self.assertIsNotNone(r1_con_test)

        delete_retailers()
        r1 = Retailer.get( website_name="Retailer1")
        self.assertIsNone(r1)
        r2 = Retailer.get( umbraco_id="UID2")
        self.assertIsNone(r2)


    def test002_ri_API_get_retailers(self):
        create_retailers()
        retailers = RetailerIntegration().get_retailers()
        self.assertEqual( len(retailers), 2)

    def test003_ri_API_get_retailer(self):
        create_retailers()

        r1 = RetailerIntegration().get( website_name="Retailer1")
        self.assertIsNotNone(r1)
        r2 = RetailerIntegration().get( umbraco_id="UID2")
        self.assertIsNotNone(r2)


    def test003_ri_API_get_retailer(self):
        create_retailers()

        r1 = RetailerIntegration().get_retailer( website_name="Retailer1")
        self.assertIsNotNone(r1)
        r2 = RetailerIntegration().get_retailer( umbraco_id="UID2")
        self.assertIsNotNone(r2)

    def test004_ri_API_add_parsed_data(self):
        create_retailers()

        r1 = RetailerIntegration().get_retailer( website_name='Retailer1')

        #create a consumer user, this will receive email r1

        cu1 = ConsumerUser.create('customer1@trustmile.com', 'boundary', name='Customer One')

        RetailerIntegration().add_parsed_email(r1, r1_e1, r1_e1_pd)

        #did the email get written
        db_r1_e1 = db.session.query(RetailerTrackingEmail).filter( RetailerTrackingEmail.to_email_address==r1_e1['to_address']).first()
        self.assertIsNotNone(db_r1_e1)

        #did the Retailer tracking number get written
        db_r1_e1_r_cons = db.session.query(RetailerIntegrationConsignment).filter( RetailerIntegrationConsignment.retailer_tracking_email == db_r1_e1).all()
        self.assertEqual( len(db_r1_e1_r_cons), 1)
        self.assertEqual( db_r1_e1_r_cons[0].tracking_number, r1_e1_pd['tracking_numbers'][0]['tracking_number'])

        #as the consumer user existed, the consignment should exists
        db_r1_e1_con = Consignment.get_consignments( r1_e1_pd['tracking_numbers'][0]['courier'],r1_e1_pd['tracking_numbers'][0]['tracking_number'])
        self.assertEqual( len(db_r1_e1_con), 1)

        #the consignment should be associated with the consumer user
        hasConsignment = False
        for consignment in cu1.user.get_consignments():
            if consignment == db_r1_e1_con[0]:
                hasConsignment = True
                break
        self.assertTrue( hasConsignment)


        RetailerIntegration().add_parsed_email(r1, r1_e2, r1_e2_pd)



        #did the email get written
        db_r1_e2 = db.session.query(RetailerTrackingEmail).filter( RetailerTrackingEmail.to_email_address==r1_e2['to_address']).first()
        self.assertIsNotNone(db_r1_e2)

        #did the Retailer tracking number get written - both of them?
        db_r1_e2_r_cons = db.session.query(RetailerIntegrationConsignment).filter( RetailerIntegrationConsignment.retailer_tracking_email == db_r1_e2).all()
        self.assertEqual( len(db_r1_e2_r_cons), 2)
        self.assertIn( db_r1_e2_r_cons[0].tracking_number, [ r1_e2_pd['tracking_numbers'][0]['tracking_number'],r1_e2_pd['tracking_numbers'][1]['tracking_number']])
        self.assertIn( db_r1_e2_r_cons[1].tracking_number, [ r1_e2_pd['tracking_numbers'][0]['tracking_number'],r1_e2_pd['tracking_numbers'][1]['tracking_number']])
        self.assertEquals( db_r1_e2_r_cons[1].order_id, r1_e2_pd['order_id'])
        self.assertIsNotNone( db_r1_e2_r_cons[1].order_id)
        self.assertNotEqual( db_r1_e2_r_cons[0].tracking_number,db_r1_e2_r_cons[1].tracking_number)


        #although the courier user does not exist, the consignment should exist
        db_r1_e2_con1 = Consignment.get_consignments( r1_e2_pd['tracking_numbers'][0]['courier'],r1_e2_pd['tracking_numbers'][0]['tracking_number'])
        self.assertEqual( len(db_r1_e2_con1), 1)
        db_r1_e2_con2 = Consignment.get_consignments( r1_e2_pd['tracking_numbers'][1]['courier'],r1_e2_pd['tracking_numbers'][1]['tracking_number'])
        self.assertEqual( len(db_r1_e2_con2), 1)


        #now, create the second user and add it in.
        # do the consignments get created?

        cu2 = ConsumerUser.create('customer2@trustmile.com', 'boundary', name='Customer Two')
        RetailerIntegration().associate_consignments_for_user( 'customer2@trustmile.com')

        #did the consignments get created?
        db_r1_e2_con1 = Consignment.get_consignments( r1_e2_pd['tracking_numbers'][0]['courier'],r1_e2_pd['tracking_numbers'][0]['tracking_number'])
        self.assertEqual( len(db_r1_e2_con1), 1)
        db_r1_e2_con2 = Consignment.get_consignments( r1_e2_pd['tracking_numbers'][1]['courier'],r1_e2_pd['tracking_numbers'][1]['tracking_number'])
        self.assertEqual( len(db_r1_e2_con2), 1)

        #the consignment should be associated with the consumer user
        hasConsignment = False
        for consignment in cu2.user.get_consignments():
            if consignment == db_r1_e2_con1[0]:
                hasConsignment = True
                break
        self.assertTrue( hasConsignment)
        hasConsignment = False
        for consignment in cu2.user.get_consignments():
            if consignment == db_r1_e2_con2[0]:
                hasConsignment = True
                break
        self.assertTrue( hasConsignment)


        db.session.commit()

    def test005_EmailGateway(self):

        eg = EmailGateway()

        create_retailers()
        r1 = RetailerIntegration().get_retailer( website_name='Retailer1')

        #empty & discard
        emails = eg.get_new_emails( r1 )
        for email in emails:
            eg.mark_as_read( email['uid'])

        #ensure that worked - tests both the flagging as read
        # and the filter to only get unread emails
        emails = eg.get_new_emails( r1 )
        self.assertEqual( len(emails), 0)


        subject_date_append = ' - SendDate:' + str(datetime.now())
        #Lets start some tests
        send_email( r1.email_integration_configuration['from_email_addresses'][0],
                    r1_e1['to_address'],
                    r1_e1['subject'] + subject_date_append,
                    r1_e1['body']
                    )

        send_email( r1.email_integration_configuration['from_email_addresses'][0],
                    r1_e2['to_address'],
                    r1_e2['subject'] + subject_date_append,
                    r1_e2['body']
                    )
        time.sleep(1)

        emails = eg.get_new_emails( r1 )
        self.assertEqual( len(emails), 2, "Sometimes gmail queues emails to throtle them.  It's annoying.. ALSO - make sure celery is stopped")

        #compare the emails to make sure what we sent is what we received
        # this will depend on the emails having different subjects.  A bit ugly but it's ok
        r1_e1_received = False
        r1_e2_received = False
        for email in emails:
            if email['to_address'] == r1_e1['to_address'] and email['subject'] == r1_e1['subject'] + subject_date_append:
                r1_e1_received = True
                self.assertEqual( email['from_address'], r1.email_integration_configuration['from_email_addresses'][0])
                #we use string.find as Mandril adds in a tracking pixel
                self.assertTrue( email['body'].find( r1_e1['body'] ) != -1 )
            elif email['to_address'] == r1_e2['to_address'] and email['subject'] == r1_e2['subject'] + subject_date_append:
                r1_e2_received = True
                self.assertEqual( email['from_address'], r1.email_integration_configuration['from_email_addresses'][0])
                #we use string.find as Mandril adds in a tracking pixel
                self.assertTrue( email['body'].find( r1_e2['body'] ) != -1 )

        self.assertTrue( r1_e1_received)
        self.assertTrue(r1_e2_received)


        #ensure we don't get emails for the wrong retailer.  AKA the filter by email address is working
        #we havn't maked the emails as unread yet, so a get for r1 would still get all the emails
        r2 = RetailerIntegration().get_retailer( website_name='Retailer2')
        emails2 = eg.get_new_emails( r2 )
        self.assertEqual( len(emails2), 0)


    def test006_EmailWorker_do_parse(self):

        ew = EmailWorker()


        p1 ={
            "in": "body",
            "type": "regex",
            "rule": "L[0-9]{12}"
          }

        p2 ={
            "in": "subject",
            "type": "regex",
            "rule": "C[0-9]{12}"
        }

        #failing case
        p3 ={
            "in": "other",
            "type": "regex",
            "rule": "C[0-9]{12}"
        }

        #failing case
        p4 ={
            "in": "subject",
            "type": "string",
            "rule": "C[0-9]{12}"
        }

        #2 trackings from p1
        # no results from p2
        e1= {
            "from_address": 'retailer1@trustmile.com',
            "to_address": 'customer2@trustmile.com',
            "subject": 'Tracking from Retailer1 D',
            "body": 'Your tracking number is L123456789013 L123456789014 order_id is C123456789012 B',
            'date': datetime.now(),
            "uid": "r1_e2"
        }

        #none from p1
        #order_id from p2
        e2= {
            "from_address": 'retailer1@trustmile.com',
            "to_address": 'customer2@trustmile.com',
            "subject": 'Tracking from Retailer1 C123456789012',
            "body": 'Your tracking number is L12345789013 L12345689014 order_id is  B',
            'date': datetime.now(),
            "uid": "r1_e2"
        }

        parse_result = ew.do_parse( e1, p1)
        self.assertEqual( len(parse_result), 2)
        self.assertIn( 'L123456789013', parse_result)
        self.assertIn( 'L123456789014', parse_result)

        parse_result = ew.do_parse( e1, p2)
        self.assertEqual( len(parse_result), 0)

        parse_result = ew.do_parse( e2, p1)
        self.assertEqual( len(parse_result), 0)

        parse_result = ew.do_parse( e2, p2)
        self.assertEqual( len(parse_result), 1)
        self.assertIn( 'C123456789012', parse_result)

        with self.assertRaises(Exception) as context:
            ew.do_parse( e1, p3)
        self.assertTrue( "unsupported parser location: " + p3['in'] in context.exception)

        with self.assertRaises(Exception) as context:
            ew.do_parse( e1, p4)
        self.assertTrue( "unsupported parser type: " + p4['type'] in context.exception)


    def test006_EmailWorker_do_simple_tracking_parser(self):

        ew = EmailWorker()

        #note the duplicated tracking number
        e1= {
            "from_address": 'retailer1@trustmile.com',
            "to_address": 'customer2@trustmile.com',
            "subject": 'Tracking from Retailer1 D',
            "body": 'Your tracking number is LL123456789013 L123456789014  L123456789014 order_id is C123456789012 B',
            'date': datetime.now(),
            "uid": "r1_e2"
        }

        #global tracking rule
        #will match 2 in e1
        pr1=[
            {
              "parsingRule": {
                "in": "body",
                "type": "regex",
                "rule": "L[0-9]{12}"
              },
              "courier": "toll-priority",
              "ruleOrder": 1,
              "pass": False
            }
        ]

        #overridxe tracking rule.  match 1 in e1

        pr2=[
            {
              "parsingRule": {
                "in": "body",
                "type": "regex",
                "rule": "LL[0-9]{12}"
              },
              "courier": "toll-priority",
              "ruleOrder": 1,
              "pass": False
            }
        ]

        #global tracking rule
        #will match 2 in e1
        #example of 2 ordered rule
        pr3=[
            {
              "parsingRule": {
                "in": "body",
                "type": "regex",
                "rule": "L[0-9]{12}"
              },
              "courier": "toll-priority",
              "ruleOrder": 2,
              "pass": False
            },
{
              "parsingRule": {
                "in": "body",
                "type": "regex",
                "rule": "LL[0-9]{12}"
              },
              "courier": "australia-post",
              "ruleOrder": 1,
              "pass": False
            }
        ]

        # 'pass' example
        #matches 0 in e1
        #when combined with p1, causes p1 to match only1
        pr4=[
            {
              "parsingRule": {
                "in": "body",
                "type": "regex",
                "rule": "LL[0-9]{12}"
              },
              "courier": None,
              "ruleOrder": 1,
              "pass": True
            }
        ]

        #trackings from the first rule
        trackings = ew.do_simple_tracking_parser( e1, pr1,[])['tracking_numbers']
        self.assertEqual( len( trackings), 2)

        t1_true = False
        t2_true = False
        for tracking in trackings:
            if tracking['tracking_number'] == 'L123456789013' and tracking['courier'] == 'toll-priority':
                t1_true = True
            elif tracking['tracking_number'] == 'L123456789014' and tracking['courier'] == 'toll-priority':
                t2_true = True
        self.assertTrue( t1_true)
        self.assertTrue( t2_true)

        #second rule
        trackings = ew.do_simple_tracking_parser( e1, pr2,[])['tracking_numbers']
        self.assertEqual( len( trackings), 1)

        t1_true = False
        t2_true = False
        for tracking in trackings:
            if tracking['tracking_number'] == 'LL123456789013' and tracking['courier'] == 'toll-priority':
                t1_true = True
        self.assertTrue( t1_true)

        #third rule
        # the extra LL on the tracking number
        trackings = ew.do_simple_tracking_parser( e1, pr3,[])['tracking_numbers']
        self.assertEqual( len( trackings), 2)

        t1_true = False
        t2_true = False
        for tracking in trackings:
            if tracking['tracking_number'] == 'LL123456789013' and tracking['courier'] == 'australia-post':
                t1_true = True
            elif tracking['tracking_number'] == 'L123456789014' and tracking['courier'] == 'toll-priority':
                t2_true = True
        self.assertTrue( t1_true)
        self.assertTrue( t2_true)


        #4th rule  no match
        trackings = ew.do_simple_tracking_parser( e1, pr4,[])['tracking_numbers']
        self.assertEqual( len( trackings), 0)

        #check that we can move where pr1 is passed to do_simple_tracking_parser
        trackings = ew.do_simple_tracking_parser( e1, [], pr1)['tracking_numbers']
        self.assertEqual( len( trackings), 2)

        t1_true = False
        t2_true = False
        for tracking in trackings:
            if tracking['tracking_number'] == 'L123456789013' and tracking['courier'] == 'toll-priority':
                t1_true = True
            elif tracking['tracking_number'] == 'L123456789014' and tracking['courier'] == 'toll-priority':
                t2_true = True
        self.assertTrue( t1_true)
        self.assertTrue( t2_true)


        ##now, for some more complicated things

        #p2 overriding p1 to pull out the double LL
        trackings = ew.do_simple_tracking_parser( e1, pr2, pr1)['tracking_numbers']
        self.assertEqual( len( trackings), 2)

        t1_true = False
        t2_true = False
        for tracking in trackings:
            if tracking['tracking_number'] == 'LL123456789013' and tracking['courier'] == 'toll-priority':
                t1_true = True
            elif tracking['tracking_number'] == 'L123456789014' and tracking['courier'] == 'toll-priority':
                t2_true = True
        self.assertTrue( t1_true)
        self.assertTrue( t2_true)

        #p4 overriding p1, to stop LL123456789013 being returned
        trackings = ew.do_simple_tracking_parser( e1, pr4, pr1)['tracking_numbers']
        self.assertEqual( len( trackings), 1)

        t1_true = False
        t2_true = False
        for tracking in trackings:
            if tracking['tracking_number'] == 'L123456789014' and tracking['courier'] == 'toll-priority':
                t1_true = True
        self.assertTrue( t1_true)


    def test007_EmailWorker_process_emails(self):
        #the big one.  this is the big end to end test.
        #will it work

        # 1) clean emails
        # 2) send 2 emails for r1, 2 different users
        # 3) create 1 consumer user
        # 4) call process_email
        # 5) verify the 2x emails are written, the 2x retailer consignments are written
        # 6) verify 1 consignment created, and assigned to customer1
        # 7) create consumer_user 2.  Call to add consignments to his account
        # 8) verify that worked

        create_retailers()
        ew = EmailWorker()
        r1 = RetailerIntegration().get_retailer(website_name='Retailer1')

        eg = EmailGateway()

        # 1) clean emails
        emails = eg.get_new_emails( r1 )
        for email in emails:
            eg.mark_as_read( email['uid'])

        # 2) send 2 emails for r1, 2 different users
        subject_date_append = ' - SendDate:' + str(datetime.now())
        #Lets start some tests
        send_email( r1.email_integration_configuration['from_email_addresses'][0],
                    r1_e1['to_address'],
                    r1_e1['subject'] + subject_date_append,
                    r1_e1['body']
                    )

        send_email( r1.email_integration_configuration['from_email_addresses'][0],
                    r1_e2['to_address'],
                    r1_e2['subject'] + subject_date_append,
                    r1_e2['body']
                    )
        time.sleep(1)

        # 3) create 1 consumer user
        cu1 = ConsumerUser.create('customer1@trustmile.com', 'boundary', name='Customer One')

         # 4) call process_email
        emails_processed = ew.process_email(r1)
        self.assertEqual( emails_processed, 2)

        # 5) verify the 2x emails are written, the 2x retailer consignments are written
        # r1_e1 = {
        #     "from_address": 'retailer1@trustmile.com',
        #     "to_address": 'customer1@trustmile.com',
        #     "subject": 'Tracking from Retailer1 C',
        #     "body": 'Your tracking number is L123456789012 B',
        #     'date': datetime.now(),
        #     "uid": "r1_e1"
        # }
        #
        # }
        #
        # #retailer1 email1
        # r1_e2= {
        #     "from_address": 'retailer1@trustmile.com',
        #     "to_address": 'customer2@trustmile.com',
        #     "subject": 'Tracking from Retailer1 D',
        #     "body": 'Your tracking number is L123456789013 L123456789014 order_id is C123456789012 B',
        #     'date': datetime.now(),
        #     "uid": "r1_e2"
        # }

        ##
        ## This is all one big copy of the test004_ri_API_add_parsed_data()
        ## With a few changes
        ## Nice to recfactor that, but it will have to be cut & paste atm

        #did the email get written
        db_r1_e1 = db.session.query(RetailerTrackingEmail).filter( RetailerTrackingEmail.to_email_address==r1_e1['to_address']).first()
        self.assertIsNotNone(db_r1_e1)

        #did the Retailer tracking number get written
        db_r1_e1_r_cons = db.session.query(RetailerIntegrationConsignment).filter( RetailerIntegrationConsignment.retailer_tracking_email == db_r1_e1).all()
        self.assertEqual( len(db_r1_e1_r_cons), 1)

        self.assertEqual( db_r1_e1_r_cons[0].tracking_number, 'L123456789012')

        #as the consumer user existed, the consignment should exists
        db_r1_e1_con = Consignment.get_consignments( 'toll-priority','L123456789012')
        self.assertEqual( len(db_r1_e1_con), 1)

        #the consignment should be associated with the consumer user
        hasConsignment = False
        for consignment in cu1.user.get_consignments():
            if consignment == db_r1_e1_con[0]:
                hasConsignment = True
                break
        self.assertTrue( hasConsignment)

        #is the subject line correct
        description_correct = False
        for uc in cu1.user.user_consignments:
            if uc.user_description == "Order from {0}".format( r1.website_name ):
                description_correct = True

        self.assertTrue( description_correct)





        #did the second email get written
        db_r1_e2 = db.session.query(RetailerTrackingEmail).filter( RetailerTrackingEmail.to_email_address==r1_e2['to_address']).first()
        self.assertIsNotNone(db_r1_e2)

        #did the Retailer tracking number get written - both of them?
        db_r1_e2_r_cons = db.session.query(RetailerIntegrationConsignment).filter( RetailerIntegrationConsignment.retailer_tracking_email == db_r1_e2).all()
        self.assertEqual( len(db_r1_e2_r_cons), 2)
        self.assertIn( db_r1_e2_r_cons[0].tracking_number, [ 'L123456789013','L123456789014'])
        self.assertIn( db_r1_e2_r_cons[1].tracking_number, [ 'L123456789013','L123456789014'])
        self.assertNotEqual( db_r1_e2_r_cons[0].tracking_number,db_r1_e2_r_cons[1].tracking_number)
        #is the order_id correct
        self.assertEquals( db_r1_e2_r_cons[1].order_id, 'C123456789012')


        #although the consumer user does not exist the consignment should exists
        db_r1_e2_con1 = Consignment.get_consignments( 'toll-priority','L123456789013')
        self.assertEqual( len(db_r1_e2_con1), 1)
        db_r1_e2_con2 = Consignment.get_consignments( 'toll-priority','L123456789014')
        self.assertEqual( len(db_r1_e2_con2), 1)


        #now, create the second user and add it in.
        # do the consignments get created?

        cu2 = ConsumerUser.create('customer2@trustmile.com', 'boundary', name='Customer Two')
        RetailerIntegration().associate_consignments_for_user( 'customer2@trustmile.com')

        #did the consignments get created?
        db_r1_e2_con1 = Consignment.get_consignments( 'toll-priority','L123456789013')
        self.assertEqual( len(db_r1_e2_con1), 1)
        db_r1_e2_con2 = Consignment.get_consignments( 'toll-priority','L123456789014')
        self.assertEqual( len(db_r1_e2_con2), 1)

        #the consignment should be associated with the consumer user
        hasConsignment = False
        for consignment in cu2.user.get_consignments():
            if consignment == db_r1_e2_con1[0]:
                hasConsignment = True
                break
        self.assertTrue( hasConsignment)

        hasConsignment = False
        for consignment in cu2.user.get_consignments():
            if consignment == db_r1_e2_con2[0]:
                hasConsignment = True
                break

        #is the subject line correct on 2 packages
        description_correct = 0
        for uc in cu2.user.user_consignments:
            if uc.user_description == "Order {0} from {1}".format( 'C123456789012',  r1.website_name ):
                description_correct += 1

        self.assertEquals( description_correct, 2)


    db.session.commit()
