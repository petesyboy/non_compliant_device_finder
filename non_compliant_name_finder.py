__author__ = 'Pete Connolly (pconnolly@extrahop.com)'
import argparse
import json
import os
import time
from pprint import pprint
from typing import Dict, Union

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def get_api_key_path():
    key_file = '.extrahop'
    path: Union[bytes, str] = os.path.join(os.path.expanduser('~'), key_file)
    if options.verbose:
        print(f'Working with key file at {path}')

    return path


def read_api_key_file():
    path = get_api_key_path()
    create_key_file_if_needed()
    key_dict = {}
    with open(path, 'r+') as fh:
        for line in fh:
            (this_ip, key) = line.split()
            key_dict[this_ip] = key
    return key_dict


def add_api_key_to_file(ip, key):
    path = get_api_key_path()
    create_key_file_if_needed()
    print(f'Saving key to {path}')
    key_dict = read_api_key_file()
    key_dict[ip] = key
    with open(path, 'w') as fh:
        for this_ip, this_key in key_dict.items():
            fh.write(str(this_ip) + ' ' + str(this_key) + '\n')
    return


def check_file_for_api_key(ip):
    path = get_api_key_path()
    create_key_file_if_needed()
    key_dict = {}
    with open(path, 'r+') as fh:
        for line in fh:
            (this_ip, key) = line.split()
            key_dict[this_ip] = key

    if ip in key_dict:
        return key_dict[ip]
    else:
        return 3


def create_key_file_if_needed():
    path = get_api_key_path()
    exists = os.path.isfile(path)
    if not exists:
        fh = open(path, 'w+')
        fh.close()
    # chmod(path, 0x755)
    return


def get_version_and_platform(ip):
    # Grab the ExtraHop device platform and firmware version.
    platform_url = "extrahop/"
    extrahop_platform = call_extrahop(platform_url, "get", "")
    eh_platform = extrahop_platform['platform']
    firmware = extrahop_platform['version']
    if eh_platform == 'extrahop':
        this_platform = 'EDA'
    else:
        this_platform = eh_platform
    if options.verbose:
        print(f'ExtraHop Appliance at {ip} is an {this_platform} and the firmware version is {firmware}')
    return this_platform, firmware


def get_options():
    parser = argparse.ArgumentParser(description='Usage: %prog [options]')
    parser.add_argument('-H', '--host',
                        required=True,
                        default='extrahop',
                        help='IP or hostname of ExtraHop appliance')
    parser.add_argument('-a', '--apikey',
                        required=False,
                        help='API token obtained from the ExtraHop system')
    parser.add_argument('-o', '--outputfile',
                        required=False,
                        default='non_compliant_server_names',
                        help='Name of the file to save the results to')
    parser.add_argument('-d', '--days',
                        required=False,
                        default='7',
                        type=int,
                        help='Number of days of lookback history to search')
    parser.add_argument('-r', '--regex',
                        required=False,
                        default='^ASUS',
                        help='The RegEx pattern to use in the device name search')
    parser.add_argument('-i', '--ipaddr',
                        required=False,
                        help='Only include devices with an IP address(L3)')  ## TODO - Implement the L3 only search
    group = parser.add_mutually_exclusive_group()  # Need to check the syntax for the API call
    group.add_argument('-v', '--verbose', action='store_true')  # and move the filter toa 'rule' section
    group.add_argument('-q', '--quiet', action='store_true')

    options = parser.parse_args()
    return options


