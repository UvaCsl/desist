In silico clinical trial workflow
=================================

Setup
-----

Start with initializing all git submodules in the following way:

```
git submodule update --init --recursive
```

Permission for certain modules can be acquired through
v.w.azizitarksalooyeh@uva.nl

Then dependencies need to be installed, on ubuntu these are (usually)

```
apt-get install python3-openpyxl xsltproc python3-lxml
```

The software modules need to be compiled (software/1d_blood_flow and
software/darcy_multi-comp) see their READMES.

Running
-------

Edit the `workflow/variables.xml` the root and config file location should be
updated correctly

Load `workflow/Main.t2flow` into taverna and run it.

