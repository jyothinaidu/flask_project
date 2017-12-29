from app.deliveries.model import Deliveries
from app.users.model import User

user = User.query.get('5b364433-74c9-40a5-b84e-7b0a413e6e41')

results = Deliveries.get_deliveries_info_for_user(user)

