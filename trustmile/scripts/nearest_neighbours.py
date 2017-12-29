from app.async.tasks import *
import argparse
import pprint
from app.location.distances import NearestNeighbours
from app.users.model import ConsumerUser

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", "-e", help="Origin username", required = True)
    parser.add_argument("--radius", "-r", help="radius for finding", required=True)
    args = parser.parse_args()


    original_user = ConsumerUser.query.filter(ConsumerUser.email_address == args.email).one()

    if len(original_user.user.user_address) > 0 and original_user.user.user_address[0].location:
        location = original_user.user.user_address[0].location

    nn = NearestNeighbours(location, radius= args.radius)

    distances = nn.distances

    results = [(d[0].email_address, d[0].user.user_address[0].addressLine1, d[1]) for d in distances.distances]

    print results