In silico trial
===============

This section is about setting up the workflow for the in silico trial. However
this is not necessary for creating a software module.

If your network admin does not allow ssh/tcp access to port 1022 then please
replace the ``.gitmodules`` file with ``.gitmodules_https`` which can also be
found in the repository.

To get started clone the git repository and all the submodules:

::
  
  git clone https://gitlab.computationalscience.nl/insist/in-silico-trial.git
  cd in-silico-trial
  #The next step is optional if your institute has very restrictive firewalls
  mv .gitmodules_https .gitmodules #use https instead of ssh over port 1022
  git submodule update --init --recursive


We have included some scripts to automatically construct and run the workflow,
the only requirement is having docker installed!

::
  
  #Build all available modules
  ./scripts/create_containers.sh


::

  #Run the pipeline
  ./scripts/run_in_silico_trial.sh scripts/variables.xml trial 1
