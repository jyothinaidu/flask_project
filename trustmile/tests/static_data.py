
retailer_config = {
    "from_email_addresses": ["retailer1@trustmile.com"],

    "simpleParsingRules": [
        {
            "parsingRule": {
                "in": "body",
                "type": "regex",
                "rule": "L[0-9]{12}"
            },
            "courier": "toll-priority",
            "ruleOrder": 1,
            "pass": False
        }
    ],
    "parsers": [
        {
            "name": "Friendly name of parser",
            "acceptanceRule": {
                "in": "body",
                "type": "regex",
                "rule": "."  # this will match on all
            },
            "parserType": "simple",
            "orderIDParser": {
                "in": "body",
                "type": "regex",
                "rule": "C[0-9]{12}"
            },
            "trackingParsingRules": [
                {
                    "parsingRule": {
                        "in": "body",
                        "type": "regex",
                        "rule": "LL[0-9]{11}"
                    },
                    "courier": None,
                    "ruleOrder": 1,
                    "pass": True
                }
            ]
        }
    ]

}

email_server1 = {
    "imapServer": 'imap.gmail.com',
    "imapPort": '993',
    "imapUsername": 'ri_test@trustmile.com',
    "imapPassword": 'R!_Test#2'
}

account_register = {
    "fullName": "James Bruceton",
    "password": "boundary1234",
    "emailAddress": "this_is_it2@cloudadvantage.com.au",
    "installationInformation": {
        "OSType": "iOS",
        "OSMinorVersion": "1",
        "DeviceIdentifier": "123123123123123123",
        "ApplicationVersion": "0.1",
        "OSMajorVersion": "8"
    }
}

anonymous_account_register = {
    "installationInformation": {
        "OSType": "iOS",
        "OSMinorVersion": "1",
        "DeviceIdentifier": "123123123123123123",
        "ApplicationVersion": "0.1",
        "OSMajorVersion": "8"
    }
}

recipient_email = 'recipient_email@cloudadvantage.com.au'

account_login = {
    "password": "boundary1234",
    "emailAddress": "this_is_it2@cloudadvantage.com.au",
}

neighbour_region_enabled_account_update = {
    "accountAddress": {
        "countryCode": "AU",
        "suburb": "Liverpool",
        "state": "NSW",
        "postcode": "2170",
        "addressLine1": "12 Smith St",
        "addressLine2": "",
        "phoneNumber": "0410 932 980"
    }
}

account_update = {
    "accountAddress": {
        "countryCode": "AU",
        "suburb": "Elizabeth Bay",
        "state": "NSW",
        "postcode": "2011",
        "addressLine1": "801/12 Ithaca Rd",
        "addressLine2": "",
        "phoneNumber": "0410 932 980"
    },
    "fullName": "James Arthurs",
    "trustmileNeighbour": "true",
    "installationInformation": {
        "OSType": "iOS",
        "OSMinorVersion": "1",
        "DeviceIdentifier": "123123123123123123",
        "ApplicationVersion": "0.1",
        "OSMajorVersion": "8"
    },
    'userPreferences': {'values': [{'key': 'courierHonesty', 'value': 'True'},
                                   {'key': 'userLocation', 'value': '-33.8717550,151.2287690'}]}
}

account_update2 = {
    'userPreferences': {'values': [{'key': 'courierHonesty', 'value': 'False'},
                                   {'key': 'userLocation', 'value': '40.7590110,-73.9844720'}]}
}

delivery_feedback = {
    'comment': "test comment",
    'rating': 4,
    "complaint": [
        "Complain1",
        "Complain2"
    ],
}

delivery_feedback_2 = {
    'netPromoterScore': 9
}

location_update = {
    "status": True,
    "location": {
        "latitude": -33.871755,
        "longitude": 151.228769

    }
}

pasword_update = {
    "newPassword": "boundary12345",
    "oldPassword": "boundary1234"
}

courier_user = {
    "username": "courier_0101",
    "password": "password5",
    "fullName": "Rapid Gonzales, Esq.",
    "emailAddress": "RapidGonzales@hisowncouriercompany.com"
}

courier_account_login = {
    "username": "courier_0101",
    "password": "password5"
}

courier_pw_update_bad = {
    "username": "courier_0101",
    "oldPassword": "password5",
    "newPassword": "123123123123"
}

courier_pw_update_ok = {
    "username": "courier_0101",
    "oldPassword": "password5",
    "newPassword": "password123"
}
