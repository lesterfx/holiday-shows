#!/usr/bin/env python3

from __future__ import print_function

import argparse
import json
import os
import sys

class Holiday_Pixels(object):
    def __init__(self):
        self.load_args()
        self.load_config()

    def load_args(self):
        parser = argparse.ArgumentParser(description='Holiday Lights')
        parser.add_argument('--reset', const=True, choices=['force'], nargs='?', default=False, help='Create a sample config file if one does not exist')
        parser.add_argument('--demo', help='Run named animation immediately')
        parser.add_argument('--display', choices=['gpio', 'console'], default='gpio', help='Where to render the animation')
        self.args = parser.parse_args()

    def load_config(self):
        self.config = json.load(open('default_config.json'))
        config_file = self.config_file
        print('Config file path:')
        print(config_file)
        if self.args.reset == 'force' or not os.path.exists(config_file):
            if self.args.reset:
                print('Saving default config file.')
                with open(config_file, 'w') as config:
                    json.dump(self.config, config, indent=4)
            else:
                print('File not found.')
                print('To auto-populate run with argument "--reset"')
                raise Exit
        else:
            if self.args.reset:
                print('Reset argument passed, but config file already exists. Use "--reset force" to make a new config')
                raise Exit
            print('Loading config')
            with open(config_file) as config:
                self.merge_config(json.load(config))
    
    @property
    def config_file(self):
        return os.path.join(os.path.expanduser('~'), '.holiday-pixels-config.json')

    def merge_config(self, override):
        def merge_dict(base, update):
            base_keys = set(base.keys())
            update_keys = set(update.keys())
            invalid_keys = update_keys - base_keys
            if invalid_keys:
                msg = 'Unexpected key(s) {}'.format(' '.join(invalid_keys))
                raise KeyError(msg)
            for key in update_keys:
                if isinstance(base[key], dict):
                    print('merging', key)
                    merge_dict(base[key], update[key])
                else:
                    print('overwriting', key)
                    base[key] = update[key]
        merge_dict(self.config, override)

class Exit (Exception):
    pass

def main():
    try:
        Holiday_Pixels()
    except Exit:
        sys.exit()

if __name__ == '__main__':
    main()