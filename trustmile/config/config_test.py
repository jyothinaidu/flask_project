__author__ = 'james'
import yaml
import logging
from logging import config


with open('config/config.yml') as f:
    d = yaml.load(f)

config.dictConfig(d)

print d

logger = logging.getLogger()

logger.info(u'Foobar')
