from EmailGateway import EmailGateway
from RetailerIntegration import RetailerIntegration
import re
import copy
from bs4 import BeautifulSoup
from model import RetailerGlobalSettings, Retailer
from app.deliveries.model import Courier

import logging

logger = logging.getLogger()


class EmailWorker:

    def process_email(self, retailer):
        if not retailer.email_integration_configuration or not retailer.email_server_configuration:
            return

        email_gateway = EmailGateway()
        emails = email_gateway.get_new_emails(retailer)
        emails_picked = len(emails)
        logger.info('Retrieved {0} emails from gateway'.format(emails_picked))
        read_email_count = 0
        unread_email_count = 0
        for email in emails:

            #we need to store emails, even if we don't pull any tracking info from them
            parsed_data = {}
            parsed_data['email_address'] = email["to_address"]
            parsed_data['tracking_numbers'] = []

            #find a matching parser
            if 'parsers' in retailer.email_integration_configuration:
                for parser in retailer.email_integration_configuration['parsers']:
                    result = self.do_parse( email, parser['acceptanceRule'])
                    if result:
                        break
                    parser = None

                # we have found our parser
                if parser:
                    if parser['parserType'] == "simple":
                        results = self.do_simple_tracking_parser( email, parser['trackingParsingRules'], retailer.email_integration_configuration.get( 'simpleParsingRules', []))
                        parsed_data['tracking_numbers'].extend( results['tracking_numbers'])
                        if parser.get( 'orderIDParser', None) != None:
                            order_id = self.do_parse( email, parser['orderIDParser'] )
                            if len( order_id):
                                parsed_data["order_id"] = order_id[0]

                    else:
                        raise Exception(u"Unsupported Parser")

                else:
                    pass
                    #this email is unsupported


            #this is the newer method parser
            if retailer.email_integration_configuration.get('parsing_set', None):
                parsing_set = retailer.email_integration_configuration['parsing_set']

                parsing_results = self.do_extractor_parsing( email['subject'], email['body'], parsing_set)

                self.format_results_for_db( parsed_data, parsing_results, retailer, email)

            #parsed_data now contains a dict/struct of data from the emailew.pro
            #time to put it into the db.
            unread_email_count = unread_email_count + 1

            RetailerIntegration().add_parsed_email( retailer, email, parsed_data)

            email_gateway.mark_as_read(email['uid'])

            read_email_count = read_email_count +1
            unread_email_count = unread_email_count - 1

        if emails_picked > 0 and unread_email_count > 0 and read_email_count > 0 :
            #Send email to Garron about emails picked and read

            pushmessage = "Hello, <br/> Below emails are processed for tracking " + retailer.website_name + "<br/></br> "+str(read_email_count)+ "Emails processed <br /> "+str(unread_email_count)+" Unread Emails <br/>"
            from_email = "smtp-test-account@trustmile.com"
            to_email = "kirthi.kamana@valuelabs.com,surendra.yallabandi@valuelabs.com" #garron@trustmile.com
            subject_email = "Processed Emails For Tracking"
            RetailerIntegration.send_email(from_email, to_email, subject_email, pushmessage)



        return emails_picked #Count of emails from gateway

    #massages parsing results into the format expected by the DB

    #retailer is used to fdo courier mapping
    # email is used for logging
    def format_results_for_db(self, parsed_data, parsing_results, retailer, email):
        for result in parsing_results:
            resultFound =False
            if result.get( 'order_id'):
                parsed_data['order_id'] = result['order_id'][0]
                resultFound = True


            if result.get( 'courier', None) and len(result['courier']) ==1:
                resultFound = True
                courier = result['courier'][0]


                courier = self.map_courier( retailer, courier)


                if result.get( 'tracking number', None):
                    for tracking_number in result['tracking number']:
                        parsed_data['tracking_numbers'].append( { "tracking_number": tracking_number,
                                  "courier": courier})
                else:
                    logger.info(u"no tracking numbers found {0} {1} {2} {3}".format(retailer.id, retailer.website_name, email['to_address'], email['subject']))

            if not resultFound:
                logger.info(u"no order_ids or couriers found {0} {1} {2} {3}".format(retailer.id, retailer.website_name, email['to_address'], email['subject']))

        #dedupe parsed_data['tracking_numbers']
        deduped_tracking_numbers = []
        existing_tracking_numbers = {}
        for tn in parsed_data['tracking_numbers']:
            if existing_tracking_numbers.get( tn['courier']):
                if existing_tracking_numbers[tn['courier']].get( tn['tracking_number']):
                    continue #this is a duplicate
                else:
                    existing_tracking_numbers[tn['courier']][tn['tracking_number']] = True
            else:
                existing_tracking_numbers[tn['courier']] = {}
                existing_tracking_numbers[tn['courier']][tn['tracking_number']] = True

            deduped_tracking_numbers.append(tn)

        parsed_data['tracking_numbers'] = deduped_tracking_numbers

    def do_parse(self, email, parserRule):
        #this takes in some parser rules, applies it to an email, and returns the result.
        # the return value is an array of matches, or None
        if parserRule['in'] == "body":
            target_string = email["body"]
        elif parserRule['in'] == "subject":
            target_string = email["subject"]
        else:
            raise Exception(u"unsupported parser location: " + parserRule['in'] )

        if parserRule['type'] == "regex":
            result = self.parse_regex( target_string, parserRule['rule'])
        else:
            raise Exception(u"unsupported parser type: " + parserRule['type'])

        return result

    def parse_regex(self, text, regex):
        return re.findall( regex, text)



    def do_simple_tracking_parser(self, email, primaryTrackingParsing, secondaryTrackingParsing ):

        #make a copy of the email, so we don't mess it up when we are replacing the body, etc
        email = copy.deepcopy(email)
        results = []

        # the [:] makes a copy of the list
        ptSorted = primaryTrackingParsing[:]
        ptSorted.sort( key=lambda rule: rule['ruleOrder'])
        stSorted = secondaryTrackingParsing[:]
        stSorted.sort( key=lambda rule: rule['ruleOrder'])

        combinedTracking = ptSorted + stSorted
        for trackingRule in combinedTracking:
            matchingStrings = self.do_parse( email, trackingRule['parsingRule'])

            if matchingStrings:
                #remove duplicates
                matchingStrings = list( set( matchingStrings) )
                for trackingNumber in matchingStrings:
                    if not trackingRule['pass']:
                        results.append( { "tracking_number": trackingNumber,
                                          "courier": trackingRule['courier']})

                    #remove the tracking number from the email so it can't be matched again by subsequent rules
                    if trackingRule['parsingRule']['in'] is "body":
                        email["body"] = email["body"].replace( trackingNumber, '')
                    if trackingRule['parsingRule']['in'] is "subject":
                        email["subject"] = email["subject"].replace( trackingNumber, '')

        return { "tracking_numbers": results}

    def do_extractor_parsing(self, email_subject, email_body, parsing_set):

        results = []

        #parse email and convert to valid HTML.
        email_body = BeautifulSoup( email_body, 'lxml').prettify(formatter='html')

        for extractor_set in parsing_set:

            search_text = self.get_email_text( email_subject,email_body, extractor_set)

            result = self.do_extractor_set(extractor_set, search_text)
            results.extend(result)

        return results

    def get_email_text(self, email_subject, email_body, extractor_set):
        # are we operating on the subject or body.
        # if we are operating on the subject - that will always be a text string, no HTML tags
        if extractor_set.get( 'location', 'body') == 'subject':
            search_text = email_subject
        else:
            soup = BeautifulSoup(email_body, 'lxml')

            for tag in extractor_set.get( 'removeTags', []):
                for e in soup.findAll( tag ):
                    e.unwrap()

            # remove any New Lines for the HTML.
            soup = BeautifulSoup(soup.prettify(formatter='html').replace('\n', ' ').replace('\r',' '), 'lxml')

            format = extractor_set.get('format', 'text')
            if format == 'text':
                search_text = soup.get_text('\n', strip=True)
                found_links = '===HREF===\n'
                for a in soup.find_all('a', href=True):
                    found_links += a['href'] + '\n'

                search_text += '\n' + found_links
            elif format == 'HTML':
                search_text = soup.prettify(formatter='html')
            else:
                raise Exception('invalid format "{0}"'.format( format) )

        return search_text

    def do_extractor_set(self,extractor_set, search_text):

        results =[]

        start_position = 0
        stop_position = len(search_text)
        extractor_result = {}



        if extractor_set.get( 'start_position', None):
            #we start from the END of the match
            ignore_result, start_position, extractor_result = self.do_extractor( extractor_set['start_position'], search_text, 0, stop_position)

        if extractor_set.get( 'stop_position', None):
            #we stop at the START of the match - 1
            stop_position, ignore_result, extractor_result = self.do_extractor( extractor_set['stop_position'], search_text, 0, stop_position)
            stop_position -= 1


        looping = True
        while looping:
            extractor_set_result = {}
            for extractor in extractor_set['extractors']:
                #the next match starts from the end of the current match
                ignore_result, start_position, extractor_result = self.do_extractor( extractor, search_text, start_position, stop_position)

                if not extractor_result:
                    #exit, stop processing
                    extractor_set_result = {}
                    break
                for key in extractor_result.keys():
                    if extractor_set_result.get( key):
                        extractor_set_result[key] + extractor_result[key]
                    else:
                        extractor_set_result[key] = [] + extractor_result[key] #the [] forces an array, not needed, but still

            if extractor_set_result:
                results.append( extractor_set_result)
                looping = extractor_set['repeat']
            else:
                looping = False


        #the default at this point is to expect results to look like
        # [ {'courier'=['Australia Post'], 'tracking_numbers'=['1234', 'abcd'] }]
        # multiple couriers can happen, if the extractor is configured incorrectly.... but we ignore that for now ...
        # here we need to implement the functionality to have a fixed courier specified, or to use a regex to determine the courier
        #fixed courier
        if extractor_set.get( 'fixed_courier_name'):
            new_results = []
            for extractor_set_result in results:
                extractor_set_result['courier'] = extractor_set['fixed_courier_name']
                new_results.extend(extractor_set_result)
            results = new_results

        #tracking_number matching.
        #this is a little different as we will likly have [{'tracking_number'=['1234', 'abcd']}]
        #but need to end up with [{'courier'=['Australia Post'], 'tracking_numbers'=['1234'], 'order_id'=['1234]},{'courier'=['Couriers Please'], 'tracking_numbers'=['abcd']}]

        if extractor_set.get( 'tracking_number_parsing'):
            new_results = []
            for current_result in results:
                new_result = self.find_courier_name(current_result['tracking number'])
                # we need to copy values, other than courier and 'tracking number' into the new result
                for k in current_result:
                    if k != 'tracking number' and k != 'courier':
                        new_result[0][k] = current_result[k]

                new_results.extend(new_result)
            results = new_results


        return results

    def do_extractor(self, extractor, search_text, start_position, stop_position):

        #returns
        #  given an extractor of
        #     {
        #     'start': 'Your parcel has been dispatched via',
        #     'end': '\n',
        #     'item': 'courier',
        #     'repeat': False
        #     },
        # which produces a regex of
        #   'Your parcel has been dispatched via(?P<capture>.+?)\n'
        # we need to return the location in the search_text where the 'Y' in 'Your' is found
        # and the location of the ending '\n' + 1 character
        #  The location of the '\n' +1 character will tell us where to start the next regex search from
        #  The location of the 'Y'  is used when we specify a 'stop_position' in the config.
        #  The stop position will occur at the start of the regex match - 1
        # This applies to the entire extractor, including loops.  extractor_match_start will be the start of the first match of the first loop
        #        extractor_match_end will be the last location of the last match.
        # extractor_match_start = 123
        # extractor_match_end = 456
        # { '#item': [extracted values] }

        result = {}
        extractor_match_start = start_position
        extractor_match_end = start_position
        if not ( extractor.get( 'start', None) or extractor.get( 'end', None)):
            return start_position, {}

        if 'capture' in extractor:
            if  extractor['capture'].find( '(?P<capture>') == -1:
                extractor['capture'] = extractor['capture'].replace( '(', '(?P<capture>', 1)

            regex = extractor['start'] + extractor['capture'] + extractor['end']
        else:
            regex = extractor['start'] + '(?P<capture>.+?)' + extractor['end']

        pattern = re.compile( regex, re.I)

        looping = True

        while looping:
            match_object = pattern.search(search_text[extractor_match_end:stop_position]) # start from the end of the last match + 1

            if not match_object:
                looping = False
            else:
                if match_object:
                    extractor_match_end += match_object.regs[0][1]
                    if extractor_match_start == start_position: #it is still set to it's initial value, AKA first iteration of the loop
                        extractor_match_start = match_object.regs[0][0]
                    capture_text = match_object.group('capture').strip()
                    if result.get( extractor['item']):
                        result[ extractor['item'] ].append( capture_text)
                    else:
                        result[ extractor['item'] ] = [capture_text]

                    looping = extractor['repeat']


        return( extractor_match_start, extractor_match_end, result)

    def find_courier_name(self, tracking_numbers):
        rules = RetailerGlobalSettings.get().tracking_number_regex

        #we put the results in here first,
        # then later re-format them into the format expected as the return value
        staging_results = {}

        for tn in tracking_numbers:
            for rule in rules:
                if re.match( rule['regex'], tn):
                    if staging_results.get( rule['courier_name']):
                        staging_results[ rule['courier_name'] ]+ tn
                    else:
                        staging_results[ rule['courier_name'] ]= [tn]
                    break

        return_results = []

        for courier_name in staging_results:
            return_results.append( {'courier': [courier_name], 'tracking number': staging_results[courier_name]})


        return return_results

    def map_courier(self, retailer, sourceText):
        if retailer.courier_mappings:
            for cm in retailer.courier_mappings:
                if cm['sourceText'] == sourceText:
                    return cm['courierName']

        return sourceText

