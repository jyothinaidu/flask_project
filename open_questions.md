1. TMdelivery create:
 -- should articles be created if not existent?
 -- how is TMdelivery connected to location?  


2. Address - properly implement as_physical (how?)
	* Postal vs physical fields *

3.   DELETE /articles/{trackingNumber}:
	- shouldn't it be  /deliveries/<deliveryId>/articles/{trackingNumber}
	- return value of {articles:[id, id, ...]}  - what is it?
	- which delivery states allow deletion of artiles?

