#!/usr/bin/env python3

import os
import sys

import paramiko

file = sys.argv[-1]

RESET_KNOWN_HOSTS = False

ssh = paramiko.SSHClient()
if RESET_KNOWN_HOSTS:
    open('known_hosts', 'w')
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.load_host_keys('known_hosts')
key = paramiko.RSAKey.from_private_key_file('key')
ssh.connect('lesterfx.mooo.com', username='pi', pkey=key)
sftp = ssh.open_sftp()
sftp.put(file, os.path.join('pixels', os.path.basename(file)))
ssh.close()
