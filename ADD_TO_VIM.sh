#!/bin/bash

vimrcfile="$HOME/.vimrc"

if [ ! -f ./rcup.py ]
then
    echo >&2 'Please cd into the bundle before running this script.'
    exit 1
elif [ ! -f "$vimrcfile" ]
then
    echo >&2 'No .vimrc file in your home directory.'
    exit 1
else
    echo >&2 'Adds an autocommand to your .vimrc to use "ronin" (via the rcup.py script)'
    echo >&2 'to sync remote files with your local copy whenever ~/.nethackrc is saved.'
    echo >&2
    echo >&2 'NB: this will write your username & password in plaintext to your .vimrc!!'
    echo >&2
    servers=""
    read -p'alt.org username (blank skips): ' -e nao_user
    if test -n "$nao_user"; then
        read -p'alt.org password (blank skips): ' -es nao_pass
        echo
        if test -n "$nao_pass"; then
            servers=" nao"
        else
            nao_user=
        fi
    fi
    read -p'hardfought username (blank skips): ' -e hdf_user
    if test -n "$hdf_user"; then
        read -p'hardfought password (blank skips): ' -es hdf_pass
        echo
        if test -n "$hdf_pass"; then
            servers="$servers$([ -n "$servers" ] && printf " and " || printf " ")hdf"
        else
            hdf_user=
        fi
    fi
    if [ -z "$servers" ]; then
        echo >&2 "no servers selected. goodbye"
        exit 0
    fi
    printf >>"$vimrcfile" '" keep .nethackrc updated on%s via ronin\n' "$servers"
    autocmd=""
    if [ "$hdf_user" = "$nao_user" ] && [ "$hdf_pass" = "$nao_pass" ]; then
        autocmd="$PWD/rcup.py -ha $nao_user '$nao_pass' &"
    else
        if [ -n "$nao_user" ]; then
            autocmd="$PWD/rcup.py  --nao --no-hdf $nao_user '$nao_pass' &"
        fi
        if [ -n "$hdf_user" ]; then
            autocmd="${autocmd}$([ -n "$autocmd" ] && echo "; ")$PWD/rcup.py --no-nao --hdf $hdf_user '$hdf_pass' &"
        fi
    fi
    echo >>"$vimrcfile" "autocmd! BufWritePost ~/.nethackrc sil!!$autocmd"
    echo >&2
    echo >&2 'Done.'
fi

