FROM trustmile/python-base
MAINTAINER James ORourke <james@trustmile.com>

RUN apt-get install -y postgresql-client

RUN pip install supervisor-stdout

# file management, everything after an ADD is uncached, so we do it as late as
# possible in the process.
ADD ./config/supervisord.conf /etc/supervisord.conf
ADD ./config/nginx.conf /etc/nginx/nginx.conf
ADD . /opt/trustmile/
#RUN mkdir /opt/trustmile/logs

#RUN htpasswd -b  -c /etc/nginx/.htpasswd trustmile wyiss8Orn6

# restart nginx to load the config
RUN service nginx stop

# start supervisor to run our wsgi server
CMD service supervisor restart
