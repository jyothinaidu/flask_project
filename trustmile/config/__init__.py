__author__ = 'james'
import yaml
import os
import re



logging_config = None
SECRET_WORDS = None
dir = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(dir , 'config.yml')) as f:
    yml_config = yaml.load(f)
    from logging import config as logging_config
    logging_config.dictConfig(yml_config)

with open(os.path.join(dir, 'secret_words.txt')) as f1:
    SECRET_WORDS = f1.read().splitlines()


ENV_TYPE = os.environ.get('TRUSTMILE_ENV_TYPE') or yml_config['env_type']


# Flask Config
SQLALCHEMY_DATABASE_URI = yml_config['db'][ENV_TYPE]['sqlalchemy']['url']
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Mandrill/Email
EMAIL_API_KEY = yml_config['mandrill']['api_key'][ENV_TYPE]


# Geocoding Keys
GOOGLE_LOCATION_KEY = yml_config['google']['api_key'][ENV_TYPE]

# Flask
FLASK_CLIENT_CONFIG = yml_config['flask']['client']['environ'][ENV_TYPE]

AFTERSHIP_API_KEY = yml_config['aftership']['api_key'][ENV_TYPE]
AFTERSHIP_COURIER_FILE = yml_config['aftership']['courier_data']
COURIER_IMAGE_URL_BASE = yml_config['assets']['image_url_base']
RETAILER_IMAGE_URL_BASE = yml_config['assets']['retailer_image_url_base']

PUSHWOOSH_APPLICATION = yml_config['pushwoosh'][ENV_TYPE]['application']
PUSHWOOSH_AUTH = yml_config['pushwoosh'][ENV_TYPE]['auth']

EMAILADDRESSES_FEEDBACK = yml_config['emailAddresses'][ENV_TYPE]['feedback']

DEFAULT_RADIUS = yml_config['location']['default_radius']

EMAIL_VERIFY_URL = yml_config['email']['verification_url'][ENV_TYPE]
PASSWORD_RESET_URL = yml_config['email']['reset_url'][ENV_TYPE]
RETAILER_PASSWORD_RESET_URL = yml_config['email']['retailer_reset_url'][ENV_TYPE]


DEEPLINK_SCHEME = yml_config['deep_link_scheme'][ENV_TYPE]

BRANCH_KEY = yml_config['branch'][ENV_TYPE]['branch_key']
BRANCH_URL = yml_config['branch'][ENV_TYPE]['base_url']

#retailer integration stuff
RI_IMAP_SERVER = yml_config['retailerIntegration'][ENV_TYPE]['imapServer']
RI_IMAP_PORT = yml_config['retailerIntegration'][ENV_TYPE]['imapPort']
RI_IMAP_USERNAME = yml_config['retailerIntegration'][ENV_TYPE]['imapUsername']
RI_IMAP_PASSWORD = yml_config['retailerIntegration'][ENV_TYPE]['imapPassword']

#admin api
ADMIN_API_KEY = yml_config['adminAPI'][ENV_TYPE]['apiKey']

COURIERS_PLEASE_FTP_HOST = yml_config['couriersPlease']['ftpHost']
COURIERS_PLEASE_FTP_USER = yml_config['couriersPlease']['ftpUser']
COURIERS_PLEASE_FTP_PASS = yml_config['couriersPlease']['ftpPass']
COURIERS_PLEASE_FTP_DIR = yml_config['couriersPlease']['ftpDir']
COURIERS_PLEASE_CONTRACTOR_NUM = yml_config['couriersPlease']['contractorNum']


ARCHIVE_DAYS = int(yml_config['archive_days'])

TM_TRACKING_URL = yml_config['tm_tracking_url'][ENV_TYPE]

REDIS_URL = yml_config['redis_url'][ENV_TYPE]

ENABLED_POSTCODES = [str(pc) for pc in yml_config['enabled_postcodes'][ENV_TYPE]]

m = re.match('redis:\/\/((\S+\.?)+):(\d+)\/(\w+)', REDIS_URL)

REDIS_HOST = m.group(1)
REDIS_PORT = m.group(3)
REDIS_DB = m.group(4)
#
# promotion_s3_access_key: 'AKIAIO23HYHLMMJYDW2Q'
# promotion_s3_secret_access_key: '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'
# region: 'ap-southeast-2'
# promotion_bucket: 'assets.trustmile.com'
# promotion_image_prefix: '/images/promotion'


AWS_S3_ACCESS_KEY = yml_config['s3']['promotion_s3_access_key']

AWS_S3_SECRET_ACCESS_KEY = yml_config['s3']['promotion_s3_secret_access_key']
PROMOTION_BUCKET_NAME = yml_config['s3']['promotion_bucket']
PROMOTION_S3_STORE_PREFIX = yml_config['s3']['promotion_image_prefix']
AWS_REGION = yml_config['s3']['region']