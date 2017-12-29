from sqlalchemy.exc import StatementError
from sqlalchemy.sql.elements import and_

import config
from app.model import GUID
from app.retailer_integration.model import Retailer
from app.util import validate_email
import uuid
import os
import logging
from sqlalchemy import event, ForeignKey
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import exc, validates, relationship
from app.model.meta.orm import one_to_many, UniqueMixin, one_to_one, many_to_one
from app import db
from app.model.meta.schema import Column, UserTypeBase, utcnow, Boolean,\
    TableColumnsBase, Address, EmailVerification
from app.exc import *
from app import util

__author__ = 'james'


logger = logging.getLogger()


class Promotion(db.Model, UniqueMixin, TableColumnsBase):
    __tablename__ = 'promotion'

    promotion_view_url = db.Column(db.String(1024), default="", nullable=False)
    promotion_destination_url = db.Column(db.String(1024), default="", nullable=False)

    retailer_id = db.Column(GUID(), ForeignKey('retailer.id'), nullable=False)
    retailer = relationship('Retailer', backref='promotions', lazy='select')

    is_active = db.Column(db.Boolean, server_default="true", nullable=False)

    def __init__(self, promotion_destination_url, retailer_id,is_active):
        self.promotion_destination_url = promotion_destination_url
        self.retailer = Retailer.query.get(retailer_id)
        self.is_active = is_active


class PromotionView(db.Model, UniqueMixin, TableColumnsBase):
    __tablename__ = 'promotion_view'
    promotion_id = db.Column(GUID(), ForeignKey('promotion.id'), nullable=False)

    view_path = db.Column(db.String(512), default='', nullable=False)

    promotion = relationship('Promotion', backref='views', lazy='select')

    user_id_fkey = db.Column(GUID(), ForeignKey('tmuser.id'), nullable=False)
    user = relationship('User', backref='promotion_views', lazy='select')

    def __init__(self, promotion, user, view_path):
        self.view_path = view_path
        self.promotion = promotion
        self.user = user


class PromotionClick(db.Model, UniqueMixin, TableColumnsBase):
    __tablename__ = 'promotion_click'
    promotion_view_id = db.Column(GUID(), ForeignKey('promotion_view.id'), nullable=False)
    promotion_view = relationship('PromotionView', backref='click', lazy='select')

    def __init__(self, promotion_view):
        self.promotion_view = promotion_view