Event and pipeline specifications
=================================

The ``desist`` tool helps to create *in silico* simulation pipelines from a set
of discrete events implemented in individual, containerised environments. Each
of the simulations provides their own implementation of the ``API`` interface,
guaranteeing the interface functions are present for embedding in a *in silico*
pipeline specification.

Event specification
-------------------

In ``desist`` the user is given full control on the specifications of the event
ordering. To provide this ordering, the user can provide the ``events`` and
``labels`` keys in the ``trial.yml`` (or ``criteria.yml``) file. With these
keys, the order of event simulations are fully defined and linked to the
corresponding container identifiers.

The ``events`` specifications considers the following format:

.. code-block:: yaml

   events:
   - event: baseline
     models:
     - label: container-a
     - label: container-b
   - event: stroke
     models:
     - label: container-a
     - label: container-c
       key: value

Thus, the ``events`` key contains an (ordered) list of dictionaries containing
the ``event: name`` and ``models: <list>`` keys. The first specifies the event's
name. Most often this is merely used as visual reference, although the event
name specification can of course be used to create, for instance, directory
structures or file specifiers. The (ordered) list of dictionaries under the
``models`` key provides the (ordered) set of models to be evaluated for the
current event. Depending on the container implementation, there might be
additional ``key:value`` pairs provided here. A common use-case for such keys is
to identify additional simulation parameters that might not be embedded directly
into the container, e.g. convergence tolerances, simulation types, or boundary
conditions.

``desist`` derives the order of the simulation pipeline by traversing the events
and their nested ``event`` specifications in the user-specified order. This
initialises the full simulation pipeline, which is assumed *constant* throughout
the duration of the call to ``desist``. Thus, modifying these orderings will
*not* influence the order in which these simulations are evaluated.

When ``desist`` invokes an simulation event the provided container label is
first translated using the user-provided ``labels`` dictionary included in the
``patient.yml`` file. This dictionary provides the optional to introduce an
additional mapping from the label specified in the ``label`` key to the final
container ID that is invoked. This can be useful when debugging different
variations of the same container, providing a way for the user to quickly
change which container is ultimately invoked.
