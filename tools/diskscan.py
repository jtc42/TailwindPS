import psutil

def get_all():
    devices = [d.device for d in psutil.disk_partitions()]  # Get list of all device paths

    data = []
    for d in devices:
        loads = psutil.disk_usage(d)
        j = {
            'device': d,
            'total': loads.total/1E9,
            'used': loads.used/1E9,
            'free': loads.free/1E9,
            'load': loads.percent
        }

        data.append(j)

    return data