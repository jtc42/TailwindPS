import sys
import time
import os
import subprocess
import numpy as np
import json

from tools import sysinfo
from tools import netscan
 
from colorama import init, Fore, Back, Style

init()  # Colorama init

# Clear screen
def cls():
    os.system('cls' if os.name=='nt' else 'clear')


# Print, or return string, with formatted spacing/padding
def format_print(items, fmt = "{: <12}", underline=False, rtn = False):
    base_str = ""
    rtn_string = ""
    for i, string in enumerate(items):
        base_str += fmt

    if rtn:
        rtn_string += base_str.format(*items) + "\n"
    else:
        print(base_str.format(*items))

    if underline:
        items_underline = items
        for i, string in enumerate(items_underline):
            items_underline[i] = '-' * len(string)

        if rtn:
            rtn_string += base_str.format(*items_underline) + "\n"
        else:
            print(base_str.format(*items_underline))
    
    if rtn:
        return rtn_string


# Print formatted RAM stats
def print_ram(data):
    format_print([
        "Load",
        "Used", 
        "Total",
    ], underline=True)

    format_print([
        "{:0>4} % ".format(round(data['Used Memory/Data']/(data['Used Memory/Data']+data['Available Memory/Data'])*100, 1)),
        "{} GB".format(data['Used Memory/Data']), 
        "{} GB".format(round(data['Used Memory/Data']+data['Available Memory/Data'], 2)),
    ])


# Print formatted CPU stats
def print_cpu(data):
    clock_sensors = [
        'CPU Core #1/Clock',
        'CPU Core #2/Clock',
        'CPU Core #3/Clock',
        'CPU Core #4/Clock',
    ]

    clocks = [data[core] for core in clock_sensors]
    clock_package = round(np.average(clocks)/1000, 2)

    format_print([
        "Load", 
        "Clock",
        "Temperature",
    ], underline=True)

    format_print([
        "{:0>4} %".format(round(data['CPU Total/Load'], 1)), 
        "{} GHz".format(clock_package),
        "{} C".format(data['CPU Package/Temperature']),
    ])


# Print formatted GPU stats
def print_gpu(data):

    format_print([
        "Load", 
        "VRAM",
        "Clock",
        "Temperature",
    ], underline=True)

    format_print([
        "{:0>4} %".format(data['GPU Core/Load']), 
        "{} %".format(data['GPU Memory/Load']),
        "{} GHz".format(data['GPU Core/Clock']),
        "{} C".format(data['GPU Core/Temperature']),
    ])


# Get formatted string of host stats
def hosts_str(host_list):
    hosts = netscan.online_dict(host_list)

    return_string = ""

    return_string += format_print([
        "Name", 
        "URL",
        "Status",
    ], fmt = "{: <32}", underline=True, rtn = True)

    for host in hosts:
        if host['online']:
            _status = Fore.GREEN + "Online" + Style.RESET_ALL
        else:
            _status = Fore.RED + "Offline" + Style.RESET_ALL

        return_string += format_print([
            "{}".format(host['name']), 
            "{}".format(host['url']),
            "{}".format(_status),
        ], fmt = "{: <32}", rtn = True)

    return return_string


# Get formatted string of Hyper-V stats
def vm_str():
    process = subprocess.Popen('powershell.exe Get-VM', stdout=subprocess.PIPE, shell=True)
    stdout, err = process.communicate()

    if not err:
        # Check for permission error
        check_str = 'Get-VM : You do not have the required permission to complete this task'
        if stdout.decode("utf-8").split('.')[0] != check_str:
            return stdout.decode("utf-8")


##### GLOBAL THINGS ######

# List of OHM sensors to grab
SENSORS = [
    'CPU Total/Load', 
    'CPU Package/Temperature', 
    'CPU Core #1/Clock',
    'CPU Core #2/Clock',
    'CPU Core #3/Clock',
    'CPU Core #4/Clock',

    'GPU Core/Load', 
    'GPU Core/Clock',
    'GPU Memory/Load',
    'GPU Core/Temperature', 

    'Used Memory/Data',
    'Available Memory/Data',
]

# Load json options
SERVER_INFO = json.load(open('server.json'))
HOSTS = SERVER_INFO['hosts']

# Refresh interval (seconds)
INTERVAL = 1

# Get info or not
GET_HYPERV = True
GET_HOSTS = True

# Update info every n ticks
UPDATE_HYPERV = 30
UPDATE_HOSTS = 30

if __name__ == '__main__':
    try:
        # Get VM status
        if GET_HYPERV:
            vm_counter = 0
            vm_status = vm_str()

        if GET_HOSTS:
            hosts_counter = 0
            hosts_status = hosts_str(HOSTS)

        while True:
            # Get latest system info
            all_data = sysinfo.get_all()

            # Clear console
            cls()

            if all_data:
                # Print stats
                print("\n-------CPU------\n")
                print_cpu(all_data)

                print("\n-------GPU------\n")
                print_gpu(all_data)

                print("\n-------MEM------\n")
                print_ram(all_data)

            if GET_HOSTS:
                # Print last hosts status
                print("\n------HOSTS-----\n")  
                print(hosts_status)

                if hosts_counter < UPDATE_HOSTS:
                    hosts_counter += 1
                else:
                    # Update VM status
                    hosts_status = hosts_str(HOSTS)
                    hosts_counter = 0

            if GET_HYPERV:
                
                # Print last VM status
                print("\n-----HYPERV-----")
                if vm_status:
                    print(vm_status)
                else:
                    print("Hyper-V not available. Ensure you're running as administrator.")

                if vm_counter < UPDATE_HYPERV:
                    vm_counter += 1
                else:
                    # Update VM status
                    vm_status = vm_str()
                    vm_counter = 0

            time.sleep(INTERVAL)

    except KeyboardInterrupt:
        pass