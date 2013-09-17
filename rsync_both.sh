#!/bin/bash
# (C)opyright L.P.Klyne 2013
source /opt/fileserver/config.sh
source /opt/fileserver/functions.sh

if is_mounted $DISKA && is_mounted $DISKB ; then
	echo "rsync both - `date`" &>$RSYNC_LOGFILE
	do_rsync "$DISKA/*" "$DISKB/"
	do_rsync "$DISKB/*" "$DISKA/"
	echo "rsync complete - `date`" &>>$RSYNC_LOGFILE
fi
