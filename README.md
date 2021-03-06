# non_compliant_device_finder.py

A script to let you query an ExtraHop EDA/Reveal(x) EDA to find devices who's names don't match a particular regex.
This can be as simple as a 'starts with' regex like '^VMware' or as complex as your naming standards require. The idea is
that you can run the script via a cron job, either specifying the API token on the command line or you can have it saved 
to a file in the user's home directory (.extrahop). This will then allow you to call the script with only a single 
parameter (the IP address or name of the ExtraHop Explore Appliance) and have it output a CSV file with all the non-compliant 
device names for further processing.

For full usage information, run the script with the -h option. As at version 1.0, the output looks like this:

```E:\deviceRenamer\Scripts\python.exe "E:/Python Projects/non_compliant_device_names/non_compliant_name_finder.py"
usage: non_compliant_name_finder.py [-h] -H HOST [-a APIKEY] [-o OUTPUTFILE]
                                    [-d DAYS] [-r REGEX] [-l LIMIT]
                                    [-O OFFSET] [-v | -q]

Usage: non_compliant_name_finder.py [options]

optional arguments:

  -h, --help show this help message and exit
  -H HOST, --host HOST  IP or hostname of ExtraHop appliance
  -a APIKEY, --apikey APIKEY API token obtained from the ExtraHop system
  -o OUTPUTFILE, --outputfile OUTPUTFILE Name of the file to save the results to (default:
                        non_compliant_server_names)
  -d DAYS, --days DAYS  Number of days of lookback history to search (default: 7 days)
  -r REGEX, --regex REGEX The RegEx pattern to use in the device name search (default "^VMware")
  -l LIMIT, --limit LIMIT Limit the number of results (for pagination) (default: 100)
  -O OFFSET, --offset OFFSET Offset to search from (for pagination - use with the
                        -l/--limit switch (default: 0)
  -v, --verbose
  -q, --quiet

Example: python3 non_compliant_name_finder.py -H 192.168.0.16 -v -o devices -r^ASUS -O100 -l100
```
To save the API token to the .extrahop file, just specify the ExtraHop EDA IP address or name on the command line, 
supply the token when prompted then select 'y' or 'yes' when asked if you want to save this. The next invocation of 
the script will search for the IP or hostname in the file and run without interaction.

Any suggestions, please email peteconnolly1@gmail.com
