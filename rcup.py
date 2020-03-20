#!/usr/bin/env python3
# vim:et:ts=4:sw=4:fdm=marker:fenc=utf-8:
import requests
import os
import sys
from hashlib import md5

nethack_version = '3.6.4'

def print2(*args, **argv):
    print(*args, **argv, file=sys.stderr)

def server_error(response, explanation = 'connection attempt'):
    # {{{
    print2('{2:s}: nao responded {0:n} {1:s}'.format(response.status_code,
                                                     response.reason,
                                                     explanation))
    exit(1)
    # }}}

args = sys.argv[1:]
if len(args) != 2:
    print2('usage: {script} USER PASS'.format(script = os.path.basename(sys.argv[0])))
    exit()

nao_user, nao_pass = args


rcfile = os.path.expanduser('~/.nethackrc')
if not os.path.isfile(rcfile):
    print2('file does not exist: ~/.nethackrc')
    exit(1)

try:
    with open(rcfile, 'rb') as f:
        nethackrc = f.read()
except FileNotFoundError as ex:
    print2('file does not exist: ~/.nethackrc')
    exit(1)
except UnicodeDecodeError as ex:
    # shouldn't happen since we are using rb mode
    print2('decode error: {}'.format(ex))
    exit(1)

if nethackrc is None or len(nethackrc) == 0:
    print('error: rcfile empty')
    exit(1)
else:
    rc_hash = md5(b'\n' + nethackrc)

nh = 'nh{0:s}'.format(nethack_version.replace('.', ''))
rc_url = 'https://alt.org/nethack/userdata/{letter}/{user}/{user}.{nh}rc'.format(
    letter = nao_user[0].lower(),
    user = nao_user,
    nh = nh)
r = requests.get(rc_url)
if r.status_code == 200:
    oldrc_hash = md5(r.content)
else:
    oldrc_hash = ''

if oldrc_hash.digest() == rc_hash.digest():
    print2('nao rcfile is already up to date: exiting')
    exit()

s = requests.Session()

auth_data = {
    'nao_username': nao_user,
    'nao_password': nao_pass,
    'submit': 'Login'
}
login = s.post('https://alt.org/nethack/login.php', data = auth_data)
if login.status_code != 200:
    server_error(login, 'login attempt')

nrc_data = {'rcdata': nethackrc,
            'submit': 'Save'}
nrc_params = {'nh': nh}
submission = s.post('https://alt.org/nethack/webconf/nhrc_edit.php',
       params = nrc_params, data = nrc_data)

if submission.status_code != 200:
    server_error(submission, 'rcfile update')

r = requests.get(rc_url)
if r.status_code != 200:
    server_error(submission, 'updated rcfile retrieval')
else:
    newrc_hash = md5(r.content)
    if newrc_hash.digest() == rc_hash.digest():
        print2('update successful:\n{url:s}'.format(url = rc_url))
    else:
        print2('hmm, hashes differ:\nold: {old}\nnew: {new}'.format(
            old = rc_hash.hexdigest(),
            new = newrc_hash.hexdigest()
        ))
