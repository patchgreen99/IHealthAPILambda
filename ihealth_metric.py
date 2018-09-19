import boto3, botocore, urllib2, json, urllib
from datetime import datetime, date, time, timedelta

DATE_FORMAT_IHEALTH = '%Y%m%d'
DATE_FORMAT_FITSENSE = '%Y%m%d'

IHEALTH_METRICS = {
    'blood_pressure': {'api': 'bp.json', 'acronym': 'BP', 'values': ['HP', 'LP']},
    'blood_glucose': {'api': 'glucose.json', 'acronym': 'BG', 'values': ['BG']}
}

IHEALTH_LOCALE = 'en_UK'

# compulsary keys in payload: user_id (string), metric (string), period (int, in days)
# expects respective values to be validated
def lambda_handler(event, context):
    user_id = event['user_id']
    metric = event['metric']
    period = event['period']

    # retrieve credentials from database
    dynamodb = boto3.resource('dynamodb')
    data_sources_table = dynamodb.Table('data_sources')
    try:
        data_sources_entry = data_sources_table.get_item(Key={'user_id': user_id})
    except botocore.exceptions.ClientError as e:
        return error(503, e.response['Error']['Message'])
    if 'ihealth' not in data_sources_entry['Item']:
        return error(400, 'User has no credentials for ihealth')
    credentials = data_sources_entry['Item']['ihealth']

    dataset = retrieveMetricFromIHealthAPI(metric, period, credentials)
    return dataset


# contact ihealth API to retrieve dataset for requested metric and period
def retrieveMetricFromIHealthAPI(metric, period, credentials):
    start_date_ihealth = date.today().strftime(DATE_FORMAT_IHEALTH)
    end_date_ihealth = (date.today() - timedelta(period)).strftime(DATE_FORMAT_IHEALTH)

    params = {
        'Client_id': credentials['Client_id'],
        'client_secret': credentials['client_secret'],
        'access_token': credentials['access_token'],
        'sc': credentials['sc'],
        'sv': credentials['sv'],
        'start_time': start_date_ihealth,
        'end_time': end_date_ihealth,
        'locale': IHEALTH_LOCALE
    }

    url = 'https://api.ihealthlabs.com:8443/openapiv2/application/' + \
          IHEALTH_METRICS[metric]['api'] + '?' + urllib.urlencode(params)

    request = urllib2.Request(url)
    try:
        response = urllib2.urlopen(request)
    except urllib2.URLError as e:
        response = json.loads(e.read())
        return error(e.code, response['errors'][0]['message'])
    response = json.loads(response.read())
    if 'errors' in response:
        return error(503, response['errors'][0]['message'])

    dataset = {}

    timeserieskey = IHEALTH_METRICS[metric]['acronym'] + 'DataList'
    unitkey = IHEALTH_METRICS[metric]['acronym'] + 'Unit'
    records = response[timeserieskey]

    for record in records:
        current_date_fitsense = convertToFitSenseDateFormat(record['MDate'], record['TimeZone'])

        dataset[current_date_fitsense] = {'unit': record[unitkey]}
        for value in IHEALTH_METRICS['values']:
            dataset[current_date_fitsense][value] = record[value]
    return dataset


def convertToFitSenseDateFormat(unix_timestamp, timezone):
    # timezone format is -0600 (minus 6 hours) so it needs applying to the unixtimestamp
    timestamp = int(unix_timestamp) + int(timezone[:3]) * 60 * 60 + int(timezone[0]+timezone[-2:]) * 60
    date_object = datetime.fromtimestamp(timestamp).date()
    fitsense_date_string = date_object.strftime(DATE_FORMAT_FITSENSE)
    return fitsense_date_string


def error(code, message):
    return {
        'error': {
            'code': code,
            'message': message
        }
    }