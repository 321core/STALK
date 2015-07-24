# -*- coding: utf-8 -*-
# conf.py

import os

base = os.path.dirname(os.path.abspath(__file__))

exec(open(base + os.path.sep + '../conf/settings.conf', 'r').read())
