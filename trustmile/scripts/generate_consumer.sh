#!/usr/bin/env bash

$WORKON_HOME/trustmile-api-new/bin/swagger_py_codegen  --swagger-doc schemas/consumer-swagger.yml -p api app --ui --spec


# http://192.168.59.103:5000/s/swagger-ui/index.html
