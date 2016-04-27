#!/bin/bash

WEBSERVER=$1
WEBUSER=$2
HTDOCS=$3
SRC=web/

rsync -rv $SRC $WEBUSER@$WEBSERVER:$HTDOCS
ssh $WEBUSER@$WEBSERVER "chown -R $WEBUSER:users $HTDOCS; find $HTDOCS -type d -exec chmod 775 {} \;; find $HTDOCS -type f -exec chmod 644 {} \;"
