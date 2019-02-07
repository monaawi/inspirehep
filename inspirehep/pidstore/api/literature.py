# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CERN.
#
# inspirehep is free software; you can redistribute it and/or modify it under
# the terms of the MIT License; see LICENSE file for more details.

from __future__ import absolute_import, division, print_function

from flask import current_app
from six.moves.urllib.parse import urlsplit

from ..minters.arxiv import ArxivMinter
from ..minters.control_number import LiteratureMinter
from ..minters.doi import DoiMinter
from .base import PidStoreBase


class PidStoreLiterature(PidStoreBase):

    minters = [LiteratureMinter, ArxivMinter, DoiMinter]
