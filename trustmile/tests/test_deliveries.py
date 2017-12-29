from nose.tools import eq_, assert_greater

from app import db
from app.deliveries.deliveries_results import DeliveryResultsAggregator
from app.deliveries.model import Article, Deliveries, Courier, TrustmileDelivery, Consignment
from app.users.model import CourierUser, ConsumerUser, UserConsignment
from tests.util import load_couriers
from tests import TransactionalTest

__author__ = 'james'


class DeliveriesTest(TransactionalTest):


    @classmethod
    def setUpClass(cls):
        super(DeliveriesTest, cls).setUpClass()
        load_couriers()
        db.session.commit()

    @classmethod
    def tearDownClass(cls):
        super(DeliveriesTest, cls).tearDownClass()

    def test_find_delivery(self):

        tracking_number = 'LV9006545301000600205'
        courier = Courier.retrieve_courier('australia-post')
        art = Article(tracking_number, courier=courier, user_entered=True)
        db.session.add(art)

        entity_ids = Deliveries.find_deliveries(['LV9006545301000600205'])

        assert_greater(len(entity_ids), 0)

    def test_add_delivery_for_user(self):

        tracking_number = u'VY30029390'
        cons_user = ConsumerUser.create('james@trustmile.com', 'boundary', name='James O''Rourke')
        u = cons_user.user

        courier = Courier.retrieve_courier('australia-post')

        consignment = Deliveries.user_adds_delivery(u, courier.courier_slug, tracking_number, "My package")

        assert consignment
        eq_(u.user_consignments[0].user_description, "My package")


    def test_create_trustmile_delivery(self):

        courier_user = CourierUser.create('brucearthurs', 'boundary', 'James O''Rourke', Courier.retrieve_courier('couriers-please'))
        cons_user = ConsumerUser.create('james@trustmile.com', 'boundary', name='James O''Rourke')

        articles = Article.new_articles(courier_user, ['LV9006545301000600205', 'VY30029390'])

        tm_delivery = TrustmileDelivery.create(courier_user, articles)
        assert tm_delivery
        assert tm_delivery.courier
        eq_(len(tm_delivery.articles), 2)

    def test_update_trustmile_delivery_info(self):

        courier_user = CourierUser.create('brucearthurs', 'boundary', 'James O''Rourke',
                                          Courier.retrieve_courier('couriers-please'))
        cons_user = ConsumerUser.create('james@trustmile.com', 'boundary', name='James O''Rourke')

        articles = Article.new_articles(courier_user, ['LV9006545301000600205', 'VY30029390'])

        tm_delivery = TrustmileDelivery.create(courier_user, articles)
        tm_delivery.update_info(recipient_name='James Smith')
        db.session.commit()
        tm_delivery_id = tm_delivery.id
        tm_delivery_retrieved = TrustmileDelivery.query.filter(TrustmileDelivery.id == tm_delivery_id).first()
        assert tm_delivery_retrieved
        assert tm_delivery_retrieved.courier
        eq_(tm_delivery_retrieved.recipient_info['recipientName'], 'James Smith')

    def test_delivery_results(self):

        cons, tm_delivery = self.setup_delivery_results()

        ag = DeliveryResultsAggregator(consignments = cons, trustmile_deliveries=[tm_delivery])

        ag.aggregate()
        results = ag.sort()

    def setup_delivery_results(self):

        courier = Courier.retrieve_courier('couriers-please')
        courier_user = CourierUser.create('brucearthurs', 'boundary', 'James O''Rourke', courier)
        cons_user = ConsumerUser.create('james@trustmile.com', 'boundary', 'James O''Rourke')
        neighbour_user = ConsumerUser.create('james+neighbour@trustmile.com', 'boundary',
                                             name='James Good Neighbour ORourke')
        tns = [('tnt', '896341434'), ('usps', '9361289949166151976035')]
        cons = []
        articles = []
        for t in tns:
            courier_obj = Courier.retrieve_courier(t[0])
            c = Consignment.create_or_get_consignment(courier_obj, t[1])
            Deliveries.user_adds_delivery(cons_user.user, t[0], t[1], "My Delivery")
            uc = UserConsignment(c, "Hellow world")
            cons_user.user.user_consignments.append(uc)
            cons.append(c)
            articles.extend(c.articles)
        tm_delivery = TrustmileDelivery.create(courier_user, articles)
        tm_delivery.neighbour = neighbour_user
        return cons, tm_delivery

    def test_get_by_tracking_for_neighbour(self):
        courier = Courier.retrieve_courier('tnt')
        courier_user = CourierUser.create('brucearthurs', 'boundary', 'James O''Rourke', courier)
        tns = ['896341434', '9361289949166151976035']
        articles = []
        for t in tns:
            articles.append(Article(t, courier = courier, user_entered= False))
        tm_delivery = TrustmileDelivery.create(courier_user, articles)
        from app.ops.base import DeliveryState
        tm_delivery.state = DeliveryState.TRANSIT_TO_NEIGHBOUR.value

        neighbour = tm_delivery.neighbour
        tmd = TrustmileDelivery.get_by_tracking_for_neighbour(neighbour, tns[0])
        eq_(tmd.id, tm_delivery.id)







