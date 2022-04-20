#!/usr/bin/env python3
# vim:et:ts=4:sw=4:fdm=marker:fenc=utf-8:
import requests
import os
import sys
from hashlib import md5
import textwrap

# defaults, settings & other preliminary definitions {{{1
# defaults/settings {{{2
# Upload to both hardfought and nao by default; behavior can be changed
# dynamically from the defaults set here with cmdline options
HARDFOUGHT, NAO = True, True
SILENT = False
# Modify this NH version's rcfile on NAO
nao_ver = '3.6.6'
# allowed command line options {{{3
HDF_FLAGS = ['-hardfought', '-hdf', 'H']
NAO_FLAGS = ['-nao', '-altorg', 'a']
HELP_FLAGS = ['-help', 'h', '?']
SILENT_FLAGS = ['-silent', 's']


def negate(flags): # {{{2
    return ['-no' + f for f in flags if f.startswith('-')]


def ffmt(flags): # {{{2
    return ['-' + f for f in flags]


# generate help text congruent with defaults set on line 11 {{{2
# usage {{{3
usage = "USAGE: {script} [-h] [-Ha] <USER> <PASS>".format(
    script = os.path.basename(sys.argv[0])
)
# description {{{3
desc = "This script can update rcfiles on NAO and/or hardfought.org; "\
    "default behavior is {nao} update NAO and {hdf} update hardfought, "\
    "but this can be modified by the options listed in the next section."
# fill in the blanks with current defaults
desc = desc.format(nao = 'to' if NAO else 'not to',
                   hdf = 'to' if HARDFOUGHT else 'not to')
# wrap description to terminal width or 80 columns, whichever is smaller
try:
    h, w = os.get_terminal_size()
    w = 80 if w > 80 else w
except OSError as ex:
    w = 80
desc = textwrap.fill(desc, w)
# options {{{3
# use stuff set above (lines 9-18) to generate options list
options = [
    [",".join(ffmt(sorted(HELP_FLAGS, key=lambda f:len(f)))),
     "Display this information"],
    [",".join(ffmt(sorted(SILENT_FLAGS, key=lambda f:len(f)))),
     "Run without printing status"],
    [",".join(ffmt(sorted(HDF_FLAGS, key=lambda f:len(f)))),
     "Enable hardfought.org{}".format(' (default)' if HARDFOUGHT else '')],
    [",".join(ffmt(sorted(negate(HDF_FLAGS), key=lambda f:len(f)))),
     "Disable hardfought.org{}".format('' if HARDFOUGHT else ' (default)')],
    [",".join(ffmt(sorted(NAO_FLAGS, key=lambda f:len(f)))),
     "Enable nethack.alt.org{}".format(' (default)' if NAO else '')],
    [",".join(ffmt(sorted(negate(NAO_FLAGS), key=lambda f:len(f)))),
     "Disable nethack.alt.org{}".format('' if NAO else ' (default)')]
]
# put it all together {{{3
HELPTEXT = '{usage}\n\n{description}\n\nOPTIONS:\n{options}\n'.lstrip().format(
    usage = usage,
    description = desc,
    options = '\n\n'.join(
        ['    {0:<28s}{1:s}'.format(*o) for o in options]
    )
)


def print2(*args, **argv): # {{{2
    if not SILENT:
        print(*args, **argv, file=sys.stderr)


def get_home_dir(): # {{{2
    h = ''
    if os.name == 'nt':
        h = os.path.join(
            os.getenv('HOMEDRIVE', default=os.getenv('HOME')),
            os.getenv('HOMEPATH', default='')
        )
    else:
        h = os.getenv('HOME')
    return h


def rcfile_location(): # {{{2
    if os.name == 'nt':
        # rcfiles for 3.6.3 and later are saved as
        #   %HOMEDRIVE%\%HOMEPATH%\Nethack\.nethackrc
        # earlier versions' config files are saved as
        #   %NETHACKDIR%\defaults.nh
        # see https://github.com/NetHack/NetHack/wiki/Windows-NetHack-3.6.3-Breaking-Change-:-Directory-Paths
        rcfl = os.path.join(os.getenv('HOMEDRIVE'), os.getenv('HOMEPATH'), 'Nethack', '.nethackrc')
        if not os.path.isfile(rcfl):
            rcfl = os.path.join(os.getenv('NETHACKDIR',
                                          default=get_home_dir()),
                                'defaults.nh')
    else:
        # on *nix systems just use ~/.nethackrc
        rcfl = os.path.join(os.getenv('HOME'), '.nethackrc')
    return rcfl


def server_error(response, explanation = 'connection attempt', **argv): # {{{2
    server_name = argv.get('server', 'server')
    print2(
        'error\n{action:s}: {site:s} responded {err:n} {msg:s}'.format(
            action = explanation,
            site = server_name,
            err = response.status_code,
            msg = response.reason
        )
    )


def parse_args(args): # {{{2
    # move flags to their own list {{{3
    options = []
    i = 0
    while i < len(args):
        a = args[i]
        if a.startswith('-'):
            arg = args.pop(i)[1:]
            options += [arg] if arg.startswith('-') else list(arg)
        else:
            i += 1
    h, n = parse_options(options)
    # make sure only username & pass remain {{{3
    if len(args) != 2:
        print2(usage)
        exit()
    u, p = args
    return (u, p, h, n)


def parse_options(options): #{{{2
    # allowable flags
    global SILENT
    hdf, nao = HARDFOUGHT, NAO
    for o in options:
        # enable/disable hdf {{{3
        if o in HDF_FLAGS:
            hdf = True
        elif o in negate(HDF_FLAGS):
            hdf = False
        # enable/disable nao {{{3
        elif o in NAO_FLAGS:
            nao = True
        elif o in negate(NAO_FLAGS):
            nao = False
        elif o in SILENT_FLAGS:
            SILENT = True
        elif o in HELP_FLAGS:
            print2(HELPTEXT)
            exit(0)
        else:
            option = '-{flag:s}'.format(flag = o)
            print2('{u}\n\nunrecognized option: {o:s}'.format(u = usage,
                                                              o = option))
            exit(0)
    return (hdf, nao)
# }}}1


args = sys.argv[1:]
user, passwd, HARDFOUGHT, NAO = parse_args(args)

rcfile = rcfile_location()
if not os.path.isfile(rcfile):
    print2('{u}\n\nfile does not exist: {f}'.format(u = usage,
                                                    f = rcfile))
    exit(1)

try:
    with open(rcfile, 'rb') as f:
        nethackrc = f.read()
except FileNotFoundError as ex:
    print2('{u}\n\nfile does not exist: {f}'.format(u = usage,
                                                    f = rcfile))
    exit(1)
except UnicodeDecodeError as ex:
    # shouldn't happen since we are using rb mode, but leaving it here in case
    # that is changed in the future
    print2('{u}\n\ndecode error: {e}'.format(u = usage,
                                             e = ex))
    exit(1)

if nethackrc is None or len(nethackrc) == 0:
    print2('{u}\n\naborting: rcfile is empty'.format(u = usage))
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

if not HARDFOUGHT:
    removed = sites.pop('hdf')

if not NAO:
    removed = sites.pop('nao')

if len(sites) == 0:
    print2('quitting: all sites disabled')
    exit(0)

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
