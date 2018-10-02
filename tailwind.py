import sys
import time
import os
import subprocess
import numpy as np
import json
import argparse

from tools import sysinfo, netscan, diskscan

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
def print_cpu(data, show_cores=True):
    core_list = []

    # Add all available CPU core info
    n_core = 1  # Initial CPU core
    while "CPU Core #{}/Load".format(n_core) in data:  # Iterate over all cores
        core_list.append("CPU Core #{}".format(n_core))
        n_core = n_core + 1

    # Create list of clockspeed sensors
    clock_sensors = ['{}/Clock'.format(core_name) for core_name in core_list]

    # Calculate a package clock 
    clock_package = np.average([data[core] for core in clock_sensors])/1000

    # Print headings
    format_print([
        "Core",
        "Load", 
        "Clock",
        "Temperature",
    ], underline=True)

    # Print package info
    format_print([
        "Package",
        "{:04.1f} %".format(data['CPU Total/Load']), 
        "{:.2f} GHz".format(clock_package),
        "{} C".format(data['CPU Package/Temperature']),
    ])

    if show_cores:
        print('')

        # Print individual cores
        for core_name in core_list:
            format_print([
                core_name[4:],  # Strip "CPU" out of core name
                "{:04.1f} %".format(data['{}/Load'.format(core_name)]), 
                "{:.2f} GHz".format(data['{}/Clock'.format(core_name)]/1000),
                "{} C".format(data['{}/Temperature'.format(core_name)]),
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
        "{:04.1f} %".format(data['GPU Core/Load']), 
        "{} %".format(data['GPU Memory/Load']),
        "{} GHz".format(data['GPU Core/Clock']),
        "{} C".format(data['GPU Core/Temperature']),
    ])

