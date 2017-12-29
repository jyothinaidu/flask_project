#!/usr/bin/env bash

OPERATION="$1"


if [[ $1 == "--help" ]]
    then
        echo $0, 'start|stop|restart'
        exit 1
fi

CELERY_LOG_DIR=/var/log/celery
CELERY_PID_DIR=/var/run/celery
GUNICORN_LOG_DIR=/var/log/gunicorn
GUNICORN_PID_DIR=/var/run/gunicorn

if [[ -z $PROJECT_HOME ]]
    then
        PROJECT_HOME = /home/ec2-user/trustmile-backend/trustmile
fi

if [[ -z $VIRTUAL_ENV ]]
    then
        VIRTUAL_ENV = /home/ec2-user/.virtualenvs/api-python2
fi

export PYTHONPATH=$PYTHONPATH:$VIRTUAL_ENV/lib64/python2.7/dist-packages/
function start_celery() {
    PATH=$VIRTUAL_ENV/bin celery multi $1 worker  -A app.async.celery_app:capp --beat --schedule config/celeryconfig.py --loglevel=debug --pidfile=$CELERY_PID_DIR/celery.pid --logfile=$CELERY_LOG_DIR/celery.log
}



function do_gunicorn() {
    if [[ $OPERATION = "restart" ]]
        then
            GunicornPID=$(<"$GUNICORN_PID_DIR/gunicorn.pid")
            kill -15 "$GunicornPID"
            #export PYTHONPATH=$PYTHONPATH:$VIRTUAL_ENV/lib64/python2.7/dist-packages/
            export PATH=$VIRTUAL_ENV/bin/
            #NEW_RELIC_CONFIG_FILE=config/newrelic.ini newrelic-admin run-program gunicorn app:app -D  -w  4 -b 0.0.0.0:5000 --chdir=$PROJECT_HOME --access-logfile gunicorn_access.log -p gunicorn.pid
            gunicorn app:app -D  -w  5 -b 0.0.0.0:5000 --chdir=$PROJECT_HOME --access-logfile $GUNICORN_LOG_DIR/gunicorn_access.log -p $GUNICORN_PID_DIR/gunicorn.pid
    elif [[ $OPERATION = "start" ]]
        then
            #export PYTHONPATH=$PYTHONPATH:$VIRTUAL_ENV/lib64/python2.7/dist-packages/
            export PATH=$VIRTUAL_ENV/bin/
            #NEW_RELIC_CONFIG_FILE=config/newrelic.ini newrelic-admin run-program gunicorn app:app -D  -w  4 -b 0.0.0.0:5000 --chdir=$PROJECT_HOME --access-logfile gunicorn_access.log -p gunicorn.pid
            gunicorn app:app -D  -w  5 -b 0.0.0.0:5000 --chdir=$PROJECT_HOME --access-logfile $GUNICORN_LOG_DIR/gunicorn_access.log -p $GUNICORN_PID_DIR/gunicorn.pid 
    elif [[ $OPERATION = "stop" ]]
        then
            GunicornPID=$(<"$GUNICORN_PID_DIR/gunicorn.pid")
            kill -15 "$GunicornPID"
    fi

}

if [[ $CELERY_GUNICORN_BOTH = 'celery' ]]
    then
        start_celery $OPERATION
elif  [[ $CELERY_GUNICORN_BOTH = 'gunicorn' ]]
    then
        do_gunicorn $OPERATION
elif [[ $CELERY_GUNICORN_BOTH = 'both' ]]
    then 
        do_gunicorn $OPERATION
        start_celery $OPERATION
fi


