In silico trial
===============

This section is about setting up the workflow for the in silico trial. However
this is not necessary for creating a software module.

To get started clone the git repository and all the submodules:

::
  
  git clone https://gitlab.computationalscience.nl/insist/in-silico-trial.git
  cd in-silico-trial
  git submodule update --init --recursive


We have included some scripts to automatically construct and run the workflow,
the only requirement is having docker installed!

::
  
  #Build all available modules
  ./scripts/create_containers.sh


::

  #Run the pipeline
  ./scripts/run_in_silico_trial.sh scripts/variables.xml trial 1
