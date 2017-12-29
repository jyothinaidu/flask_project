from app.retailer_integration.model import Retailer
from app.retailer_integration.EmailGateway import EmailGateway
from app.retailer_integration.EmailWorker import EmailWorker

class ParsingRulesDev():

    retailer = None #type: retailer

    email_id = None

    #email server detailes will come from here
    def set_retailer(self, retailer):
        retailer = retailer

    #set the email server details directly
    def set_imap(self, username, password, server, port):
        self.retailer = Retailer('test','test')
        self.retailer.email_server_configuration = {}
        self.retailer.email_server_configuration['imapServer'] = server
        self.retailer.email_server_configuration['imapPort'] = port
        self.retailer.email_server_configuration['imapUsername'] = username
        self.retailer.email_server_configuration['imapPassword'] = password


    def load_email(self,uid, mark_as_unread=False):
        if not self.retailer:
            raise Exception( 'set retailer first')

        eg = EmailGateway()
        eg.open_connection(self.retailer)

        email = eg.fetch_email(uid,mark_as_unread)
        return email

    def get_email_text(self, email_dict, extractor_set):
        ew = EmailWorker()

        email_text = ew.get_email_text( email_dict['subject'], email_dict['body'], extractor_set)

        return email_text

    def test_rules(self, email_dict, extractor_set):
        ew = EmailWorker()

        email_text = self.get_email_text(email_dict,extractor_set)
        result = ew.do_extractor_set(extractor_set, email_text)

        return result

    def format_results_for_db(self,parsing_results):
        ew = EmailWorker()

        retailer = Retailer('test','test')
        email = {}
        email['to_address'] = ''
        email['subject'] = ''

        result = {}
        result['tracking_numbers'] = []
        ew.format_results_for_db(result,parsing_results,retailer,email)

        return result



