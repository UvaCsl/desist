#!/bin/bash

realpath() {   
  OURPWD=$PWD;
  cd "$(dirname "$1")";
  LINK=$(readlink "$(basename "$1")");
  while [ "$LINK" ]; do
    cd "$(dirname "$LINK")";     LINK=$(readlink "$(basename "$1")");
  done;
  REALPATH="$PWD/$(basename "$1")";
  cd "$OURPWD";
  echo "$REALPATH";
}

set -e

function usage {
  echo "Usage: $0 <variables.xml> <working_folder> <number_of_patients>"
  exit 1
}
if [ $# -lt 3 ]; then
  usage
fi

if [ ! -f $1 ]; then
  echo "Could not find config file $1"
  usage
fi

if [ -e $2 ]; then
  echo "removing existing file/folder $2, press enter to continue, or CTRL-C to abort"
  read   
  rm -rf $2
fi

mkdir $2
cp $1 $2/config.xml

sudo docker run -v `realpath $2`:/patients virtual_patient_generation $3
sudo docker run -v /var/run/docker.sock:/var/run/docker.sock -v `realpath $2`:/patients in_silico_trial /patients/config.xml `realpath $2`

sudo chown -R `whoami`:`whoami` $2