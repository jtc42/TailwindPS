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
    
# Print header format
def hdrprint(msg, length=28, char="-", col=Fore.CYAN, style=Style.BRIGHT):
    print(col + style + '{0:{char}^{length}}'.format(msg, length=length, char=char) + Style.RESET_ALL)
    
# Print string with a fixed width buffer, for overwriting stdout lines
def padprint(msg, len=50):
    print(msg.ljust(50), end='\r')  # Print loading line

# Overwrite previous padprint with empty space, to avoid mashing if next print is shorter
def padflush(len=50):
    padprint("", len=len)
    
# Just print without a newline
def nprint(msg):
    print(msg, end="")

# Print, or return string, with formatted spacing/padding
def format_cols(items, fmt = "{: <12}", underline=False):
    base_str = ""
    rtn_string = ""

    for i, string in enumerate(items):
        base_str += fmt

    rtn_string += base_str.format(*items)

    if underline:
        rtn_string += "\n"
        items_underline = items
        for i, string in enumerate(items_underline):
            items_underline[i] = '-' * len(string)

        rtn_string += base_str.format(*items_underline) + "\n"

    return rtn_string

# Print formatted RAM stats
def mem_str(data):
    return_string = ""
    return_string += format_cols([
        "Load",
        "Used", 
        "Total",
    ], underline=True)

    return_string += format_cols([
        "{:0>4} % ".format(round(data['Used Memory/Data']/(data['Used Memory/Data']+data['Available Memory/Data'])*100, 1)),
        "{} GB".format(data['Used Memory/Data']), 
        "{} GB".format(round(data['Used Memory/Data']+data['Available Memory/Data'], 2)),
    ])
    return_string += "\n"
    return return_string

# Print formatted CPU stats
def cpu_str(data, show_cores=True):
    return_string = ""

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
    return_string += format_cols([
        "Core",
        "Load", 
        "Clock",
        "Temperature",
    ], underline=True)

    # Print package info
    return_string += format_cols([
        "Package",
        "{:04.1f} %".format(data['CPU Total/Load']), 
        "{:.2f} GHz".format(clock_package),
        "{} C".format(data['CPU Package/Temperature']),
    ])

    if show_cores:
        return_string += "\n"

        # Print individual cores
        for core_name in core_list:
            return_string += format_cols([
                core_name[4:],  # Strip "CPU" out of core name
                "{:04.1f} %".format(data['{}/Load'.format(core_name)]), 
                "{:.2f} GHz".format(data['{}/Clock'.format(core_name)]/1000),
                "{} C".format(data['{}/Temperature'.format(core_name)]),
            ])
            return_string += "\n"

    return return_string

# Print formatted GPU stats
def gpu_str(data):
    return_string = ""
    return_string += format_cols([
        "Load", 
        "VRAM",
        "Clock",
        "Temperature",
    ], underline=True)

    return_string += format_cols([
        "{:04.1f} %".format(data['GPU Core/Load']), 
        "{} %".format(data['GPU Memory/Load']),
        "{} GHz".format(data['GPU Core/Clock']),
        "{} C".format(data['GPU Core/Temperature']),
    ])
    return_string += "\n"
    return return_string

# Print formatted STORAGE stats
def storage_str(data):
    return_string = ""

    return_string += format_cols([
        "Drive",
        "Free",
        "Used", 
        "Total",
    ], underline=True)

    for d in data:
        return_string += format_cols([
            "{}".format(d['device']), 
            "{:.0f} GB".format(d['free']), 
            "{:.0f} GB".format(d['used']), 
            "{:.0f} GB".format(d['total']), 
        ])
        return_string += "\n"
    return return_string

# Get formatted string of host stats
def hosts_str(host_list):
    hosts = netscan.online_dict(host_list)

    return_string = ""

    return_string += format_cols([
        "Name", 
        "URL",
        "Status",
    ], fmt = "{: <32}", underline=True)

    for host in hosts:
        if host['online']:
            _status = Fore.GREEN + "Online" + Fore.RESET
        else:
            _status = Fore.RED + "Offline" + Fore.RESET

        return_string += format_cols([
            "{}".format(host['name']), 
            "{}".format(host['url']),
            "{}".format(_status),
        ], fmt = "{: <32}")
        return_string += "\n"
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

            return_string += format_cols([
                "Name", 
                "CPU Load",
                "Memory",
                "Uptime",
                "State",
            ], fmt = "{: <16}", underline=True)

            for host in hosts:
                # Format online status
                if host['State'] == 'Running':
                    _status = Fore.GREEN + "Running" + Fore.RESET
                else:
                    _status = Fore.RED + "Offline" + Fore.RESET

                # Create uptime string
                uptime_arr = host['Uptime'].split(".")
                if len(uptime_arr) == 1 or len(uptime_arr) == 2:
                    uptime = uptime_arr[0]
                elif len(uptime_arr) == 3:
                    uptime = "{}d {}".format(*uptime_arr[:2])
                
                return_string += format_cols([
                    "{}".format(host['Name']), 
                    "{:04.1f} %".format(float(host['CPUUsage(%)'])), 
                    "{} MB".format(host['MemoryAssigned(M)']), 
                    "{}".format(uptime),  
                    "{}".format(_status),
                ], fmt = "{: <16}")
                return_string += "\n"

            return return_string


def print_shot(sys_data, storage_status, hosts_status, vm_status, show_cores=True):
    if sys_data:
        # Print stats
        hdrprint("CPU")
        nprint(cpu_str(sys_data, show_cores=show_cores))

        hdrprint("GPU")
        nprint(gpu_str(sys_data))

        hdrprint("MEM")
        nprint(mem_str(sys_data))

    if storage_status:
        hdrprint("DRV")
        nprint(storage_status)

    if hosts_status:
        # Print last hosts status
        hdrprint("SVR")
        nprint(hosts_status)  # Use 'end' to stop default newline, replaced by Fore.RESET

    if vm_status:
        # Print last VM status
        hdrprint("HVM")
        if vm_status:
            nprint(vm_status)
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
    padprint("Initialising {}...".format(VERSION))
    
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
    
        # Get latest system info
        padprint("Scanning hardware status...")
        sys_data = sysinfo.get_all()
        
        # Get initial VM status
        if GET_HYPERV:
            padprint("Scanning for Hyper-V VMs...")
            vm_counter = 0
            vm_status = vm_str()
        else:
            vm_status = None

        # Get initial hosts status
        if GET_HOSTS:
            padprint("Scanning web hosts...")
            hosts_counter = 0
            hosts_status = hosts_str(HOSTS)
        else:
            hosts_status = None
        
        # Get storage data
        if GET_STORAGE:
            padprint("Scanning storage devices...")
            storage_status = storage_str(diskscan.get_all())
        else:
            storage_status = None

        padflush()

        if args.reload:
            while True:
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
                print_shot(sys_data, storage_status, hosts_status, vm_status, show_cores=SHOW_CORES)

                # Pause
                time.sleep(INTERVAL)
                
                # Get latest system info
                sys_data = sysinfo.get_all()
        else:
            print_shot(sys_data, storage_status, hosts_status, vm_status, show_cores=SHOW_CORES)

    except KeyboardInterrupt:
        pass