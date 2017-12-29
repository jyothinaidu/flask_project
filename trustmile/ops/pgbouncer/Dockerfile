FROM ubuntu:15.10
MAINTAINER James ORourke <james@trustmile.com>
RUN apt-get update

RUN DEBIAN_FRONTEND=noninteractive apt-get -y install wget
RUN DEBIAN_FRONTEND=noninteractive apt-get -y install  logrotate postgresql-client-common postgresql-common postgresql-client
RUN DEBIAN_FRONTEND=noninteractive apt-get -y install pgbouncer

ADD config/pgbouncer.ini /etc/pgbouncer/pgbouncer.ini
RUN mkdir /var/log/pgbouncer
RUN mkdir /var/run/pgbouncer

RUN adduser postgres sudo 
RUN chown -R postgres:postgres /etc/pgbouncer
RUN chown -R postgres:postgres /etc/pgbouncer
RUN chown root:postgres /var/log/pgbouncer
RUN chown root:postgres /var/run/pgbouncer
RUN chmod 1775 /var/log/pgbouncer
RUN chmod 1775 /var/run/pgbouncer
#chmod 640 /etc/pgbouncer/userlist.txt

EXPOSE 6432
CMD  pgbouncer -u postgres -R  /etc/pgbouncer/pgbouncer.ini


