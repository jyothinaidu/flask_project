__author__ = 'james'


class AbstractDeliveriesIterator:
    pass


class ConsumerDeliveriesIterator:

    def __init__(self, delivery_items):
        # TODO: sort
        def compare_delivery_item(item1, item2):
            if item1['courierName'] == 'TrustMile' and item2['courierName'] == 'TrustMile':
                if item1['updated_at'] > item2['updated_at']:
                    return 1
                elif item1['updated_at'] == item2['updated_at']:
                    return 0
                else:
                    return -1
            elif item1['courierName'] == 'TrustMile' and item2['courierName'] != 'TrustMile':
                return 1
            elif item1['courierName'] != 'TrustMile' and item2['courierName'] == 'TrustMile':
                return -1
            elif item1['courierName'] != 'TrustMile' and item2['courierName'] != 'TrustMile':
                if item1['updated_at'] > item2['updated_at']:
                    return 1
                elif item1['updated_at'] == item2['updated_at']:
                    return 0
                else:
                    return -1

        self.delivery_items = sorted(delivery_items, compare_delivery_item)
        self.index = 0

    def __iter__(self):
        return self

    def next(self):
        if self.index < len(self.delivery_items):
            r = self.delivery_items[self.index]
            self.index += 1
            return r
        else:
            raise StopIteration



