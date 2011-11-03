#!/bin/sh

# find script dir http://stackoverflow.com/questions/59895/can-a-bash-script-tell-what-directory-its-stored-in
DIR="$( cd -P "$( dirname "$0" )" && pwd )"

# Kubuntu 11.10: modified symbolic link /usr/lib/libpython2.7.so to point to /usr/lib/libpython3.2mu.so.1.0

export PYQTDESIGNERPATH=$DIR/wic/widgets/
export PYTHONPATH=$DIR/wic/widgets/
cd $DIR/wic/widgets/
export PATH=$PATH:$DIR/wic/widgets/
#printenv
designer