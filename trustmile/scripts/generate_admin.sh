#!/usr/bin/env bash

ls -d ./app/api/admin/api/* | grep -v '/__init__\.py$' | xargs rm

$WORKON_HOME/trustmile-api/bin/swagger_py_codegen  --swagger-doc schemas/admin-swagger.yml -p api app --ui --spec


# http://192.168.59.103:5000/s/swagger-ui/index.html
