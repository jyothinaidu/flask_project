export TRUSTMILE_ENV_TYPE=test
nosetests -v  tests.test_api:ConsumerApiTest
nosetests -v  tests.test_deliveries:DeliveriesTest
nosetests -v  tests.test_distances:DistancesTest
nosetests -v  tests.test_users
nosetests -v  tests.test_api_courier:CourierApiTest

