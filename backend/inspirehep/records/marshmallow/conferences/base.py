# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CERN.
#
# inspirehep is free software; you can redistribute it and/or modify it under
# the terms of the MIT License; see LICENSE file for more details.

import pycountry
import structlog
from marshmallow import fields

from inspirehep.records.marshmallow.base import RecordBaseSchema
from inspirehep.records.marshmallow.conferences.common.proceeding_info_item import (
    ProceedingInfoItemSchemaV1,
)

LOGGER = structlog.getLogger()


class ConferencesRawSchema(RecordBaseSchema):
    # These are attributes on a mixin that is used by ConferenceRecord class
    # therefore can't be included by default RecordBaseSchema.include_original_fields
    number_of_contributions = fields.Raw()
    proceedings = fields.Nested(ProceedingInfoItemSchemaV1, many=True, dump_only=True)
    addresses = fields.Method("get_addresses")

    def get_addresses(self, record):
        addresses = record.get("addresses", [])
        for address in addresses:
            if "country_code" in address:
                try:
                    address["country"] = pycountry.countries.get(
                        alpha_2=address["country_code"]
                    ).name
                except KeyError:
                    LOGGER.warning(
                        "Wrong Country code",
                        country_code=address["country_code"],
                        recid=record.get("control_number"),
                    )
        return addresses


class ConferencesAdminSchema(ConferencesRawSchema):
    pass


class ConferencesPublicSchema(ConferencesRawSchema):
    class Meta:
        exclude = ["_private_notes", "_collections"]
