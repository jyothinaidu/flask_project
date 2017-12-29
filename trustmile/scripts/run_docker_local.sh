#!/usr/bin/env bash


#!/usr/bin/env bash

# pgbouncer
docker stop pgbouncer
docker rm -f pgbouncer
docker run  --name pgbouncer -P -d -t -i trustmile/pgbouncer-deploy


docker stop tm-api
docker rm -f tm-api
docker run --name tm-api -d -p 80:8080 --link pgbouncer:pgbouncer -t -i trustmile/python-deploy
#docker run  --name pgbouncer -d  -p 6432:6432 -t -i   trustmile/pgbouncer-deploy
#docker run  --name tm-api -d  -p 80:8080 -t -i   trustmile/python-deploy
