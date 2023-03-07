#!/bin/sh

# SPDX-FileCopyrightText: 2023 Brian Kubisiak <brian@kubisiak.com>
#
# SPDX-License-Identifier: GPL-3.0-only

if [ -f venv/bin/activate ]; then
	. venv/bin/activate
fi

export PATH="${PATH}:./scripts"
export PYTHONPATH=.
export PYTHONDONTWRITEBYTECODE=1

exec "$@"
