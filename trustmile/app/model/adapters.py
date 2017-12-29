



class TrustmileDeliveryInfoAdapter:

    def __init__(self, trustmile_delivery, delivery_feedback_map, card_number_map):
        self.trustmile_delivery = trustmile_delivery
        self.delivery_feedback_map = delivery_feedback_map
        self.card_number_map = card_number_map

    def get_delivery_info_json(self):
        pass


class ConsignmentDeliveryInfoAdapter:

    def __init__(self, consignment, delivery_feedback_map):
        self.trustmile_delivery = trustmile_delivery
        self.delivery_feedback_map = delivery_feedback_map

    def get_delivery_info_json(self):
        pass


