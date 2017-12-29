#!/usr/bin/env bash
celery multi start worker  -A app.async.celery_app:capp --beat --loglevel=debug --pidfile=celery.pid --logfile=celery.log