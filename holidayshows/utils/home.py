#!/usr/bin/env python3

import time

from . import music_client, relay_client, relay, remote_client

from enum import Enum
PLAYER_KINDS = Enum('MUSIC', 'STRIP')

class Home(object):
    def __init__(self, globals_):
        self.globals = globals_
        self.init_relays()
        self.init_remotes()
        self.init_music_client()
        self.init_strips()
        self.clear()
        self.show()

    def init_remote_clients(self):
        print('Initializing Remotes')
        self.remote_clients = {}
        for name, config in self.globals.remotes:
            self.remote_clients[name] = remote_client.Remote_Client(config)

    def init_music_client(self):
        print('Initializing Music Client')
        self.remote_clients[self.globals.music_server].add_player(PLAYER_KINDS.MUSIC, None)

    def init_strips(self):
        print('Initializing Strips')
        self.strips = {}
        for strip_config in self.globals.strips:
            self.remote_clients[strip_config.name].add_player(PLAYER_KINDS.STRIP, strip_config)

    def init_relays(self):
        self.relay_client = relay_client.RelayClient()

        self.relays = {}
        self.remotes = {}
        for name, config in self.globals.relay_remotes.items():
            remote = relay.Relay_Remote(name, config, self.relay_client)
            self.remotes[name] = remote
            self.relays.update(remote)
        self.relay_client.handshake_all()
        self.relay_groups = {}
        for name in [
            'off_when_blank',
            'off_for_shows',
            'animate_between_shows',
            'on_show_nights'
        ]:
            self.relay_groups[name] = []
            for relay_name in self.globals.relay_purposes.get(name, []):
                self.relay_groups[name].append(self.relays[relay_name])
    
    def show_relays(self):
        for remote in self.remotes.values():
            labels = remote.show()
            # print(remote.name, labels, end=' ')
        # print()

    def __enter__(self):
        self.show_relays()
        return self

    def cleanup(self):
        self.clear()
        self.show()
        for strip in self.strips:
            self.strips[strip].disconnect()
        self.clear_relays()

    def __exit__(self, *args, **kwargs):
        self.cleanup()
        print('Complete')
    
    @staticmethod
    def run_for(seconds, function, *args, **kwargs):
        end = time.time() + seconds
        while time.time() < end:
            function(*args, **kwargs)

    def clear(self, show=False):
        self.strip.clear(show)
    
    def clear_relays(self):
        for remote in self.remotes.values():
            remote.all(False)

    def show(self):
        self.strip.show()

    def __setitem__(self, key, value):
        key = int(key)
        if key not in self: return
        self.strip[key] = value or 0

    def __del__(self):
        try:
            self.clear(True)
        except:
            pass
