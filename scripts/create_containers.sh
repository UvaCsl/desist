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

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd ${DIR}
docker_image_list="../workflow/docker_image_list"
docker_image_list=`realpath "${docker_image_list}"`

if [ -e "${docker_image_list}" ]; then
  rm "${docker_image_list}"
fi

# Create Docker images
cd ../software
for dir in *; do
  if [ -d "${dir}" ]; then
    cd "${dir}"
    if [ -f Dockerfile ]; then
      if [[ "${dir}" = *" "* ]]; then
        echo "Directory '${dir}' contains spaces, to tag the image no space is allowed, exiting"
        exit 1
      fi
      docker build . -t "${dir}"
      echo "${dir}" >> "${docker_image_list}"
    fi
    cd ../
  fi
done

# Last but not least, create the container that runs the workflow

cd ../
docker build  . -t "in_silico_trial"
