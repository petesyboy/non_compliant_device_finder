import json
import optparse
import sys
import time
import os
from typing import Dict, Union

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def get_api_key_path() -> object:
    key_file = '.extrahop'
    path: Union[bytes, str] = os.path.join(os.path.expanduser('~'), key_file)
    return path


def save_api_key(ip, key):
    path = get_api_key_path()
    print('Saving key to {}'.format(path))
    fh = open(path,'r+')


    fh.close()
    return


def check_for_api_key(ip):

    return


def call_extrahop(url, code, data):
    headers = {'Accept': 'application/json',
               'Authorization': 'ExtraHop apikey={}'.format(opts.apikey)}
    fullurl = "https://" + opts.host + "/api/v1/" + url
    # print('Full URL is ' + fullurl)
    if code == 'get':
        response = requests.get(fullurl, headers=headers,
                                timeout=10, verify=False)
    elif code == 'post':
        response = requests.post(fullurl, data=json.dumps(
            data), headers=headers, timeout=10, verify=False)

    if response.status_code != 200:
        response.raise_for_status()
    # Return the response as a JSON object.
    return response.json()


if len(sys.argv) < 3:
    print(
        'Usage: python %s -H Extrahop_IP -O OutputFile <minus extension, csv is added> -D Lookback in days -K apikey') % (
    sys.argv[0])
    sys.exit(1)

# Set up options
p = optparse.OptionParser()
p.add_option('-H', '--host', dest='host', default='extrahop')
p.add_option('-K', '--key', dest='apikey')
p.add_option('-O', '--file', dest='outputfile',
             default='non_compliant_server_names')
p.add_option('-D', '--days', dest='days', default='7')
(opts, argv) = p.parse_args()

if not opts.host:
    print('An IP address for an EDA or ECA must be specified')
    exit(1)

if not opts.apikey:
    check_for_api_key(opts.host)
    print('No API Key specified for device with IP address {}. '.format(str(opts.host)))
    this_api_key = input('Please enter the API key for the specified appliance: ')
    opts.apikey = this_api_key

    api_key_file=get_api_key_path()
    save_key = input('Do you wish to save this key to the default file ({})?'.format(api_key_file))
    if save_key.lower() == "y" or save_key.lower() == 'yes':
        save_api_key(opts.host, this_api_key)


# Name of the csv file we will be writing to....
csvName = opts.outputfile + ".csv"
file = open(csvName, "w")

now = time.strftime("%c")
# date and time representation
nowForFile = time.strftime("%c")
file.write('# Generated from ExtraHop EDA at ' + str(opts.host) +
           '. Non-compliant server names in the last ' + str(opts.days) + ' days as at ' + nowForFile + ".\n")
# Write first line / headers of CSV file.
file.write("device API id, Default Name, IPAddress, Display Name, MAC Address\n")

if __name__ == '__main__':
    daysinMS = int(opts.days) * 86400000
    lookbackTime = 0 - daysinMS

    # Grab the ExtraHop device firmware version as a sanity check.
    versionURL = "extrahop/version"
    extrahop_fw_version = call_extrahop(versionURL, "get", "")
    print('ExtraHop Appliance Version is ' + extrahop_fw_version['version'])

    device_name_check_data: Dict[str, Union[str, int,
                                            Dict[str, Union[str, Dict[str, str]]]]] = {}

    ''' We're looking to build a JSON object like this to POST to the EDA:

    {
        "active_from": "-7d",
        "active_until": 0,
        "filter": {
            "field": "name",
            "operand": {
                "value": "^VMware.*",  <--- Replace this with your regex of choice
                "is_regex": "true"
            },
            "operator": "!="           <--- You might want to change this to "=" or something else
        },
        "limit": 100,                  <--- And this might need updating if you have many non-compliant devices
        "offset": 0
    }

    '''
    operand = {}  # Create the 'operand' JSON object
    operand["value"] = "^VMware"
    operand["is_regex"] = "true"
    filter_details = {}  # Create the 'filter' JSON object
    filter_details["field"] = "name"
    filter_details["operand"] = operand
    filter_details['operator'] = "!="
    device_name_check_data["active_from"] = "-{}d".format((opts.days))
    device_name_check_data["active_until"] = 0
    device_name_check_data["filter"] = filter_details

    device_name_check_data["limit"] = 100
    device_name_check_data["offset"] = 0
    # print(json.dumps(device_name_check_data, indent=2))

    non_compliant_device_name_url = "devices/search"
    non_compliant_device_list = call_extrahop(
        non_compliant_device_name_url, "post", device_name_check_data)

    device: object
    for device in non_compliant_device_list:
        file_line = str(device['id']) + ',' + device['default_name']
        if (device['ipaddr4']):
            file_line += ',' + device['ipaddr4']
        else:
            file_line += ','
        if device['default_name']:
            file_line += ',' + str(device['display_name'])
        else:
            file_line += ','
        if device['macaddr']:
            file_line += ',' + str(device['macaddr'])
        else:
            file_line += ','
        file_line += '\n'
        file.write(file_line)
    file.close()