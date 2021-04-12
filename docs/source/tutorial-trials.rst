Evaluating *in silico* trials
=============================

.. code-block:: bash

    # the name of the trial directory
    trial=demo-trial

    # creating a trial with `num` patients
    desist trial create $trial -n $num

    # creating a trial from a in/exclusion file
    desist trial create $trial -c criteria.yml

    # printing the commands to run the trial without evaluating
    desist trial run $trial -x

    # running the trial sequentially
    desist trial run $trial

    # running the trial in parallel
    desist trial run $trial --parallel | parallel
