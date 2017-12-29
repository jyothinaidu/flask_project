import imaplib
import email
from config import *
import datetime
import quopri
import logging

logger = logging.getLogger()

class EmailGateway():

    retailer = None # type: Retailer

    def open_connection(self, retailer):
        #setup an imap connection here
        self.server = imaplib.IMAP4_SSL( retailer.email_server_configuration['imapServer'],
                                         int(retailer.email_server_configuration['imapPort']))
        self.server.login( retailer.email_server_configuration['imapUsername'],
                           retailer.email_server_configuration['imapPassword'])

        # self.server = imaplib.IMAP4_SSL('imap.gmail.com', 993)
        #
        # self.server.login('smtp-test-account@trustmile.com','S!_Test#2')

        #if we impelement organising retailer into folders, enter that folder here.
        self.server.select( "inbox")


    def add_retailer(self, retailer):
        #used to do things like create folders & filters on the imap
        #server to organise the retailers emails
        #not surrently implement
        pass

    def update_retailer_email_addresses(self, retailer):
        #called when the email addreses for a retailer change
        #not implemented
        pass

    def get_new_emails(self, retailer):
        #gets any new emails from the retailer

        #this is used by other methods that need to do error logging
        self.retailer = retailer

        self.open_connection( retailer)

        if '*' in retailer.email_integration_configuration['from_email_addresses']:
            from_email_addresses = '*'
        else:
            from_email_addresses = retailer.email_integration_configuration['from_email_addresses']
        collected_emails = []





        for email_address in from_email_addresses:

            if email_address == '*':
                result, data = self.server.uid( 'search', None, '(UNSEEN)')
            else:
                result, data = self.server.uid( 'search', None, '(HEADER FROM "'+ email_address+'") (UNSEEN)')

            for email_uid in data[0].split():

                ret_email = self.fetch_email(email_uid)

                if ret_email:
                    collected_emails.append( ret_email)

        return collected_emails

    def fetch_email(self, email_uid, mark_as_unread=True):
        ret_email = {}

        result, email_data =  self.server.uid( 'fetch', email_uid, '(RFC822)')
        #some imap servers (GMAIL) set the seen flag when you tell it
        # others (RackSpace) set the flag when you fetch it
        # we want the flag set after the email is processed.
        # so reset it
        # the upper case 'STORE' is the key to making this work
        if mark_as_unread:
            self.server.uid( 'STORE',email_uid, '-FLAGS', '(\\SEEN)')

        parsed_email = email.message_from_string( email_data[0][1])
        if len(parsed_email) == 0:
            #log this
            logger.warn(u"len(parsed_email) == 0 Retailer: {0} {1}".format( self.retailer.id, self.retailer.website_name))
            return None

        ret_email["uid"] = email_uid
        ret_email["to_address"] = email.utils.parseaddr( parsed_email["TO"])[1]
        ret_email["from_address"] = email.utils.parseaddr( parsed_email["FROM"])[1]
        ret_email["subject"] = parsed_email["SUBJECT"]
        #this datetime has been converted into local time.
        ret_email["date"] = datetime.datetime.fromtimestamp( email.utils.mktime_tz( email.utils.parsedate_tz(parsed_email['Date'])))

        #the body of the email is a little tricky, as there can be html & text versions of it
        text_body = None
        html_body = None

        payload = parsed_email.get_payload()
        if isinstance(payload, str):
            text_body = payload
        else:
            for body_part in parsed_email.get_payload():
                if body_part.get_content_type() == 'text/plain':
                    text_body = body_part.get_payload()
                    if body_part['Content-Transfer-Encoding'] and body_part['Content-Transfer-Encoding'] == 'quoted-printable':
                        text_body = quopri.decodestring( text_body)
                elif body_part.get_content_type() == 'text/html':
                    html_body = body_part.get_payload()
                    if body_part['Content-Transfer-Encoding'] and body_part['Content-Transfer-Encoding'] == 'quoted-printable':
                        html_body = quopri.decodestring( html_body)

        if html_body:
            ret_email["body"] =  html_body
        elif text_body:
            ret_email["body"] =  text_body
        else:
            ret_email["body"] = ''

        return ret_email

    def mark_as_read(self, uid):
        self.server.uid( 'STORE',uid, '+FLAGS', '(\\SEEN)')








