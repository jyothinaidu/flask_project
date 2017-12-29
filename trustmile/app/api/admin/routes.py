# -*- coding: utf-8 -*-

###
### DO NOT CHANGE THIS FILE
### 
### The code is auto generated, your change will be overwritten by 
### code generating.
###

from .api.seal_seal_id_seal_audit import SealSealIdSealAudit
from .api.retailers import Retailers
from .api.allNeighbourLocations import Allneighbourlocations
from .api.seal_seal_id import SealSealId
from .api.promotion import Promotion
from .api.neighbourSignup import Neighboursignup
from .api.retailers_umbraco_id import RetailersUmbracoId


routes = [
    dict(resource=SealSealIdSealAudit, urls=['/seal/<seal_id>/seal-audit'], endpoint='seal_seal_id_seal_audit'),
    dict(resource=Retailers, urls=['/retailers'], endpoint='retailers'),
    dict(resource=Allneighbourlocations, urls=['/allNeighbourLocations'], endpoint='allNeighbourLocations'),
    dict(resource=SealSealId, urls=['/seal/<seal_id>'], endpoint='seal_seal_id'),
    dict(resource=Promotion, urls=['/promotion'], endpoint='promotion'),
    dict(resource=Neighboursignup, urls=['/neighbourSignup'], endpoint='neighbourSignup'),
    dict(resource=RetailersUmbracoId, urls=['/retailers/<umbraco_id>'], endpoint='retailers_umbraco_id'),
]