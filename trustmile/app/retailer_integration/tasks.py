from celery.utils.log import get_task_logger
from redlock import RedLock, RedLockError
import config

from app.async.celery_app import capp
from app.retailer_integration.EmailWorker import EmailWorker
from app.model.meta.base import close_db
from app.retailer_integration.model import Retailer

__author__ = 'james'

logger = get_task_logger(__file__)

@capp.task(bind=True)
@close_db
def run_email_pull(self):
    retailers = Retailer.get_all_ids()
    for r in retailers:
        if self.request.id:
            pull_mail_for_retailer.delay( r.id)
        else:
            pull_mail_for_retailer( r.id)


@capp.task(bind=True)
@close_db
def pull_mail_for_retailer(self, retailer_id):

    #locking ensures only one task is running per retailer
    # should there be 2 tasks for a retailer, the second task exits
    # this prevents big mail boxes queuing up tasks
    try:
        retailer = Retailer.get( id=retailer_id)
        with RedLock( 'retailer-{0}'.format(retailer_id), [{"host": config.REDIS_HOST, "port": config.REDIS_PORT, "db": config.REDIS_DB} ], retry_delay=0, retry_times=1):
            try:
                ew = EmailWorker()
                ew.process_email(retailer)
            except Exception, e:
                logger.error(u'Exception in pull_mail_for_retailer for retailer {0},{1},{2}'.format( retailer_id, retailer.website_name,retailer.website_url), exc_info=True)

    except RedLockError, e:
        #no lock acquired.  exit quietly
        logger.info(u"Email Worker lock not acquired for retailer {0}".format(retailer_id))


