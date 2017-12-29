#!/usr/bin/env bash
export PYTHONPATH=$PYTHONPATH:/home/ec2-user/.virtualenvs/api-python2/lib64/python2.7/dist-packages/
gunicorn app:app -D  -w  4 -b 0.0.0.0:5000 --chdir=$PROJECT_HOME --access-logfile gunicorn_access.log -p gunicorn.pid
