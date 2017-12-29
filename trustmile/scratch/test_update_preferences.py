from app.users.model import User
from app import db
mu = User.query.get('465c4b3e-07dd-4cff-9e0c-ccc4dac2383d')
mu.update_preferences({'values':[{'key': 'neighbourEnabled', 'value': "True"}]})
db.session.commit()