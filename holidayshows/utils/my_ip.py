import socket

def my_ip() -> str:
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

def my_hostname() -> str:
    return socket.gethostname()

MY_IP: str = my_ip()
MY_HOSTNAME: str = my_hostname()
ME = {MY_IP, MY_HOSTNAME}

if __name__ == '__main__':
    print(MY_IP)