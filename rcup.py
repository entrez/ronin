#!/usr/bin/env python3
# vim:et:ts=4:sw=4:fdm=marker:fenc=utf-8:
import requests
import os
import sys
from hashlib import md5

nao_ver = '3.6.6'

def print2(*args, **argv):
    print(*args, **argv, file=sys.stderr)


def rcfile_location():
    # {{{
    if os.name == 'nt':
        # rcfiles for 3.6.3 and later are saved as
        #   %HOMEDRIVE%\%HOMEPATH%\Nethack\.nethackrc
        # earlier versions' config files are saved as
        #   %NETHACKDIR%\defaults.nh
        # see https://github.com/NetHack/NetHack/wiki/Windows-NetHack-3.6.3-Breaking-Change-:-Directory-Paths
        rcfl = os.path.join(os.getenv('HOMEDRIVE'), os.getenv('HOMEPATH'), 'Nethack', '.nethackrc')
        if not os.path.isfile(rcfl):
            rcfl = os.path.join(os.getenv('NETHACKDIR', default=os.getenv('HOME')),
                                'defaults.nh')
    else:
        # on *nix systems just use ~/.nethackrc
        rcfl = os.path.join(os.getenv('HOME'), '.nethackrc')

    return rcfl
    # }}}


def server_error(response, explanation = 'connection attempt', **argv):
    # {{{
    server_name = argv.get('server', 'server')
    print2(
        'error\n{action:s}: {site:s} responded {err:n} {msg:s}'.format(
            action = explanation,
            site = server_name,
            err = response.status_code,
            msg = response.reason
        )
    )
    # }}}


args = sys.argv[1:]
if len(args) != 2:
    print2('usage: {script} USER PASS'.format(script = os.path.basename(sys.argv[0])))
    exit()

user, passwd = args

rcfile = rcfile_location()
if not os.path.isfile(rcfile):
    print2('file does not exist: {}'.format(rcfile))
    exit(1)

try:
    with open(rcfile, 'rb') as f:
        nethackrc = f.read()
except FileNotFoundError as ex:
    print2('file does not exist: {}'.format(rcfile))
    exit(1)
except UnicodeDecodeError as ex:
    # shouldn't happen since we are using rb mode, but leaving it here in case
    # that is changed in the future
    print2('decode error: {}'.format(ex))
    exit(1)

if nethackrc is None or len(nethackrc) == 0:
    print2('error: rcfile is empty')
    exit(1)
else:
    # we need to run the contents of the rcfile through strip() because \n is
    # prepended to the beginning of the file for some reason if it is submitted
    # via the web interface -- if the only difference in the two files is
    # removed by strip() there's really no point in updating it anyway though.
    rc_hash = md5(nethackrc.strip())

nh = 'nh{0:s}'.format(nao_ver.replace('.', ''))

sites = {
    'nao': {
        'login': {
            'url': 'https://alt.org/nethack/login.php',
            'data': {
                'nao_username': user,
                'nao_password': passwd,
                'submit': 'Login'
            }
        },
        'rcfile': {
            'url': 'https://alt.org/nethack/userdata/{letter}/{user}/{user}.{nh}rc'.format(
                letter = user[0],
                user = user,
                nh = nh
            )
        },
        'rcedit': {
            'url': 'https://alt.org/nethack/webconf/nhrc_edit.php',
            'params': {
                'nh': nh
            },
            'data': {
                'rcdata': nethackrc,
                'submit': 'Save'
            }
        }
    },
    'hdf': {
        'login': {
            'url': 'https://hardfought.org/nh/nethack/login.php',
            'data': {
                'username': user,
                'password': passwd,
                'submit': 'Login'
            }
        },
        'rcfile': {
            'url': 'https://hardfought.org/userdata/{letter}/{user}/nethack/{user}.{nh}rc'.format(
                letter = user[0],
                user = user,
                nh = 'nh'
            )
        },
        'rcedit': {
            'url': 'https://www.hardfought.org/nh/nethack/rcedit.php',
            'data': {
                'rcdata': nethackrc,
                'submit': 'Save'
            }
        }
    }
}

for serv, reqs in sites.items():
    print2('updating {servername}'.format(servername = serv), end='...')
    # TODO add try/catch block here to catch requests exceptions:
    # ConnectionError, etc
    r = requests.get(**reqs['rcfile'])
    if r.status_code == 200:
        oldrc_hash = md5(r.content.strip())
    else:
        oldrc_hash = md5()

    if oldrc_hash.digest() == rc_hash.digest():
        print2('rcfile already up to date')
        continue

    # create session and login user
    s = requests.Session()
    login = s.post(**reqs['login'])
    if login.status_code != 200:
        server_error(login, 'login attempt', site = serv)
        continue

    rcedit = s.post(**reqs['rcedit'])
    if rcedit.status_code != 200:
        server_error(rcedit, 'rcfile update', site = serv)
        continue

    r = requests.get(**reqs['rcfile'])
    if r.status_code != 200:
        server_error(r, 'updated rcfile retrieval', site = serv)
        continue
    else:
        newrc_hash = md5(r.content.strip())
        if newrc_hash.digest() == rc_hash.digest():
            print2('done')
        else:
            print2('error\nhashes differ even after update!\nold: {old}\nnew: {new}'.format(
                old = rc_hash.hexdigest(),
                new = newrc_hash.hexdigest()
            ))
