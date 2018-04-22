# -*- coding: utf-8 -*-
"""
Created on Wed Aug 10 09:46:09 2016

@author: jtc9242
"""
import wmi
import pythoncom
import copy

def get_all(sensor_list = None):

    if sensor_list:
        sensor_list = copy.copy(sensor_list)
        for i, s in enumerate(sensor_list):
            sensor_list[i] = s.split('/')  # Break sensor name by /
    
    pythoncom.CoInitialize()

    # Connect to OpenHardwareMonitor
    w = wmi.WMI(namespace="root\OpenHardwareMonitor")
    
    data = {}
    
    # Get sensor data. Note: This totally rebuilds the sensor array, so targetting below is required at each run
    data_all = w.Sensor()

    if len(data_all) > 0:
        for d in data_all:
            if sensor_list:
                for s in sensor_list:
                    if d.Name == s[0] and d.SensorType == s[1]:
                        data["{0}/{1}".format(d.Name, d.SensorType)] = round(d.Value,2)
            else:
                data["{0}/{1}".format(d.Name, d.SensorType)] = round(d.Value,2)
        return data
    else:
        print("OpenHardwareMonitor cannot be found.")
        return None
    


def get_objects(sensor_list):

    for i, s in enumerate(sensor_list):
        sensor_list[i] = s.split('/')  # Break sensor name by /
    
    pythoncom.CoInitialize()

    # Connect to OpenHardwareMonitor
    w = wmi.WMI(namespace="root\OpenHardwareMonitor")
    
    data = []
    
    # Get sensor data. Note: This totally rebuilds the sensor array, so targetting below is required at each run
    data_all = w.Sensor()
    if len(data_all) > 0:
        for d in data_all:
            for s in sensor_list:
                if d.Name == s[0] and d.SensorType == s[1]:
                    data.append(d)
    else:
        print("OpenHardwareMonitor cannot be found.")
        for s in sensor_list:
            data.append(None)

    return data