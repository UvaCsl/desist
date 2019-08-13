#!/usr/bin/python3
# -*- coding: utf-8 -*-
import subprocess
import os 
import sys
from lxml import etree
dir_path = os.path.dirname(os.path.realpath(__file__))

config_file = sys.argv[1]
mount_location = sys.argv[2]
try:
  config = open(config_file, "rb")
except IOError:
  print("File open error")
  exit(1)
config = etree.parse(config);
patients_folder = config.find("patients_directory").text

#load in available docker images
with open(dir_path + "/docker_image_list","r") as f:
  images = f.readlines()
images = [ image[:-1] for image in images ]

#for now assume that every directory is a patient
from glob import glob
patients = glob(patients_folder + "*/")

for patient in patients:
  try:
    patient_file = open(patient+"/config.xml", "rb")
  except IOError:
    print("File open error")
    exit(1)
  patient_config = etree.parse(patient_file);
  print("\033[4m\033[95mHandling patient: " + patient_config.find("Patient/Name").text + "\033[0m\033[0m")
  sys.stdout.flush()
    
  parse_event = subprocess.run(['python3',dir_path + "/parse_events.py",patient +"/config.xml"], stdout=subprocess.PIPE, check=True)
  events = parse_event.stdout.decode().split('\n')[:-1]
  events = [(x.split(' ')[0],x.split(' ')[1]) for x in events] 
  
  for event in events:
    if not event[0] in images:
      print ("\033[91m" + event[0] + " is not available as docker container, skipping\033[0m")
      sys.stdout.flush()
    else:
    # call the docker container of every event 
      print ("\033[92mexecuting docker container of: " + event[0] + "\033[0m")
      sys.stdout.flush()
      subprocess.run(['docker','run','-v',mount_location+"/"+patient.split('/')[-2]+":/patient",event[0],"handle_event","--patient=/patient/config.xml","--event="+event[1]])
      sys.stdout.flush()
