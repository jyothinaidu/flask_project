#pres_tm_results = [{'courier_name': 'TrustMile', 'trackingNumber': str(tm.id),
            #                     'description': 'Packages for a neighbour', "latestStatus": tm.get_latest_status(),
            #                     'deliveryId': str(tm.id), 'updated_at': tm.updated_at} for tm in tm_deliveries]
            #
            # results = {'deliveries': [{'courier_name': c.courier.courier_name, 'trackingNumber': c.tracking_number,
            #                            "description": c.user_description, "latestStatus": c.latest_status(),
            #                            'deliveryId': str(c.id), 'updated_at': c.updated_at} for c in consignments]}


class DeliveryItemSummary(object):

    def __init__(self, courier_name, tracking_numbers, description, latest_status, delivery_id, updated_at):
        self.courier_name = courier_name
        self.tracking_numbers = tracking_numbers
        self.description = description
        self.latest_status = latest_status
        self.delivery_id = delivery_id
        self.updated_at = updated_at


class DeliveryResultsAggregator(object):

    def __init__(self, consignments = None, trustmile_deliveries = None, articles = None):
        self.consignments = consignments
        self.trustmile_deliveries = trustmile_deliveries
        self.articles = articles


    def aggregate(self):

        for c in self.consignments:
            for td in self.trustmile_deliveries:
                # TODO: Must unravel those tacking numbers which overlap with existing consignments
                for a in c.articles:
                    if a in td.articles:
                        c.articles.remove(a)

        cons_summary = [DeliveryItemSummary(c.courier.courier_name, [a.tracking_number for a in c.articles], c.user_consignments[0].user_description, c.latest_status(),
                                             str(c.id), c.updated_at) for c in self.consignments]

        # TODO: Implement user description for a TMD - eg. either for reicipient or derived from tracking numbers
        tm_summary  = [DeliveryItemSummary(td.courier.fullName, [a.tracking_number for a in td.articles], td.user_description,
                                            td.latest_status, str(td.id), td.updated_at) for td in self.trustmile_deliveries]

        cons_summary.extend(tm_summary)
        self.results = cons_summary
        return self.results

    def sort(self):

        def compare_delivery_item(item1, item2):
            if item1.courier_name == 'TrustMile' and item2.courier_name == 'TrustMile':
                if item1.updated_at > item2.updated_at:
                    return 1
                elif item1.updated_at == item2.update_at:
                    return 0
                else:
                    return -1
            elif item1.courier_name == 'TrustMile' and item2.courier_name != 'TrustMile':
                return 1
            elif item1.courier_name != 'TrustMile' and item2.courier_name == 'TrustMile':
                return -1
            elif item1.courier_name != 'TrustMile' and item2.courier_name != 'TrustMile':
                if item1.updated_at > item2.updated_at:
                    return 1
                elif item1.updated_at == item2.updated_at:
                    return 0
                else:
                    return -1

        return sorted(self.results, compare_delivery_item, reverse=True)




