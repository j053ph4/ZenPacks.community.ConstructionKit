#!/bin/bash

ZENPACKFILE=$1;
ABSOLUTE_PATH=$(cd `dirname "${BASH_SOURCE[0]}"` && pwd)
echo "DIR $ABSOLUTE_PATH"
NAME=$(echo $ZENPACKFILE | cut -f 1 -d '-')
echo "installing $ZENPACKFILE $NAME"
$ABSOLUTE_PATH/save-components.py -Z $NAME ; wait
zenpack --install=$ZENPACKFILE; wait ; zopectl restart ; zenhub restart
$ABSOLUTE_PATH/load-components.py -Z $NAME ; wait

