import glob

def read_external_temperature():
    base_dir = '/sys/bus/w1/devices/'
    device_folders = glob.glob(base_dir + '28-*')

    if not device_folders:
        return None

    device_file = device_folders[0] + '/w1_slave'

    try:
        with open(device_file, 'r') as f:
            lines = f.readlines()
    except:
        return None

    if lines[0].strip()[-3:] != 'YES':
        return None

    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos + 2:]
        temp_c = float(temp_string) / 1000.0
        return round(temp_c, 1)

    return None

if __name__ == "__main__":
    temp = read_external_temperature()
    print(temp)

