# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# inspirehep is free software; you can redistribute it and/or modify it under
# the terms of the MIT License; see LICENSE file for more details.
from copy import deepcopy

from helpers.utils import es_search
from invenio_search import current_search
from marshmallow import utils

from inspirehep.search.api import SeminarsSearch


def test_index_seminars_record(base_app, es_clear, db, datadir, create_record):
    record = create_record("sem")

    expected_count = 1
    expected_metadata = deepcopy(record)
    expected_metadata["_created"] = utils.isoformat(record.created)
    expected_metadata["_updated"] = utils.isoformat(record.updated)

    response = es_search("records-seminars")

    assert response["hits"]["total"]["value"] == expected_count
    assert response["hits"]["hits"][0]["_source"] == expected_metadata


def test_indexer_deletes_record_from_es(es_clear, db, datadir, create_record):
    record = create_record("sem")

    record["deleted"] = True
    record.index(delay=False)
    current_search.flush_and_refresh("records-seminars")

    expected_records_count = 0

    record_lit_es = SeminarsSearch().get_record(str(record.id)).execute().hits
    assert expected_records_count == len(record_lit_es)
