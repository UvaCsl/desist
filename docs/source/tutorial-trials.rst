Evaluating *in silico* trials
=============================

The following code block illustrates how to create, run, and analyse trials
using ``desist``. To run trials in parallel you can either use the ``parallel``
executable or use parallelisation functionality through the ``QCG-PilotJob``
runner. Both provide the ability to run trials in a massively parallel fashion.
Note: when running on large ``SLURM``-based allocations using ``parallel`` it
might be required to forward the current environment to all parts of the
allocation. Depending on the cluster configuration, this process might be
opaque and error-prone. A way to avoid these errors is to opt for the
``QCG-PilotJob`` based runner through the ``--qcg`` flag, which automatically
take over the resource management within the allocation.

.. code-block:: bash

    # the name of the trial directory
    trial=demo-trial

    # creating a trial with `num` patients
    desist trial create $trial -n $num

    # creating a trial from a in/exclusion file
    desist trial create $trial -c criteria.yml

    # creating a trial using Singularity containers
    desist trial create $trial -c criteria.yml -s $HOME/containers

    # printing the commands to run the trial without evaluating
    desist trial run $trial -x

    # running the trial sequentially
    desist trial run $trial

    # running the trial in parallel
    desist trial run $trial --parallel | parallel

    # running the trial in parallel using the QCG-PilotJob runner
    desist trial run $trial --qcg

    # generating trial outcome
    desist trial outcome $trial
