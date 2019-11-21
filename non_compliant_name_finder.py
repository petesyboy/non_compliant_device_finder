__author__ = 'Pete Connolly (pconnolly@extrahop.com)'
# non_compliant_name_finder.py version 1.0

import json
import time

import ehoplib as eh

options = eh.get_options()
if not options.host:
    parser.error('Incorrect number of arguments. Specify an ExtraHop appliance IP or hostname as a minimum, '
                 'or specify "-h" for help on all options')

if not options.apikey:
    this_api_key = eh.check_file_for_api_key(options.host)
    if this_api_key != 3:
        if options.verbose:
            print(f'Found API key in key file for appliance at {options.host}')
        options.apikey = this_api_key
    else:
        print(f'No key found in file and no API Key specified for device with IP address {str(options.host)}. ')
        this_api_key = input('Please enter the API key for the specified appliance: ')
        options.apikey = this_api_key

        api_key_file = eh.get_api_key_path()
        save_key = input(f'Do you wish to save this key to the default file ({api_key_file})?')
        if save_key.lower() == "y" or save_key.lower() == 'yes':
            eh.add_api_key_to_file(options.host, this_api_key)

# Name of the csv file we will be writing to....
csvName = options.outputfile + ".csv"
file = open(csvName, "w")

now = time.strftime("%c")
# date and time representation
now_for_file = time.strftime("%c")
header_info_line = '# Generated from ExtraHop EDA at {}. Non-compliant device names in the last {} days as at {}.\n'.format(
    str(options.host), str(options.days), now_for_file)
file.write(header_info_line)
# Write headers of CSV file.
file.write("device API id, Default Name, IPAddress, Display Name, MAC Address\n")

platform, version = eh.get_version_and_platform(options.host, options.apikey, options.verbose)

if __name__ == '__main__':
    daysinMS = int(options.days) * 86400000
    lookback_time = 0 - daysinMS
    if options.verbose:
        print(f'Setting lookback to {options.days} ({daysinMS}ms)')

    device_name_check_data = {}

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
        operand["value"] = "^VMware"

    operand["is_regex"] = "true"
    filter_details = {}  # Create the 'filter' JSON object
    filter_details["field"] = "name"
    filter_details["operand"] = operand
    filter_details['operator'] = "!="
    device_name_check_data["active_from"] = "-{}".format((daysinMS))
    device_name_check_data["active_until"] = 0
    device_name_check_data["filter"] = filter_details

    device_name_check_data["limit"] = options.limit
    device_name_check_data["offset"] = options.offset
    if options.verbose:
        print('Filter constructed for name check:')
        print(json.dumps(device_name_check_data, indent=2))

    # def call_extrahop(host, url, code, apikey, verbose, data):
    non_compliant_device_name_url = "devices/search"
    non_compliant_device_list = eh.call_extrahop(options.host,
                                                 non_compliant_device_name_url, "post", options.apikey, options.verbose,
                                                 device_name_check_data)

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
