__author__ = 'Pete Connolly (peteconnolly1@gmail.com)'
# ehoplib.py version 0.1

import argparse
import json
import os
import sys
from pprint import pprint

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Disable the warning for the default self-signed certificate (I know, I know)
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


def get_version_and_platform(ip, apikey, verbose):
    # Grab the ExtraHop device platform and firmware version.
    platform_url = "extrahop/"
    extrahop_platform = call_extrahop(ip, platform_url, "get", apikey, verbose, "")
    eh_platform = extrahop_platform['platform']
    firmware = extrahop_platform['version']
    if eh_platform == 'extrahop':
        this_platform = 'EDA'
    else:
        this_platform = eh_platform
    if verbose:
        print(f'ExtraHop Appliance at {ip} is an {this_platform} and the firmware version is {firmware}')
    return this_platform, firmware


def get_options():
    parser = argparse.ArgumentParser(description=f'Usage: %(prog)s [options]',
                                     epilog='Example: python3 %(prog)s -H 192.168.0.16 -v -o devices -r ^ASUS -O 100 -l 100')
    parser.add_argument('-H', '--host',
                        required=True,
                        default='extrahop',
                        help='IP or hostname of ExtraHop appliance')
    parser.add_argument('-a', '--apikey',
                        required=False,
                        help='API token obtained from the ExtraHop system')
    parser.add_argument('-o', '--outputfile',
                        required=False,
                        default='non_compliant_device_names',
                        help='Name of the file to save the results to (default: non_compliant_device_names)')
    parser.add_argument('-d', '--days',
                        required=False,
                        default='7',
                        type=int,
                        help='Number of days of lookback history to search (default: 7 days)')
    parser.add_argument('-r', '--regex',
                        required=False,
                        default='^VMware',
                        help='The RegEx pattern to use in the device name search (default "^VMware"')
    #    parser.add_argument('-i', '--ipaddr',
    #                        required=False,
    #                        help='Only include devices with an IP address(L3)')  ## TODO - Implement the L3 only search
    parser.add_argument('-l', '--limit',
                        required=False,
                        default=100,
                        type=int,
                        help='Limit the number of results (for pagination) (default: 100)')
    parser.add_argument('-O', '--offset',
                        required=False,
                        type=int,
                        default=0,
                        help='Offset to search from (for pagination - use with the -l/--limit switch (default: 0)')
    group = parser.add_mutually_exclusive_group()  # Need to check the syntax for the API call
    group.add_argument('-v', '--verbose', action='store_true')  # and move the filter to a 'rule' section
    group.add_argument('-q', '--quiet', action='store_true')
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    options = parser.parse_args()
    return options


def call_extrahop(host, url, code, apikey, verbose, data):
    if not apikey:
        print('No API key available in call_extrahop(). Exiting')
        exit(2)

    if not host:
        print('No host specified in call_extrahop(). Exiting')
        exit(2)

    headers = {'Accept': 'application/json',
               'Authorization': 'ExtraHop apikey={}'.format(apikey)}
    fullurl = "https://" + host + "/api/v1/" + url
    if verbose:
        print(f'Sending a {code} request to {fullurl} with the headers {headers}')

    if code == 'get':
        response = requests.get(fullurl, headers=headers,
                                timeout=10, verify=False)
    elif code == 'post':
        if verbose:
            pprint(data)
        response = requests.post(fullurl, data=json.dumps(
            data), headers=headers, timeout=10, verify=False)

    if response.status_code != 200:
        # response.raise_for_status()
        if response.status_code == 401:
            path = get_api_key_path()
            print(
                f'The API returned an unauthorised / missing API key error {response.status_code}. ' \
                f'Please check your API key in the file {path}')

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
