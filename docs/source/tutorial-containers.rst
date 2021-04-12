Creating containers
===================

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

    # cleaning up Singularity containers
    rm /path/to/containers/*.sif
