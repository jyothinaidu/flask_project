from nose.tools import eq_

from app.deliveries.model import Courier
from tests import TransactionalTest
from app import db


class CouriersTest(TransactionalTest):

    @staticmethod
    def test_courier_create():
        phone = '029555555'
        c = Courier("Allied Express", 'allied-express', phone, 'http://www.alliedexpress.com.au/',
                    trustmile_courier=False, tracking_url='http://www.alliedexpress.com.au/',
                    tracking_info_supported=False)
        db.session.add(c)
        db.session.commit()

        c1 = Courier.query.filter(Courier.courier_slug == 'allied-express').first()
        eq_(c1.phone, phone)
