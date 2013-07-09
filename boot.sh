#!/bin/bash

names='ns_xm netsoul_host netsoul_auth netsoul_client'
sudo echo 'killing..'
if [ $? == 0 ]
then
    for name in $names
    do
	echo "kill $name"
	if [ "`pidof $name`" != "" ]
	then
	    sudo kill -s SIGKILL `pidof $name`
	fi
    done
    (setsid cptsoul &)
    sleep 1
else
    echo 'Etes vous sur detre root ?'
fi
