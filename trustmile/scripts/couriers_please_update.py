import requests
import json
import argparse

couriers_please_data = {
    "Courier": "CouriersPlease",
    "storeDlb": "LOC0042184",
    "missedDeliveryCardNumber": '19100787713',
    "labelNumber": 'CPAOAES0001308',
    "consignmentNumber": "CPAOAE0001308",
    "totalNumberOfLogisticUnits": "1",
    "contactName": "Narendra",
    "mobileNumber": "",
    "emailAddress": "kathayatnk@gmail.com"
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--recipient", '-r', help="Recipient email to post the failure notice for", required=True)
    parser.add_argument("--labelNumber", '-l', help="Label number for notice", required=True)
    parser.add_argument("--cardNumber", '-c', help="Card Number for notice", required=True)
    parser.add_argument("--name", '-n', help="Name for notice", required=True)

    args = parser.parse_args()

    couriers_please_data['missedDeliveryCardNumber'] = args.cardNumber
    couriers_please_data['labelNumber'] = args.labelNumber
    couriers_please_data['emailAddress'] = args.recipient
    couriers_please_data['contactName'] = args.name

    rv = requests.post('http://127.0.0.1:5000/couriers_please', data=json.dumps(couriers_please_data),
                       headers={'content-type': 'application/json', 'X-courier-apiKey': 'e686b40e1d72374de9d31bdfb73e6c0367b7d45fb2772f676c6e8b0985366d06'})
