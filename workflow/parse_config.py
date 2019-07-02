#!/usr/bin/python3
# -*- coding: utf-8 -*-
import subprocess
import os 
import sys
dir_path = os.path.dirname(os.path.realpath(__file__))

if len(sys.argv) > 1:
  var_file = sys.argv[1]
else:
  var_file = "/patients/variables.xml"

xsltproc_result = subprocess.run(['xsltproc',var_file], stdout=subprocess.PIPE, check=True)
with open("/patients/config.xml", "wb") as f:
  f.write(xsltproc_result.stdout)
