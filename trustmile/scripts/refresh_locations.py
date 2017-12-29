from app.async import tasks
from app.users.model import ConsumerUser
import time

if __name__ == '__main__':

    rs = ConsumerUser.query.all()

    m = 50
    for i, r in enumerate(rs):
        if r.user.user_address:
            tasks.update_address_location.delay(r.user.user_address[0].id)
        if i % m == 0:
            time.sleep(5)
