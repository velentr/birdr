;;; SPDX-FileCopyrightText: 2023 Brian Kubisiak <brian@kubisiak.com>
;;;
;;; SPDX-License-Identifier: GPL-3.0-only

(use-modules (gnu packages check)
             (gnu packages databases)
             (gnu packages python)
             (gnu packages python-check)
             (gnu packages python-xyz)
             (gnu packages sqlite)
             (guix build-system pyproject)
             (guix gexp)
             ((guix licenses) #:prefix license:)
             (guix packages))

(package
 (name "birdr")
 (version "0.0.0")
 (source (local-file "." "birdr" #:recursive? #t))
 (build-system pyproject-build-system)
 (arguments
  (list #:tests? #false))
 (native-inputs
  ;; used for development
  (list python-black python-ipython python-mypy python-pylint sqlite))
 (propagated-inputs
  (list python-click python-rich python-sqlalchemy))
 (synopsis "Record and track bird sightings and checklists")
 (description "Command-line tool for tracking bird sightings and checklists in a
database.")
 (home-page "https://github.com/velentr/birdr")
 (license license:gpl3))
