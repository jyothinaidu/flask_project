#!/usr/bin/env bash
docker run -d  -p 5000:5000  --name tm --restart=always  trustmile/api-service /run.sh
