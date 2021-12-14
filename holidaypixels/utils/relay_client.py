import socket

class RelayClient:
    # ips: array of ip addresses of relay control boards. The index of the ip in the list is used
    # to address future commands to that particular board
    def __init__(self):
        self.ip_ports = []
        self.state  = []
        self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

    def append(self, ip, port):
        self.ip_ports.append((ip, port))
        self.state.append(0xDD0000)
        return len(self.ip_ports) - 1

    # Check that we can talk to all the clients
    def handshake_all(self):
        for ip, port in self.ip_ports:
            self.socket.sendto(bytes.fromhex('AA0000'), (ip, port))

        ips_remaining = [ip for ip, port in self.ip_ports]

        while len(ips_remaining) > 0:
            self.socket.settimeout(1)
            try:
                msg, (returnIP, returnPort) = self.socket.recvfrom(3)
            except socket.timeout:
                raise Exception(f'Timeout on handshake. Not connected: {", ".join(ips_remaining)}')
            if (msg != b'\xbb\x00\x00'):
                print(msg)
                raise Exception("Invalid Handshake Msg: {}".format(msg))
            print(returnIP, 'handshake success')
            ips_remaining.remove(returnIP)

        return True

    # Get the number of frames sent since last call of get_frames on the server
    # ip_idx: index of IP address to request the frame count from.
    # IMPORTANT NOTE 1: You can only do this for one IP at a time. You must wait for the response or
    # timeout before sending another request
    # IMPORTANTE NOTE 2: If there is packet loss while this command is executing it WILL timeout and raise an exception. 
    # Make sure to deal with errors (try...catch) if you want the code to continue to execute even on packet loss
    def get_frames(self, ip_idx):
        ip, port = self.ip_ports[ip_idx]
        self.socket.sendto(bytes.fromhex('CC0000'), (ip, port))

        self.socket.settimeout(1)
        msg, (returnIP, returnPort) = self.socket.recvfrom(3)
        if returnIP != ip:
            raise Exception("Get frame error - invalid return IP. Only call for one device at a time")
        if msg[0] != 0xCC:
            raise Exception("Invalid response from get_frames: {}".format(msg))
        return int.from_bytes(msg[1:3], "big")
        

    # Set relay state
    # ip_idx: IP Address index
    # relay_idx: Relay index
    # value: On (True) or Off (False)
    # send_now: Whether a state frame should be sent to the relay control. 
    # Make sure all relays have been set to their value before sending (by setting last one to True or calling send_state)
    def set_relay(self, ip_idx, relay_idx, value, send_now = False):
        if value:
            self.state[ip_idx] |= (1 << relay_idx)
        else:
            self.state[ip_idx] &= ~(1 << relay_idx)
        if send_now: self.send_state(ip_idx)

    # Sets all relays on. See set_relay
    def set_all_on(self, ip_idx, send_now = False):
        self.state[ip_idx] = 0xDDFFFF
        if send_now: self.send_state(ip_idx)

    # Sets all relays off. See set_relay
    def set_all_off(self, ip_idx, send_now = False):
        self.state[ip_idx] = 0xDD0000
        if send_now: self.send_state(ip_idx)

    # Sends the state to the relay
    def send_state(self, ip_idx):
        ip, port = self.ip_ports[ip_idx]
        # print(self.state[ip_idx].to_bytes(3, byteorder='big').hex())
        self.socket.sendto(self.state[ip_idx].to_bytes(3, byteorder='big'), (ip, port))
        return bin(self.state[ip_idx])[-16:].replace("0", ".").replace("1", "|")

if __name__ == '__main__':
    import time
    client = RelayClient()
    client.append('192.168.3.240', 2700)
    client.append('192.168.3.242', 2700)
    print('Handshaking...')
    client.handshake_all()
    print('Success!')
    for on in True, False:
        for i in range(16):
            box, relay = divmod(i, 16)
            print(f'Setting box {box} relay {relay} to {on}')
            client.set_relay(box, relay, True, True)
            time.sleep(1)
    print('Test complete')
