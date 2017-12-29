FROM trustmile/python-base
MAINTAINER James ORourke <james@trustmile.com>


ADD . /opt/trustmile/

# start supervisor to run our wsgi server
CMD cd /opt/trustmile/ && /opt/venv/bin/python run.py

EXPOSE 5000
