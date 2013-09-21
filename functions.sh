# (C)opyright L.P.Klyne 2013

function is_mounted()
{
	if mount | grep --quiet "$1"; then
		echo "$1 is mounted"
	    return 0
	fi
	echo "$1 is not mounted"
	return 1
}

function do_rsync()
{
	echo "rsync from $1 to $2 - `date`"
	rsync --archive --verbose $1 $2 >>$RSYNC_LOGFILE
	echo "rsync complete - `date`"
}