def call_extrahop(url, code, data):
    if not options.apikey:
        print('No API key available in call_extrahop(). Exiting')
        exit(2)

    headers = {'Accept': 'application/json',
               'Authorization': 'ExtraHop apikey={}'.format(options.apikey)}
    fullurl = "https://" + options.host + "/api/v1/" + url
    if options.verbose:
        print(f'Sending a {code} request to {fullurl} with the headers {headers}')

    if code == 'get':
        response = requests.get(fullurl, headers=headers,
                                timeout=10, verify=False)
    elif code == 'post':
        if options.verbose:
            pprint(data)
        response = requests.post(fullurl, data=json.dumps(
            data), headers=headers, timeout=10, verify=False)

    if response.status_code != 200:
        # response.raise_for_status()
        if response.status_code == 401:
            print(
                f'The API returned an unauthorised /missing API key error {response.status_code}. ' \
                    f'Please check your API key')

        elif response.status_code == 402:
            print(
                f'The EULA has not been accepted for this appliance (status {response.status_code}. ' \
                    f'Please browse to https://{options.host}/admin to accept the EULA')

        elif response.status_code == 404:
            print(
                f'The requested resource could not be found. Are you specifying the right object ID? ' \
                    f'(device/appliance/alert/detection etc). {response.status_code}')

        elif response.status_code == 403:
            print(f'The current user has insufficient privileges to perform that operation. {response.status_code}')

        elif response.status_code == 422:
            print(f'Partial update or ticketing is disabled {response.status_code}')

        elif response.status_code >= 500:
            print(f'Internal Server Error. {response.status_code}')

    # Return the response as a JSON object.
    return response.json()


options = get_options()
if not options.host:
    parser.error('Incorrect number of arguments. Specify an ExtraHop appliance IP or hostname as a minimum, '
                 'or specify "-h" for all options')

if not options.apikey:
    this_api_key = check_file_for_api_key(options.host)
    if this_api_key != 3:
        if options.verbose:
            print('Found API key in key file')
        options.apikey = this_api_key
    else:
        print(f'No key found in file and no API Key specified for device with IP address {str(options.host)}. ')
        this_api_key = input('Please enter the API key for the specified appliance: ')
        options.apikey = this_api_key

        api_key_file = get_api_key_path()
        save_key = input(f'Do you wish to save this key to the default file ({api_key_file})?')
        if save_key.lower() == "y" or save_key.lower() == 'yes':
            add_api_key_to_file(options.host, this_api_key)

# Name of the csv file we will be writing to....
csvName = options.outputfile + ".csv"
file = open(csvName, "w")

now = time.strftime("%c")
# date and time representation
now_for_file = time.strftime("%c")
header_info_line = '# Generated from ExtraHop EDA at {}. Non-compliant server names in the last {} days as at {}.\n'.format(
    str(options.host), str(options.days), now_for_file)
file.write(header_info_line)
# Write headers of CSV file.
file.write("device API id, Default Name, IPAddress, Display Name, MAC Address\n")

platform, version = get_version_and_platform(options.host)

if __name__ == '__main__':
    daysinMS = int(options.days) * 86400000
    lookback_time = 0 - daysinMS

    device_name_check_data: Dict[str, Union[str, int,
                                            Dict[str, Union[str, Dict[str, str]]]]] = {}

    ''' We're looking to build a JSON object like this to POST to the EDA:

    {
        "active_from": "-7d",          <- 'From' when. Easiest to use the d,w,m format see the REST API for full details)
        "active_until": 0,             <- 0 = Now
        "filter": {
            "field": "name",
            "operand": {
                "value": "^VMware",    <- Replace this with your regex of choice
                "is_regex": "true"
            },
            "operator": "!="           <- You might want to change this to "=" or something else
        },
        "limit": 100,                  <- And this might need updating if you have many non-compliant devices
        "offset": 0                    <- Or you can paginate through results with a cursor-like workflow 
    }

    '''
    operand = {}  # Create the 'operand' JSON object
    if options.regex:
        operand["value"] = options.regex
    else:
        operand["value"] = "^ASUS"

    operand["is_regex"] = "true"
    filter_details = {}  # Create the 'filter' JSON object
    filter_details["field"] = "name"
    filter_details["operand"] = operand
    filter_details['operator'] = "!="
    device_name_check_data["active_from"] = "-{}d".format((options.days))
    device_name_check_data["active_until"] = 0
    device_name_check_data["filter"] = filter_details

    device_name_check_data["limit"] = 100
    device_name_check_data["offset"] = 0
    if options.verbose:
        print('Filter constructed for name check:')
        print(json.dumps(device_name_check_data, indent=2))

    non_compliant_device_name_url = "devices/search"
    non_compliant_device_list = call_extrahop(
        non_compliant_device_name_url, "post", device_name_check_data)

    device: object
    cnt = 0
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
        cnt += 1
    print(f'Wrote a total of {cnt} device detail lines to file')
    file.close()
