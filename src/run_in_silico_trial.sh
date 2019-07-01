#!/bin/bash

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
cp $1 $2/variables.xml
cp config.xsl $2/config.xsl

sudo docker run -v `realpath $2`:/patients in_silico_trial
sudo docker run -v `realpath $2`:/patients virtual_patient_generation $3
