#!/usr/bin/env python3

import time

from . import relay, remote_client
from .players import PLAYER_KINDS

class Home(object):
    def __init__(self, globals_):
        self.globals = globals_
        self.init_relays()
        self.init_remote_clients()
        self.init_music_client()
        self.init_strips()

    def init_remote_clients(self):
        print('Initializing Remotes')
        self.remote_clients = {}
        for name, config in self.globals['remotes'].items():
            client = remote_client.Remote_Client(name, config)
            self.remote_clients[name] = client
            if client.local:
                self.local_client = client

    def init_music_client(self):
        print('Initializing Music Client')
        self.music_client = self.remote_clients[self.globals['music_server']]
        self.music_client.add_player(PLAYER_KINDS.MUSIC, None)

    def init_strips(self):
        print('Initializing Strips')
        for strip_config in self.globals['strips']:
            self.remote_clients[strip_config['name']].add_player(PLAYER_KINDS.STRIP, strip_config)

    def init_relays(self):
        self.relays = {}
        self.remotes = {}
        for name, config in self.globals['relay_remotes'].items():
            remote = relay.RelayRemote(name, config)
            self.remotes[name] = remote
            intersection = set(remote).intersection(self.relays)
            if intersection:
                message = f'Duplicate relay names found: {", ".join(intersection)}'
                raise KeyError(message)
            self.relays.update(remote)

        unassigned = set(self.relays)
        self.relay_groups = {}
        for group_name in [
            'off_when_blank',
            'off_for_shows',
            'animate',
            'on_show_nights'
        ]:
            self.relay_groups[group_name] = []
            for relay_name in self.globals['relay_purposes'].get(group_name, []):
                self.relay_groups[group_name].append(self.relays[relay_name])
                unassigned.remove(relay_name)
        if unassigned:
            raise ValueError(f'Unassigned relays: {unassigned}')

    def show_relays(self, do_print=False):
        for remote in self.remotes.values():
            labels = remote.show()
            if do_print:
                print(remote.name, labels, end=' ')
        if do_print:
            print()

    def report_dropped_frames(self):
        for name, remote in self.remotes.items():
            try:
                received, sent = remote.get_frames()
            except:
                print(f'{name}: error getting frames')
            else:
                if sent:
                    print(f'{name}: received {received} of {sent} frames ({received/sent:.0%} success)')
                else:
                    print(f'{name}: no frames sent')

    def report_relay_duty_cycles(self):
        results = []
        for name, relay in self.relays.items():
            results.append((relay.time_on, name))
        results.sort()
        for time_on, name in results:
            print(f'relay timing: on {time_on:.0%} of the time ({name})')

    def __enter__(self):
        self.show_relays()
        return self

    def cleanup(self):
        for client in self.remote_clients:
            self.remote_clients[client].disconnect()
        self.clear_relays()

    def __exit__(self, *args, **kwargs):
        self.cleanup()
        print('Complete')
    
    @staticmethod
    def run_for(seconds, function, *args, **kwargs):
        end = time.time() + seconds
        while time.time() < end:
            function(*args, **kwargs)

    def clear_relays(self):
        for remote in self.remotes.values():
            remote.all(False)

    def __setitem__(self, key, value):
        key = int(key)
        if key not in self: return
        self.strip[key] = value or 0

    def __del__(self):
        try:
            self.clear(True)
        except:
            pass
