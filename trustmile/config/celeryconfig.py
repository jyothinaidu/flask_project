from celery.schedules import crontab, timedelta

CELERYBEAT_SCHEDULE = {
    'send-couriers-please-file': {
        'task': 'app.async.tasks.send_couriers_please_notifications',
        'schedule': crontab(minute='*/1'),
    },
    """ Run this one at 1 am """
    'archive-old-trustmile-deliveries': {
        'task': 'app.async.tasks.archive_old_trustmile_deliveries',
        'schedule': crontab(hour=[1,]),
    },
#'check-retailer-email': {
#        'task': 'app.retailer_integration.tasks.run_email_pull',
#        'schedule': timedelta(seconds=30),
#        'args': (),
#    },
    'check-expired-locations': {
        'task': 'app.async.tasks.check_expired_locations',
        'schedule': timedelta(seconds=30),
        'args': (),
    },
}