# Print formatted STORAGE stats
def print_storage(data):
    format_print([
        "Drive",
        "Free",
        "Used", 
        "Total",
    ], underline=True)

    for d in data:
        format_print([
            "{}".format(d['device']), 
            "{:.0f} GB".format(d['free']), 
            "{:.0f} GB".format(d['used']), 
            "{:.0f} GB".format(d['total']), 
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
    header_str = 'NameStateCPUUsage(%)MemoryAssigned(M)UptimeStatusVersion'
    error_str = 'Get-VM : You do not have the required permission to complete this task'

    process = subprocess.Popen('powershell.exe Get-VM', stdout=subprocess.PIPE)
    stdout, err = process.communicate()

    if not err:
        out_raw = stdout.decode("utf-8")  # Decode output
        out_lines = [i for i in out_raw.split('\r\n') if i !='']  # Split output by lines
        
        out_lines_nospace = [s.replace(" ", "") for s in out_lines]  # Out lines with all spaces stripped out

        if error_str in out_lines:  # If permissions error
            print("You do not have the required permission to complete this task.")
            return None
        elif not header_str in out_lines_nospace:  # If no header is found
            print("No valid Get-VM header found")
            print(out_lines)
            return None
        else: 
            header_index = out_lines_nospace.index(header_str)  # Get line index of header
            header_line = out_lines[header_index]  # Store header (including spaces) string
            header_vals = header_line.split()  # Store list of header values

            column_indices = [header_line.find(val) for val in header_vals]  # Find start positions of each column
            column_indices.append(-1)  # Add index marking end of line

            data_lines = out_lines[header_index+2:]  # Cut out everything not data

            hosts = []
            for data_line in data_lines:  # For each VM
                d = {}  #  Create empty dictionary
                for i, header in enumerate(header_vals):  # For each column header
                    d[header] = data_line[column_indices[i]:column_indices[i+1]].strip()  # Split by column index, and strip whitespace

                hosts.append(d)  # Add dictionary to list of VM data

            # Start building string
            return_string = ""

            return_string += format_print([
                "Name", 
                "CPU Load",
                "Memory",
                "Uptime",
                #"Version",
                "State",
            ], fmt = "{: <16}", underline=True, rtn = True)

            for host in hosts:
                if host['State'] == 'Running':
                    _status = Fore.GREEN + "Running" + Style.RESET_ALL
                else:
                    _status = Fore.RED + "Offline" + Style.RESET_ALL

                return_string += format_print([
                    "{}".format(host['Name']), 
                    "{:04.1f} %".format(float(host['CPUUsage(%)'])), 
                    "{} MB".format(host['MemoryAssigned(M)']), 
                    "{}".format(host['Uptime'].split(".")[0]), 
                    #"{}".format(host['Version']), 
                    "{}".format(_status),
                ], fmt = "{: <16}", rtn = True)

            return return_string


def print_shot(sys_data, storage_data, hosts_status, vm_status, show_cores=True):
    if sys_data:
        # Print stats
        print("-------CPU------\n")
        print_cpu(sys_data, show_cores=show_cores)

        print("\n-------GPU------\n")
        print_gpu(sys_data)

        print("\n-------MEM------\n")
        print_ram(sys_data)

    if storage_data:
        print("\n-----STORAGE----\n")
        print_storage(storage_data)

    if hosts_status:
        # Print last hosts status
        print("\n------HOSTS-----\n")  
        print(hosts_status)

    if vm_status:
        # Print last VM status
        print("-----HYPERV-----\n")
        if vm_status:
            print(vm_status)
        else:
            print("\nHyper-V not available. Ensure you're running as administrator.")


##### GLOBAL THINGS ######

# Version name
VERSION = "TailwindPS 18.09.30"

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
SERVER_FILE = os.path.join(os.path.dirname(__file__), 'server.json')
SERVER_INFO = json.load(open(SERVER_FILE))
HOSTS = SERVER_INFO['hosts']

# Refresh interval (seconds)
INTERVAL = 1

# Get info or not
GET_HYPERV = True
GET_HOSTS = True
GET_STORAGE = True
SHOW_CORES = True

# Update info every n ticks
UPDATE_HYPERV = 30
UPDATE_HOSTS = 30

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--reload', action='store_true')
    parser.add_argument('-s', '--simple', action='store_true')

    args = parser.parse_args()

    if args.simple:
        GET_HYPERV = False
        GET_HOSTS = False
        GET_STORAGE = False
        SHOW_CORES = False

    try:
        print("Initialising {}...".format(VERSION))
        # Get initial VM status
        if GET_HYPERV:
            vm_counter = 0
            vm_status = vm_str()
        else:
            vm_status = None

        # Get initial hosts status
        if GET_HOSTS:
            hosts_counter = 0
            hosts_status = hosts_str(HOSTS)
        else:
            hosts_status = None
        
        # Get storage data
        if GET_STORAGE:
            storage_data = diskscan.get_all()
        else:
            storage_data = None

        print("Entering TailwindPS...")
        time.sleep(0.2)

        if args.reload:
            while True:
                # Get latest system info
                sys_data = sysinfo.get_all()

                if GET_HOSTS:
                    if hosts_counter < UPDATE_HOSTS:
                        hosts_counter += 1
                    else:
                        # Update VM status
                        hosts_status = hosts_str(HOSTS)
                        hosts_counter = 0

                if GET_HYPERV:
                    if vm_counter < UPDATE_HYPERV:
                        vm_counter += 1
                    else:
                        # Update VM status
                        vm_status = vm_str()
                        vm_counter = 0

                # Print output
                cls()
                print("{}\n".format(VERSION))
                print_shot(sys_data, storage_data, hosts_status, vm_status, show_cores=SHOW_CORES)

                # Pause
                time.sleep(INTERVAL)
        else:
            # Get latest system info
            sys_data = sysinfo.get_all()
            print_shot(sys_data, storage_data, hosts_status, vm_status, show_cores=SHOW_CORES)

    except KeyboardInterrupt:
        pass