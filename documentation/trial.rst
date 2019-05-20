In silico trial
===============

This section is about setting up the workflow for the in silico trial. However
this is not necessary for creating a software module.

To get started clone the git repository and all the submodules:

::
  
  git clone https://gitlab.computationalscience.nl/insist/in-silico-trial.git
  cd in-silico-trial
  git submodule update --init --recursive

The next step is creating the docker containers for the various software
packages:

::
  
  #Do this for each software module
  cd software/place_clot
  docker build .

.. todo::
  Make a docker container for the whole trial as well so that we can finish
  writing this documentation
   
