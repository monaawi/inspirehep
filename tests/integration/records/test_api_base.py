# -*- coding: utf-8 -*-
#
# This file is part of INSPIRE.
# Copyright (C) 2014-2018 CERN.
#
# INSPIRE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# INSPIRE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with INSPIRE. If not, see <http://www.gnu.org/licenses/>.
#
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization
# or submit itself to any jurisdiction.

"""INSPIRE module that adds more fun to the platform."""

from __future__ import absolute_import, division, print_function

import pytest
from helpers.providers.faker import faker
from invenio_pidstore.models import PersistentIdentifier, RecordIdentifier
from invenio_records.models import RecordMetadata

from inspirehep.records.api import InspireRecord
from inspirehep.records.api.base import InspireQueryBuilder


def test_query_builder_returns_not_deleted(base_app, db, create_record):
    create_record("lit", data={"deleted": True})
    not_deleted_record = create_record("lit", data={"deleted": False})

    not_deleted_records = InspireQueryBuilder().not_deleted().query().all()

    assert len(not_deleted_records) == 1
    assert not_deleted_records[0].json == not_deleted_record.json


def test_query_builder_returns_by_collections(base_app, db, create_record):
    literature_record = create_record("lit", data={"_collections": ["Literature"]})
    create_record("lit", data={"_collections": ["Other"]})

    literature_records = (
        InspireQueryBuilder().by_collections(["Literature"]).query().all()
    )

    assert len(literature_records) == 1
    assert literature_records[0].json == literature_record.json


def test_query_builder_returns_no_duplicates(base_app, db, create_record):
    create_record("lit", with_pid=False, data={"control_number": 1})
    create_record("lit", with_pid=False, data={"control_number": 1})
    create_record("lit", with_pid=False, data={"control_number": 1})

    literature_records = InspireQueryBuilder().no_duplicates().query().all()

    assert len(literature_records) == 1


# FIXME: maybe too brittle, need to find another way to test chainability
def test_query_builder_returns_no_duplicated_not_deleted_by_collections(
    base_app, db, create_record
):
    record = create_record(
        "lit",
        data={"deleted": False, "_collections": ["Literature"], "control_number": 1},
    )
    create_record(
        "lit", data={"deleted": False, "_collections": ["Other"], "control_number": 2}
    )
    create_record(
        "lit",
        with_pid=False,
        data={"deleted": False, "_collections": ["Literature"], "control_number": 1},
    )
    create_record("lit", data={"deleted": True, "_collections": ["Literature"]})

    records = (
        InspireQueryBuilder()
        .by_collections(["Literature"])
        .not_deleted()
        .no_duplicates()
        .query()
        .all()
    )

    assert len(records) == 1
    assert records[0].json == record.json


def test_base_get_record(base_app, db, create_record):
    record = create_record("lit")

    expected_record = InspireRecord.get_record(record.id)

    assert expected_record == record.json


def test_base_get_records(base_app, db, create_record):
    records = [create_record("lit"), create_record("lit"), create_record("lit")]
    record_uuids = [record.id for record in records]

    expected_records = InspireRecord.get_records(record_uuids)

    for record in records:
        assert record.json in expected_records


def test_get_uuid_from_pid_value(base_app, db, create_record):
    record = create_record("lit")
    record_uuid = record.id
    record_pid_type = record._persistent_identifier.pid_type
    record_pid_value = record._persistent_identifier.pid_value

    expected_record_uuid = InspireRecord.get_uuid_from_pid_value(
        record_pid_value, pid_type=record_pid_type
    )

    assert expected_record_uuid == record_uuid


def test_soft_delete_record(base_app, db, create_record):
    record_factory = create_record("lit")
    record_uuid = record_factory.id
    record = InspireRecord.get_record(record_uuid)
    record.delete()
    record_pid = PersistentIdentifier.query.filter_by(
        object_uuid=record.id
    ).one_or_none()

    assert "deleted" in record
    assert record_pid is None


def test_hard_delete_record(base_app, db, create_record, create_pidstore):
    record_factory = create_record("lit")
    create_pidstore(record_factory.id, "pid1", faker.control_number())
    create_pidstore(record_factory.id, "pid2", faker.control_number())
    create_pidstore(record_factory.id, "pid3", faker.control_number())

    pid_value_rec = record_factory.json["control_number"]
    record_uuid = record_factory.id
    record = InspireRecord.get_record(record_uuid)
    record_pids = PersistentIdentifier.query.filter_by(object_uuid=record.id).all()

    assert 4 == len(record_pids)
    assert record_factory.json == record

    record.hard_delete()
    record = RecordMetadata.query.filter_by(id=record_uuid).one_or_none()
    record_pids = PersistentIdentifier.query.filter_by(
        object_uuid=record_uuid
    ).one_or_none()
    record_identifier = RecordIdentifier.query.filter_by(
        recid=pid_value_rec
    ).one_or_none()

    assert record is None
    assert record_pids is None
    assert record_identifier is None


def test_redirect_records(base_app, db, create_record):
    current_factory = create_record("lit")
    other_factory = create_record("lit")

    current = InspireRecord.get_record(current_factory.id)
    other = InspireRecord.get_record(other_factory.id)

    current.redirect(other)

    current_pids = PersistentIdentifier.query.filter(
        PersistentIdentifier.object_uuid == current_factory.id
    ).all()
    other_pid = PersistentIdentifier.query.filter(
        PersistentIdentifier.object_uuid == other_factory.id
    ).one()

    assert current["deleted"] is True
    for current_pid in current_pids:
        assert current_pid.get_redirect() == other_pid
