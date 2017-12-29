from app.messaging.push import PushNotification

import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", '-e', help="Usernane to send push to - generally email.", required = True)
    parser.add_argument("--tracking_number", '-tn', help="tracking number for item to send push about", required=True)
    parser.add_argument("--item_description", '-d', help="The description of the item", required=True)
    parser.add_argument("--status", '-s', help="status of the item", required=True)
    args = parser.parse_args()

    PushNotification.send_new_tracking_notification(args.email, args.tracking_number, args.item_description,
                                                    args.status)
