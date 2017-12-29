from __future__ import absolute_import
from config import celeryconfig
import config
__author__ = 'james'

from celery import Celery

capp = Celery('async', backend=config.REDIS_URL,
              broker=config.REDIS_URL, include=['app.async.tasks','app.retailer_integration.tasks'])

# Optional configuration, see the application user guide.
capp.config_from_object(celeryconfig)
capp.conf.update(
    CELERY_TASK_RESULT_EXPIRES=3600,
)

if __name__ == '__main__':
    capp.start()