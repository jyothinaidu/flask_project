__author__ = 'james'

from app import db
from app.deliveries.model import Courier, Consignment, Article
from app.users.model import ConsumerUser, UserAddress
from app.retailer_integration.model import Retailer, RetailerGlobalSettings
from app.model.meta.schema import utcnow
from app.model.meta.base import commit_on_success
import json
import os


db.drop_all()
db.create_all()

path = os.getcwd()




# create couriers
@commit_on_success
def create_base_couriers():
    import json
    path = os.path.dirname(os.path.realpath(__file__))
    d  = json.load(open(path + "/../tests/couriers-aftership.json"))
    couriers = d

    for c in couriers:

        courier = Courier(c['name'], c['slug'], c['phone'], c['web_url'], trustmile_courier=True)
        db.session.add(courier)


# Create test set of users.

# Users
#   Address
#   Consignments
#       Articles

@commit_on_success
def create_dummy_data():
    import json
    from app.model import ConsumerUser, UserAddress
    path = os.path.dirname(os.path.realpath(__file__))
    test_data = json.load(( open( path + "/../" + "tests/testing-data-for-db.json")))


    for user in test_data["users"]:
        cu = ConsumerUser.create(user["emailAddress"], user["password"] )
        cu.email_verified = True
        cu.email_verification_dt = utcnow()
        if user.get("passwordResetToken" ):
            cu.password_reset_token = user["passwordResetToken"]

        cu.user.user_address.append( UserAddress( addressLine1 = user["address"]["addressLine1"],
                                             addressLine2 = user["address"]["addressLine2"],
                                             state = user["address"]["state"],
                                             countryCode = user["address"]["countryCode"],
                                             suburb = user["address"]["suburb"],
                                             postcode = user["address"]["postcode"]
                                             ) )
        for consignment in user["consignments"]:
            courier_obj = Courier.retrieve_courier(consignment['slug'])
            cons = Consignment.create_or_get_consignment(courier_obj, consignment["consignmentNumber"])
            cu.user.add_consignment(cons)
            cons.tracking_info = consignment["tracking_info"]
            article = Article( cons.tracking_number, cons.courier, True)
            article.tracking_info = consignment["tracking_info"]
            cons.articles.append( article )


def create_dummy_retailer():
    test1_config_1 = {

        'parsing_set': [ #extractor_sets
                        {
                                'position_extractor': None,
                                'repeat': False,
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
      "from_email_addresses": [ "retailer1@trustmile.com" ],
      "mailServer": {
            "imapServer": 'imap.gmail.com',
            "imapPort": '993',
            "imapUsername": 'ri_test@trustmile.com',
            "imapPassword": 'R!_Test#2'
      }
    }
    config1['parsing_set'] = test1_config_1['parsing_set']

    r1 = Retailer( 'Retailer1', 'UID1', config1)
    r1.secret = 'abc123'
    db.session.add( r1 )
    db.session.commit()



def create_retailer_global_config():
    rg = RetailerGlobalSettings()
    rg.tracking_number_regex = [ {'regex': '(?i)IZ[0-9]{10}', 'courier_name': 'Couriers Please'} ]
    rg.shopify_courier_mapping = [ {'tracking_company': 'couriersplease', 'courier_name': 'Couriers PLease'}]
    db.session.add(rg)
    db.session.commit()

create_base_couriers()
create_dummy_data()
create_dummy_retailer()
create_retailer_global_config()

r = Retailer(website_name='indulgeHQ', umbraco_id='1234',config={})
r.secret = 'abc123'
db.session.add(r)
db.session.commit()


