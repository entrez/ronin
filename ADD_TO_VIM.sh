#!/bin/sh

if [ ! -f ./rcup.py ]
then
    echo >&2 'Please cd into the bundle before running this script.'
    exit 1
elif [ ! -f ~/.vimrc ]
then
    echo >&2 'No .vimrc file in your home directory.'
    exit 1
else
    echo >&2 'Adds an autocommand to your .vimrc to run rcup.py whenever ~/.nethackrc is'
    echo >&2 'saved.'
    echo >&2 'NB: this will write your NAO username & password in plaintext to your .vimrc'
    echo >&2
    read -p'alt.org username (blank aborts): ' -e nao_user
    test -n "$nao_user" || exit 0
    read -p'alt.org password (blank aborts): ' -es nao_pass
    test -n "$nao_pass" || exit 0
    echo >>~/.vimrc '" keep nao .nethackrc updated'
    echo >>~/.vimrc "autocmd! BufWritePost ~/.nethackrc sil!!$PWD/rcup.py $nao_user '$nao_pass' &"
    echo >&2
    echo >&2 'Done.'
fi

