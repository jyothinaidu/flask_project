#!/usr/bin/env bash

docker build  -f ops/base/Dockerfile -t="trustmile/python-base" .
docker build  -f ops/pgbouncer/Dockerfile -t="trustmile/pgbouncer-deploy" .
docker build  -f ops/deploy/Dockerfile -t="trustmile/python-deploy" .

docker push trustmile/python-base
docker push trustmile/python-deploy
docker push trustmile/python-deploy
