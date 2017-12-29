#!/bin/sh

if [ -n "$TM_HOME" ];
	then cd $TM_HOME;
fi

    ls -d ./app/api/admin/api/* | grep -v '/__init__\.py$' | xargs rm
    ls -d ./app/api/consumer_v1/api/* | grep -v '/__init__\.py$' | xargs rm
    ls -d ./app/api/courier_v1/api/* | grep -v '/__init__\.py$' | xargs rm
    ls -d ./app/api/retailer/api/* | grep -v '/__init__\.py$' | xargs rm

for ff in retailer courier consumer admin
do
	echo $ff

	python scripts/append_definitions.py  schemas/$ff-swagger.yml
	swagger_py_codegen --swagger-doc schemas/$ff-swagger-ammended.yml -p api app --ui --spec
done
