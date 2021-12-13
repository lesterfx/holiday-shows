class Relay_Remote(dict):
    def __init__(self, name, config, client):
        self.client = client
        self.name = name
        ip = config.ip
        port = config.port
        for i, relay_name in enumerate(config.relays):
            if relay_name is None: continue
            relay = Relay(self, relay_name, i)
            self[relay_name] = relay
        if not self: return
        self.client_index = client.append(ip, port)
        self.all(0)

    def __hash__(self):
        return hash(self.name)

    def show(self):
        if not self: return ''
        for relay in self.values():
            self.client.set_relay(self.client_index, relay.index, relay.value)
        return self.client.send_state(self.client_index)
    
    def all(self, value):
        for relay in self.values():
            relay.value = value
        self.show()

class Relay(object):
    def __init__(self, remote, name, index):
        self.remote = remote
        self.name = name
        self.index = index
        self.value = 0

    def set(self, value):
        self.value = int(bool(value))

    def show(self):
        self.remote.show()
