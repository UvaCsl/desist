Place clot software module
--------------------------

The place clot software module can be found as a seperate git repository at
`<https://gitlab.computationalscience.nl/insist/place_clot>`_ or as a submodule
from `<https://gitlab.computationalscience.nl/insist/in-silico-trial>`_ .


Files and Modules
-----------------

Within this module two files are present and one submodule. The submodule is the
:ref:`eventmodule` and is used in the :ref:`API` file. The two files are the
:ref:`API` file and the :ref:`docker` file. 

.. _API:

API.py
------

The API.py file is based on the :any:`EventHandler <eventmodule.EventHandler>` class

.. autoclass:: API.API
  :show-inheritance:
  :members:

.. _docker:

Dockerfile
----------

The dockerfile is used to specify an environment with which to build the
container. See the example from the place_clot package below:

::

  # What is this container based on
  FROM ubuntu:18.04
  # Install the dependencies
  RUN apt-get update && apt-get install -y python3 python3-lxml
  # Copy everything from this folder to /app in the container
  COPY . /app

  # Set the default entry point to call the API
  ENTRYPOINT ["python3", "/app/API.py"]

Structure of events
-------------------

Every module should handle an event. The :ref:`eventmodule` class is written to
hide the complexities of the pipline for the module. the :ref:`API` file is used
to implement this. There are three important objects that you need to know about
when implementing the API.

- **self.patient:** a structure containing the information about the patient.



Testing with docker image
-------------------------

To get started with running a software module it is important to first set up a
docker image. To do this first install docker:
`<https://www.docker.com/get-started>`_ 

then navigate to the folder of your software module ``software/place_clot`` and
execute ``sudo docker build .``. This should produce some output and create your docker
image. Docker images are identified by a hash which should be outputted on the
last line of the ``build`` command. You can also try to find the correct image by
executing ``sudo docker image list`` or rerunning the ``build`` command. 

When you have created the image it is time to start testing your software! When
developing it is easiest to create a terminal within the docker like so: 
``sudo docker run -it --entrypoint /bin/bash <container_hash>``. Don't be confused!
You are now inside the docker image which is like a tiny OS. You can try to run
commands like ``python3 API.py handle_example``. However, any change you make will
be lost when you exit the container!

In the in silico clinical trial the folder with patient info will be mounted at
``/patient``. To mount this folder you can use the ``-v`` directive of docker
this will result in the command

::

  sudo docker run -v `pwd`/patient:patient -it --entrypoint /bin/bash <container>


Where ```pwd``` expands to the current directory. When executing this command
the ``/patient`` folder will be available within the docker container. This
folder is also present outside the container and thus any changes made within
this folder are persistent!

We can use the same docker behaviour to edit/debug/test our software modules.
Normally the full module folder is placed inside the container as the ``/app``
directory. However we can mount our development version `over` the container
version with the ``-v`` flag as well. So whenever you have a working container environment
it is not necessary to run ``docker build`` after each software module update. 

To mount the software module folder simply specify an extra ``-v`` flag:

::

  sudo docker run -v `pwd`/patient:patient -v `pwd`:/app -it --entrypoint /bin/bash <container>

This command assumes that your current working directory is the software module
directory (``software/place_clot`` for example for the place clot module)

Testing events within the docker container
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This part assumes you have run your docker container as specified above, and
that you are currently have a terminal into the container open.

An event will always be passed to the software with the following command:

::
  
  python3 /app/API.py handle_event --event <event_number> --patient <xml file>

For the example event handler you can set the variables in :ref:`API` and you don't have
to specify them on the command line (but you could!). See command below:

::

  python3 /app/API.py handle_example 

Within the place_clot software module this will ultimately create a clot_present
file in the ``/patient`` directory. (Which then is present outside the container
as well).
