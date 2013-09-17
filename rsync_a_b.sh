#!/bin/bash
# (C)opyright L.P.Klyne 2013
source /opt/fileserver/config.sh
source /opt/fileserver/functions.sh

if is_mounted $DISKA && is_mounted $DISKB ; then
	do_rsync "$DISKA/*" "$DISKB/"
fi
