Creating containers
===================

Although containers can be created with Docker or Singularity directly,
``desist`` provides a wrapper command ``desist container create`` that wraps
calls to Docker or Singularity to create containers. The following code snippets
illustrate how the create and remove these containers using ``desist``.

.. code-block:: bash

    # a directory containing a `Dockerfile` and `singularity.def`
    directory=/path/to/simulation/directory

    # docker containers
    desist container create $directory

    # singularity images are stored on disk as `*.sif` files
    # this container variable points to the desired location
    containers=/path/to/containers/

    # singularity containers
    desist container create $directory -s $containers

.. code-block:: bash

    # cleaning up Docker containers
    docker image prune  # remove unused images
    docker image rm ... # remove specific image
    docker system prune # remove unsused data (all data!)

    # cleaning up all Singularity containers
    rm /path/to/containers/*.sif
