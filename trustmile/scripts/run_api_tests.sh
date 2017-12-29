#!/usr/bin/env bash

nosetests -v tests.test_api:ConsumerApiTest
nosetests -v tests.test_api_courier:CourierApiTest
