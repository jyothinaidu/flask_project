# -*- coding: utf-8 -*-

###
### DO NOT CHANGE THIS FILE
### 
### The code is auto generated, your change will be overwritten by 
### code generating.
###

from .api.anonymous_tracking_courierSlug_trackingNumber import AnonymousTrackingCourierslugTrackingnumber
from .api.account_register import AccountRegister
from .api.deliveries_tracking_deliveryId import DeliveriesTrackingDeliveryid
from .api.account_reverifyEmail import AccountReverifyemail
from .api.deliveries import Deliveries
from .api.account_forgotPassword import AccountForgotpassword
from .api.order_orderId import OrderOrderid
from .api.account import Account
from .api.deliveries_delegateLink_deliveryId import DeliveriesDelegatelinkDeliveryid
from .api.deliveries_neighbourReceiveLookup_trackingNumber import DeliveriesNeighbourreceivelookupTrackingnumber
from .api.account_resetPassword_resetToken import AccountResetpasswordResettoken
from .api.account_password import AccountPassword
from .api.deliveries_cardLookup_cardId import DeliveriesCardlookupCardid
from .api.deliveries_deliveryId import DeliveriesDeliveryid
from .api.user_presence import UserPresence
from .api.deliveries_trustmile_deliveryId import DeliveriesTrustmileDeliveryid
from .api.feedback import Feedback
from .api.promotion_viewlist import PromotionViewlist
from .api.deliveries_recipientHandover_deliveryId import DeliveriesRecipienthandoverDeliveryid
from .api.deliveries_delegate import DeliveriesDelegate
from .api.account_login import AccountLogin
from .api.account_verifyEmail_verificationCode import AccountVerifyemailVerificationcode
from .api.deliveries_neighbourReceive_deliveryId import DeliveriesNeighbourreceiveDeliveryid
from .api.promotion_click_promotionViewId import PromotionClickPromotionviewid
from .api.account_anonymous_register import AccountAnonymousRegister
from .api.deliveries_feedback_deliveryId import DeliveriesFeedbackDeliveryid


routes = [
    dict(resource=AnonymousTrackingCourierslugTrackingnumber, urls=['/anonymous/tracking/<courierSlug>/<trackingNumber>'], endpoint='anonymous_tracking_courierSlug_trackingNumber'),
    dict(resource=AccountRegister, urls=['/account/register'], endpoint='account_register'),
    dict(resource=DeliveriesTrackingDeliveryid, urls=['/deliveries/tracking/<deliveryId>'], endpoint='deliveries_tracking_deliveryId'),
    dict(resource=AccountReverifyemail, urls=['/account/reverifyEmail'], endpoint='account_reverifyEmail'),
    dict(resource=Deliveries, urls=['/deliveries'], endpoint='deliveries'),
    dict(resource=AccountForgotpassword, urls=['/account/forgotPassword'], endpoint='account_forgotPassword'),
    dict(resource=OrderOrderid, urls=['/order/<orderId>'], endpoint='order_orderId'),
    dict(resource=Account, urls=['/account'], endpoint='account'),
    dict(resource=DeliveriesDelegatelinkDeliveryid, urls=['/deliveries/delegateLink/<deliveryId>'], endpoint='deliveries_delegateLink_deliveryId'),
    dict(resource=DeliveriesNeighbourreceivelookupTrackingnumber, urls=['/deliveries/neighbourReceiveLookup/<trackingNumber>'], endpoint='deliveries_neighbourReceiveLookup_trackingNumber'),
    dict(resource=AccountResetpasswordResettoken, urls=['/account/resetPassword/<resetToken>'], endpoint='account_resetPassword_resetToken'),
    dict(resource=AccountPassword, urls=['/account/password'], endpoint='account_password'),
    dict(resource=DeliveriesCardlookupCardid, urls=['/deliveries/cardLookup/<cardId>'], endpoint='deliveries_cardLookup_cardId'),
    dict(resource=DeliveriesDeliveryid, urls=['/deliveries/<deliveryId>'], endpoint='deliveries_deliveryId'),
    dict(resource=UserPresence, urls=['/user/presence'], endpoint='user_presence'),
    dict(resource=DeliveriesTrustmileDeliveryid, urls=['/deliveries/trustmile/<deliveryId>'], endpoint='deliveries_trustmile_deliveryId'),
    dict(resource=Feedback, urls=['/feedback'], endpoint='feedback'),
    dict(resource=PromotionViewlist, urls=['/promotion/viewlist'], endpoint='promotion_viewlist'),
    dict(resource=DeliveriesRecipienthandoverDeliveryid, urls=['/deliveries/recipientHandover/<deliveryId>'], endpoint='deliveries_recipientHandover_deliveryId'),
    dict(resource=DeliveriesDelegate, urls=['/deliveries/delegate'], endpoint='deliveries_delegate'),
    dict(resource=AccountLogin, urls=['/account/login'], endpoint='account_login'),
    dict(resource=AccountVerifyemailVerificationcode, urls=['/account/verifyEmail/<verificationCode>'], endpoint='account_verifyEmail_verificationCode'),
    dict(resource=DeliveriesNeighbourreceiveDeliveryid, urls=['/deliveries/neighbourReceive/<deliveryId>'], endpoint='deliveries_neighbourReceive_deliveryId'),
    dict(resource=PromotionClickPromotionviewid, urls=['/promotion/click/<promotionViewId>'], endpoint='promotion_click_promotionViewId'),
    dict(resource=AccountAnonymousRegister, urls=['/account/anonymous/register'], endpoint='account_anonymous_register'),
    dict(resource=DeliveriesFeedbackDeliveryid, urls=['/deliveries/feedback/<deliveryId>'], endpoint='deliveries_feedback_deliveryId'),
]