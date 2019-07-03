#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Parse Events

Usage:
  parse_events.py <patient_config_file.xml> 
  parse_events.py (-h | --help)

Options:
  -h --help     Show this screen.
"""
from docopt import docopt
from sys import exit
from lxml import etree

def run_event(name,number):
  print("%s %s"%(name,number))

if __name__ == '__main__':
    arguments = docopt(__doc__, version='0.1')
    config_file = arguments["<patient_config_file.xml>"];
    
    try:
      config = open(config_file, "rb")
    except IOError:
      print("File open error")
      exit(1)

    queued_events = []
    parsed_events = []
    config = etree.parse(config);

    events = config.find("Patient/events")

    for event in events:
      depend = event.get("depend")
      name = event.get("name")
      number = event.get("id") 
      if not number or not name:
        print("error parsing event, not all fields present")
        exit(1)
      if depend:
        queued_events.append((name,number,depend))
      else:
        run_event(name,number)
        parsed_events.append(number)

    while len(queued_events):
      new_queued_events = []
      for event in queued_events:
        name,number,depend = event
        if depend in parsed_events:
          run_event(name,number)
          parsed_events.append(number)
        else:
          new_queued_events.append((name,number,depend))
      if len(queued_events) == len(new_queued_events):
        print("error parsing events, unsatisfiable dependency detected")
        exit(1)
      queued_events = new_queued_events
