# -*- coding: utf-8 -*-

###
### DO NOT CHANGE THIS FILE
### 
### The code is auto generated, your change will be overwritten by 
### code generating.
###

from .api.account_deliveries_day_weekorMonth import AccountDeliveriesDayWeekormonth
from .api.account_register import AccountRegister
from .api.account_login import AccountLogin
from .api.account_seal_audit import AccountSealAudit
from .api.account_password import AccountPassword
from .api.account_courier_mapping import AccountCourierMapping
from .api.account_forgotPassword import AccountForgotpassword
from .api.account import Account
from .api.account_deliveries_retailerintegration import AccountDeliveriesRetailerintegration
from .api.account_deliveries_courier_weekorMonth import AccountDeliveriesCourierWeekormonth
from .api.account_resetPassword_resetToken import AccountResetpasswordResettoken
from .api.ping import Ping
from .api.account_attributes import AccountAttributes


routes = [
    dict(resource=AccountDeliveriesDayWeekormonth, urls=['/account/deliveries/day/<weekorMonth>'], endpoint='account_deliveries_day_weekorMonth'),
    dict(resource=AccountRegister, urls=['/account/register'], endpoint='account_register'),
    dict(resource=AccountLogin, urls=['/account/login'], endpoint='account_login'),
    dict(resource=AccountSealAudit, urls=['/account/seal-audit'], endpoint='account_seal_audit'),
    dict(resource=AccountPassword, urls=['/account/password'], endpoint='account_password'),
    dict(resource=AccountCourierMapping, urls=['/account/courier-mapping'], endpoint='account_courier_mapping'),
    dict(resource=AccountForgotpassword, urls=['/account/forgotPassword'], endpoint='account_forgotPassword'),
    dict(resource=Account, urls=['/account'], endpoint='account'),
    dict(resource=AccountDeliveriesRetailerintegration, urls=['/account/deliveries/retailerintegration'], endpoint='account_deliveries_retailerintegration'),
    dict(resource=AccountDeliveriesCourierWeekormonth, urls=['/account/deliveries/courier/<weekorMonth>'], endpoint='account_deliveries_courier_weekorMonth'),
    dict(resource=AccountResetpasswordResettoken, urls=['/account/resetPassword/<resetToken>'], endpoint='account_resetPassword_resetToken'),
    dict(resource=Ping, urls=['/ping'], endpoint='ping'),
    dict(resource=AccountAttributes, urls=['/account/attributes'], endpoint='account_attributes'),
]