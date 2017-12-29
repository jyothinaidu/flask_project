# -*- coding: utf-8 -*-

###
### DO NOT CHANGE THIS FILE
### 
### The code is auto generated, your change will be overwritten by 
### code generating.
###

from .api.nearestNeighbours_latitude_longitude import NearestneighboursLatitudeLongitude
from .api.deliveries_deliveryId import DeliveriesDeliveryid
from .api.deliveries_deliveryId_articles import DeliveriesDeliveryidArticles
from .api.logout import Logout
from .api.login import Login
from .api.deliveries import Deliveries
from .api.account import Account
from .api.deliveries_state_deliveryState import DeliveriesStateDeliverystate
from .api.articles_trackingNumber import ArticlesTrackingnumber
from .api.login_password import LoginPassword


routes = [
    dict(resource=NearestneighboursLatitudeLongitude, urls=['/nearestNeighbours/<latitude>/<longitude>'], endpoint='nearestNeighbours_latitude_longitude'),
    dict(resource=DeliveriesDeliveryid, urls=['/deliveries/<deliveryId>'], endpoint='deliveries_deliveryId'),
    dict(resource=DeliveriesDeliveryidArticles, urls=['/deliveries/<deliveryId>/articles/'], endpoint='deliveries_deliveryId_articles'),
    dict(resource=Logout, urls=['/logout'], endpoint='logout'),
    dict(resource=Login, urls=['/login'], endpoint='login'),
    dict(resource=Deliveries, urls=['/deliveries'], endpoint='deliveries'),
    dict(resource=Account, urls=['/account'], endpoint='account'),
    dict(resource=DeliveriesStateDeliverystate, urls=['/deliveries/state/<deliveryState>'], endpoint='deliveries_state_deliveryState'),
    dict(resource=ArticlesTrackingnumber, urls=['/articles/<trackingNumber>'], endpoint='articles_trackingNumber'),
    dict(resource=LoginPassword, urls=['/login/password'], endpoint='login_password'),
]