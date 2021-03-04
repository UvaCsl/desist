Evaluating *in silico* trials
=============================

.. code-block:: bash

    # the name of the trial directory
    trial=demo-trial

    # creating a trial with `num` patients
    isct trial create $trial -n $num

    # creating a trial from a in/exclusion file
    isct trial create $trial -c criteria.yml

    # printing the commands to run the trial without evaluating
    isct trial run $trial -x

    # running the trial sequentially
    isct trial run $trial

    # running the trial in parallel
    isct trial run $trial --parallel | parallel
