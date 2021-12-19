import socket

def my_ip():
    # https://stackoverflow.com/a/28950776/3130539
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip
MY_IP = my_ip()

if __name__ == '__main__':
    print(MY_IP)