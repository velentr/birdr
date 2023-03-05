;;; SPDX-FileCopyrightText: 2023 Brian Kubisiak <brian@kubisiak.com>
;;;
;;; SPDX-License-Identifier: GPL-3.0-only

(use-modules (gnu packages check)
             (gnu packages databases)
             (gnu packages python)
             (gnu packages python-check)
             (gnu packages python-xyz)
             (gnu packages sqlite))

(packages->manifest
 (list python
       python-black
       python-coverage
       python-ipython
       python-mypy
       python-pylint
       python-pytest
       python-pytest-black
       python-pytest-cov
       python-pytest-mypy
       python-rich
       python-sqlalchemy
       python-textual
       sqlite))
