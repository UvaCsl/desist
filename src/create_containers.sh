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
      sudo docker build . -t "${dir}"
      echo "${dir}" >> "${docker_image_list}"
    fi
    cd ../
  fi
done

# Last but not least, create the container that runs the workflow

cd ../
sudo docker build  . -t "in_silico_trial"
