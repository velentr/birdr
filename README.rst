.. SPDX-FileCopyrightText: 2023 Brian Kubisiak <brian@kubisiak.com>

   SPDX-License-Identifier: CC0-1.0

=====
birdr
=====

Record and track bird sightings and checklists.

``birdr`` is still under active development and very unstable; use with
caution.

===========
Development
===========

Running scripts (including the ``birdr`` executable) should be prefixed with
``./pre-inst-env.sh`` from the top-level directory. To setup an initial virtual
environment with the required packages::

 $ ./pre-inst-env.sh setup

The same command can be run to upgrade existing packages or install new ones
when ``requirements.txt`` gets updated. Once the environment is set up, you can
run ``birdr`` and (for example) check which commands and options are available::

 $ ./pre-inst-env.sh birdr --help
