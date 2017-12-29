import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.model.meta.base import commit_on_success
from model import *
from app.deliveries.model import *
from app import db

smtp_server = {
    "imapServer": 'imap.gmail.com',
    "imapPort": '993',
    "imapUsername": 'smtp-test-account@trustmile.com',
    "imapPassword": 'S!_Test#2'
}

class RetailerIntegration:

    def get_retailers(self):
        return Retailer.get_all()

    def get_retailer(self, id=None, umbraco_id=None, website_name=None):
        return Retailer.get(id, umbraco_id, website_name)

    @commit_on_success
    def add_parsed_email(self, retailer, email_dict, parsed_data):
        # email_dict["from_address"]
        # email_dict["to_address"],
        # email_dict["subject"]
        # email_dict["date"]
        # email_dict["body"]
        # email_dict["uid"]

        email = RetailerTrackingEmail.create( retailer, **email_dict)
        logger.debug(u"In add_parsed_email. retailer- {0} email_dict - {1} parsed_data - {2}".format(retailer, email_dict, parsed_data))

        if parsed_data['tracking_numbers']:
            for tracking in parsed_data['tracking_numbers']:
                try:
                    courier = Courier.retrieve_courier(tracking['courier'].replace("%20", " "))
                    retailer_consignment = RetailerIntegrationConsignment( retailer, email, parsed_data["email_address"], parsed_data.get( "order_id", None), tracking['tracking_number'], courier)
                    self.associate_retailer_consignment(retailer_consignment)
                    #self.associate_retailer_consignment( retailer_consignment, parsed_data["description"], parsed_data["retailer_name"])
                    #pushmessage = "Tracking a new Delivery from " +  parsed_data["retailer_name"]
                    #retailer_consignment = RetailerIntegrationConsignment( retailer, email, email_dict["to_address"], parsed_data.get( "order_id", None), tracking['tracking_number'], courier)
                    #self.associate_retailer_consignment( retailer_consignment, parsed_data["description"], retailer.website_name)
                    pushmessage = "Tracking a new Delivery from " +  retailer.website_name
                    PushNotification.send_push(email_dict["to_address"], message=pushmessage)
                except Exception, e:
                    logger.error( "Error saving tracking {0} {1} {2} {3}".format( retailer.website_name, parsed_data["email_address"], email.subject, e.message))
            #PushNotification.send_push(email_dict["to_address"], message=pushmessage) #commented to remove undefined pushmessage if no trackings available.
        else:
            #if no tracking exists or incorrect format for tracking numbers, notify garron about the same
            pushmessage = "Failed to Process a tracking for " +  retailer.website_name
            from_email = "surendra.yallabandi@valuelabs.com"
            to_email = "garron@trustmile.com"
            subject_email = email.subject
            self.send_email(from_email, to_email, subject_email, pushmessage)

        #for tracking in parsed_data['tracking_numbers']:
        #    try:
        #        courier = Courier.retrieve_courier(tracking['courier'].replace("%20"," "))
        #        retailer_consignment = RetailerIntegrationConsignment( retailer, email, parsed_data["email_address"], parsed_data.get( "order_id", None), tracking['tracking_number'], courier)
        #        logger.debug(u"In add_parsed_email. retailer_consignment obj - {0} ".format(retailer_consignment))

        #        self.associate_retailer_consignment(retailer_consignment)
                #self.associate_retailer_consignment( retailer_consignment, parsed_data["description"], parsed_data["retailer_name"])
                #pushmessage = "Tracking a new Delivery from " +  parsed_data["retailer_name"]
                #retailer_consignment = RetailerIntegrationConsignment( retailer, email, email_dict["to_address"], parsed_data.get( "order_id", None), tracking['tracking_number'], courier)
                #self.associate_retailer_consignment( retailer_consignment, parsed_data["description"], retailer.website_name)
        #        pushmessage = "Tracking a new Delivery from " +  retailer.website_name
        #    except Exception, e:
        #        logger.error( "Error saving tracking {0} {1} {2} {3}".format( retailer.website_name, parsed_data["email_address"], email.subject, e.message))
        #PushNotification.send_push(email_dict["to_address"], message=pushmessage)

    @commit_on_success
    def add_shopify_tracking(self, retailer, retailer_shopify_tracking, email_address, order_id, tracking_number, courier):
        retailer_consignment = RetailerIntegrationConsignment( retailer, None, email_address, order_id, tracking_number, courier)
        retailer_consignment.retailer_shopify_tracking = retailer_shopify_tracking
        db.session.add( retailer_consignment)
        self.associate_retailer_consignment( retailer_consignment)


    def associate_retailer_consignment(self, retailer_consignment):
    #def associate_retailer_consignment(self, retailer_consignment, description = None, retailer_name = None):
        #this method takes in a RetailerIntegrationConsignment
        #this method
        # creates a consignment if it doesn't exists, else update the consignment with a pointer to this retailer_consignment
        # if the consumer user exists
        #   adds the consignment to the consumer_user if it does not already have the consignment
        logger.debug(
            u"Updating shipping info on courier {0} for tracking {1}".format(retailer_consignment.courier, retailer_consignment.tracking_number))
        consignment = Consignment.create_or_get_consignment( retailer_consignment.courier, retailer_consignment.tracking_number)
        consignment.integration_consignment = retailer_consignment
        consignment.set_retailer(retailer_consignment.retailer, 'Integration')

        logger.debug(
            u"Updating shipping info on consignment {0} for tracking {1}".format(consignment.id, consignment.tracking_number))
        #Commenting this line to update the shipping info asynchoronously.
        #r_result = tasks.update_shipping_info_for_consignment.apply_async(args=(consignment.id,), countdown=3)
        r_result = tasks.update_shipping_info_for_consignment(consignment.id)

        #Found the consignment id is being obtained only after the above code is executed.? Why?
        if r_result is False:
            r_result = tasks.update_shipping_info_for_consignment(consignment.id)

        consumer_user = ConsumerUser.get(retailer_consignment.email_address)
        if consumer_user:

            #it would be nice if we could call User.add_consignment, but that would wipe  out the users description if they had one
            user =consumer_user.user
            exists = False
            for uc in user.user_consignments:
                if uc.consignment == consignment:
                    exists = True
                    break
            if not exists:
                #construct the description and retailer name
                #retailer = retailer_consignment.retailer
                retailer = retailer_consignment.retailer

                if not retailer_consignment.order_id:
                    #consignment_description = format( description )
                    #consignment_retailername = format( retailer_name)
                    consignment_description = u"Order from {0}".format(retailer.website_name)
                else:
                    #consignment_description = format( retailer_consignment.order_id,  description )
                    #consignment_retailername = format( retailer_consignment.order_id,  retailer_name)
                    consignment_description = u"Order {0} from {1}".format(retailer_consignment.order_id, retailer.website_name)

                #user.user_consignments.append( UserConsignment( consignment, consignment_description, consignment_retailername))
                user.user_consignments.append(UserConsignment(consignment, consignment_description))

    @commit_on_success
    def associate_consignments_for_user(self, email_address):
        retailer_consignments = RetailerIntegrationConsignment.get_by_email_address( email_address)
        for retailer_consignment in retailer_consignments:
            self.associate_retailer_consignment( retailer_consignment)



    def send_email(self,from_address, to_address, subject, body):

        # msg = MIMEText(body, 'html')
        msg = MIMEMultipart('alternative')
        msg.attach(MIMEText(body, 'html'))
        msg['Subject'] = subject
        # the from address needs to be fixed for the moment :/
        # msg['From'] = email_server1["imapUsername"]
        msg['From'] = from_address
        msg["To"] = to_address

        s = smtplib.SMTP('smtp.gmail.com:587')
        s.ehlo()
        s.starttls()
        s.login(smtp_server['imapUsername'], smtp_server['imapPassword'])

        s.sendmail(msg['From'], [msg['To'], config.RI_IMAP_USERNAME], msg.as_string())