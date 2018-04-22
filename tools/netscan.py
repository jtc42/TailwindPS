# -*- coding: utf-8 -*-
import urllib.request
import urllib.error

# Function to check if HTTP connection to host on port is available
def http_online_old(url):
    
    # Add port if missing
    if len(url.split(':')) < 2:
        url = url + ':80'

    try:
        urllib.request.urlopen(url, timeout=5)
        return True
    except urllib.error.URLError as e:
        print("{} offline".format(url))
        print(e.reason)
        return False
    

import socket
def http_online(url):
    
    # Strip protocol if it exists in the url
    u = url.split('://')
    if len(u) == 2:
        url = u[1]
        
    # Strip paths if any exist in the url
    u = url.split('/')
    if len(u) > 1:
        url = u[0]
    
    # Add port if missing
    u = url.split(':')
    if len(u) < 2:
        u.append(80)
    else:
        u[1] = int(u[1])

    # Test socket connection
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((u[0], u[1]))
        s.close()
        return True
    except socket.error as e:
        s.close()
        return False
    

def online_dict(host_dict, debug=False):
    for d in host_dict:
        if debug:
            print("Scanning {}".format(d['url']))
        d['online'] = http_online(d['url'])
    return host_dict