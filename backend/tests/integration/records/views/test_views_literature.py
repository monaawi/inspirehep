# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CERN.
#
# inspirehep is free software; you can redistribute it and/or modify it under
# the terms of the MIT License; see LICENSE file for more details.

import json
from urllib.parse import urlencode

import mock
from flask import current_app
from helpers.providers.faker import faker
from invenio_accounts.testutils import login_user_via_session
from invenio_search import current_search

from inspirehep.accounts.roles import Roles
from inspirehep.records.errors import MaxResultWindowRESTError


def test_literature_search_application_json_get(
    api_client, db, es_clear, create_record, datadir
):
    data = {
        "$schema": "http://localhost:5000/schemas/records/hep.json",
        "control_number": 666,
        "document_type": ["article"],
        "titles": [{"title": "Partner walk again seek job."}],
    }

    record = create_record("lit", data=data)

    headers = {"Accept": "application/json"}
    expected_status_code = 200
    expected_data = {
        "$schema": "http://localhost:5000/schemas/records/hep.json",
        "control_number": 666,
        "document_type": ["article"],
        "titles": [{"title": "Partner walk again seek job."}],
        "citation_count": 0,
        "author_count": 0,
    }

    response = api_client.get("/literature", headers=headers)
    response_status_code = response.status_code
    response_data = json.loads(response.data)
    response_data_metadata = response_data["hits"]["hits"][0]["metadata"]

    assert expected_status_code == response_status_code
    assert expected_data == response_data_metadata


def test_literature_search_application_json_ui_get(
    api_client, db, es_clear, create_record
):
    data = {
        "control_number": 666,
        "titles": [{"title": "Partner walk again seek job."}],
        "preprint_date": "2019-07-02",
    }
    record = create_record("lit", data=data)
    headers = {"Accept": "application/vnd+inspire.record.ui+json"}
    expected_status_code = 200
    expected_data = {
        "citation_count": 0,
        "control_number": 666,
        "document_type": ["article"],
        "titles": [{"title": "Partner walk again seek job."}],
        "preprint_date": "2019-07-02",
        "date": "Jul 2, 2019",
    }

    response = api_client.get("/literature", headers=headers)
    response_status_code = response.status_code
    response_data = json.loads(response.data)
    response_data_metadata = response_data["hits"]["hits"][0]["metadata"]

    assert expected_status_code == response_status_code
    assert expected_data == response_data_metadata


def test_literature_application_json_get(api_client, db, create_record):
    record = create_record("lit")
    record_control_number = record["control_number"]

    expected_status_code = 200
    response = api_client.get("/literature/{}".format(record_control_number))
    response_status_code = response.status_code

    assert expected_status_code == response_status_code


def test_literature_application_json_put_without_token(api_client, db, create_record):
    record = create_record("lit")
    record_control_number = record["control_number"]

    expected_status_code = 401
    response = api_client.put("/literature/{}".format(record_control_number))
    response_status_code = response.status_code

    assert expected_status_code == response_status_code


def test_literature_application_json_delete_without_token(
    api_client, db, create_record
):
    record = create_record("lit")
    record_control_number = record["control_number"]

    expected_status_code = 401
    response = api_client.delete("/literature/{}".format(record_control_number))
    response_status_code = response.status_code

    assert expected_status_code == response_status_code


def test_literature_application_json_post_without_token(api_client, db):
    expected_status_code = 401
    response = api_client.post("/literature")
    response_status_code = response.status_code

    assert expected_status_code == response_status_code


def test_literature_application_json_put_with_token(
    api_client, db, create_record, create_user_and_token
):
    record = create_record("lit")
    record_control_number = record["control_number"]
    token = create_user_and_token()

    expected_status_code = 200

    headers = {"Authorization": "BEARER " + token.access_token}
    response = api_client.put(
        "/literature/{}".format(record_control_number), headers=headers, json=record
    )
    response_status_code = response.status_code

    assert expected_status_code == response_status_code


def test_literature_application_json_delete_with_token(
    api_client, db, create_record, create_user_and_token
):
    record = create_record("lit")
    record_control_number = record["control_number"]
    token = create_user_and_token()

    expected_status_code = 403

    headers = {"Authorization": "BEARER " + token.access_token}
    response = api_client.delete(
        "/literature/{}".format(record_control_number), headers=headers
    )
    response_status_code = response.status_code

    assert expected_status_code == response_status_code


def test_literature_application_json_post_with_token(
    api_client, db, create_user_and_token
):
    expected_status_code = 201
    token = create_user_and_token()
    headers = {"Authorization": "BEARER " + token.access_token}
    rec_data = faker.record("lit")

    response = api_client.post("/literature", headers=headers, json=rec_data)
    response_status_code = response.status_code

    assert expected_status_code == response_status_code


def test_literature_citations(api_client, db, es_clear, create_record):
    record = create_record("lit")
    record_control_number = record["control_number"]

    data = {
        "references": [
            {
                "record": {
                    "$ref": f"http://localhost:5000/api/literature/{record_control_number}"
                }
            }
        ],
        "publication_info": [{"year": 2019}],
    }
    record_citing = create_record("lit", data=data)
    record_citing_control_number = record_citing["control_number"]
    record_citing_titles = record_citing["titles"]

    expected_status_code = 200
    expected_data = {
        "metadata": {
            "citation_count": 1,
            "citations": [
                {
                    "control_number": record_citing_control_number,
                    "titles": record_citing_titles,
                    "earliest_date": "2019",
                    "publication_info": [{"year": 2019}],
                }
            ],
        }
    }

    response = api_client.get("/literature/{}/citations".format(record_control_number))
    response_status_code = response.status_code
    response_data = json.loads(response.data)

    assert expected_status_code == response_status_code
    assert expected_data == response_data


def test_literature_citations_with_superseded_citing_records(
    api_client, db, es_clear, create_record
):
    record = create_record("lit")
    record_control_number = record["control_number"]

    record_data = {
        "references": [
            {
                "record": {
                    "$ref": f"http://localhost:5000/api/literature/{record_control_number}"
                }
            }
        ],
        "related_records": [
            {
                "record": {"$ref": "https://link-to-commentor-record/1"},
                "relation": "commented",
            },
            {"record": {"$ref": "https://link-to-any-other-record/2"}},
        ],
        "publication_info": [{"year": 2019}],
    }
    record_citing = create_record("lit", data=record_data)
    record_citing_control_number = record_citing["control_number"]
    record_citing_titles = record_citing["titles"]

    superseded_record_data = {
        "references": [
            {
                "record": {
                    "$ref": f"http://localhost:5000/api/literature/{record_control_number}"
                }
            }
        ],
        "related_records": [
            {
                "record": {"$ref": "https://link-to-successor-record/2"},
                "relation": "successor",
            }
        ],
        "publication_info": [{"year": 2019}],
    }
    record_superseded = create_record("lit", data=superseded_record_data)
    record_superseded_control_number = record_superseded["control_number"]
    record_superseded_titles = record_superseded["titles"]

    expected_status_code = 200

    expected_count = 1
    expected_citation_citing = {
        "control_number": record_citing_control_number,
        "earliest_date": "2019",
        "publication_info": [{"year": 2019}],
        "titles": record_citing_titles,
    }

    response = api_client.get(f"/literature/{record_control_number}/citations")
    response_status_code = response.status_code
    response_data = json.loads(response.data)
    response_data_metadata = response_data["metadata"]

    assert expected_status_code == response_status_code
    assert expected_count == response_data_metadata["citation_count"]
    assert expected_citation_citing in response_data_metadata["citations"]


def test_literature_citations_with_non_citeable_collection(
    api_client, db, es_clear, create_record
):
    record = create_record("lit")
    record_control_number = record["control_number"]

    record_data = {
        "references": [
            {
                "record": {
                    "$ref": f"http://localhost:5000/api/literature/{record_control_number}"
                }
            }
        ],
        "related_records": [
            {
                "record": {"$ref": "https://link-to-commentor-record/1"},
                "relation": "commented",
            },
            {"record": {"$ref": "https://link-to-any-other-record/2"}},
        ],
        "publication_info": [{"year": 2019}],
    }
    create_record("lit", data=record_data)

    record_with_no_citable_collection_data = {
        "_collections": ["Fermilab"],
        "references": [
            {
                "record": {
                    "$ref": f"http://localhost:5000/api/literature/{record_control_number}"
                }
            }
        ],
        "publication_info": [{"year": 2019}],
    }
    record_with_no_citable_collection = create_record(
        "lit", data=record_with_no_citable_collection_data
    )

    expected_status_code = 200

    response = api_client.get(f"/literature/{record_control_number}/citations")
    response_status_code = response.status_code
    response_data = json.loads(response.data)

    assert expected_status_code == response_status_code
    assert record_with_no_citable_collection["control_number"] not in [
        record["control_number"] for record in response_data["metadata"]["citations"]
    ]


def test_literature_citations_empty(api_client, db, es_clear, create_record):
    record = create_record("lit")
    record_control_number = record["control_number"]

    response = api_client.get("/literature/{}/citations".format(record_control_number))
    response_status_code = response.status_code
    response_data = json.loads(response.data)

    expected_status_code = 200
    expected_data = {"metadata": {"citation_count": 0, "citations": []}}

    assert expected_status_code == response_status_code
    assert expected_data == response_data


def test_literature_citations_missing_pids(api_client, db, es_clear):
    missing_control_number = 1
    response = api_client.get("/literature/{}/citations".format(missing_control_number))
    response_status_code = response.status_code

    expected_status_code = 404

    assert expected_status_code == response_status_code


def test_literature_citations_with_size_bigger_than_maximum(
    api_client, db, es_clear, create_record
):
    record = create_record("lit", data=faker.record("lit"))
    headers = {"Accept": "application/json"}
    config = {"MAX_API_RESULTS": 3}
    with mock.patch.dict(current_app.config, config):
        response = api_client.get(
            f"/literature/{record['control_number']}/citations?size=5", headers=headers
        )
    response_status_code = response.status_code
    response_data = json.loads(response.get_data())
    expected_status_code = 400
    expected_response = MaxResultWindowRESTError().description
    assert expected_status_code == response_status_code
    assert expected_response == response_data["message"]


def test_literature_facets(api_client, db, es_clear, create_record):
    record = create_record("lit")

    response = api_client.get("/literature/facets")
    response_data = json.loads(response.data)
    response_status_code = response.status_code
    response_data_facet_keys = list(response_data.get("aggregations").keys())

    expected_status_code = 200
    expected_facet_keys = [
        "arxiv_categories",
        "author",
        "author_count",
        "doc_type",
        "earliest_date",
        "subject",
        "collaboration",
        "rpp",
    ]
    expected_facet_keys.sort()
    response_data_facet_keys.sort()
    assert expected_status_code == response_status_code
    assert expected_facet_keys == response_data_facet_keys
    assert len(response_data["hits"]["hits"]) == 0


def test_literature_cataloger_facets(
    api_client, db, create_record, create_user, es_clear
):
    user = create_user(role=Roles.cataloger.value)
    login_user_via_session(api_client, email=user.email)

    create_record("lit")

    response = api_client.get("/literature/facets")

    response_data = json.loads(response.data)
    response_status_code = response.status_code
    response_data_facet_keys = list(response_data.get("aggregations").keys())

    expected_status_code = 200
    expected_facet_keys = [
        "arxiv_categories",
        "author",
        "author_count",
        "doc_type",
        "earliest_date",
        "subject",
        "collaboration",
        "collection",
        "rpp",
    ]
    expected_facet_keys.sort()
    response_data_facet_keys.sort()
    assert expected_status_code == response_status_code
    assert expected_facet_keys == response_data_facet_keys
    assert len(response_data["hits"]["hits"]) == 0


def test_literature_facets_author_count_does_not_have_empty_bucket(
    api_client, db, es_clear
):
    response = api_client.get("/literature/facets")
    response_data = json.loads(response.data)
    author_count_agg = response_data.get("aggregations")["author_count"]
    assert author_count_agg["buckets"] == []


def test_literature_facets_author_count_returns_non_empty_bucket(
    api_client, db, es_clear, create_record, redis
):
    create_record(
        "lit",
        data={"authors": [{"full_name": "Harun Urhan"}, {"full_name": "John Doe"}]},
    )
    response = api_client.get("/literature/facets")
    response_data = json.loads(response.data)
    author_count_agg = response_data.get("aggregations")["author_count"]
    buckets = author_count_agg["buckets"]
    assert len(buckets) == 1
    assert buckets[0]["doc_count"] == 1


def test_literature_facets_doc_type_has_bucket_help(
    api_client, db, es_clear, create_record
):
    response = api_client.get("/literature/facets")
    response_data = json.loads(response.data)
    response_status_code = response.status_code
    response_data_facet_bucket_help = (
        response_data.get("aggregations").get("doc_type").get("meta").get("bucket_help")
    )

    expected_status_code = 200
    expected_text = (
        "Published papers are believed to have undergone rigorous peer review."
    )
    expected_link = "https://inspirehep.net/help/knowledge-base/faq/#faq-published"

    assert expected_status_code == response_status_code
    assert "published" in response_data_facet_bucket_help
    assert expected_text == response_data_facet_bucket_help["published"]["text"]
    assert expected_link == response_data_facet_bucket_help["published"]["link"]
    assert len(response_data["hits"]["hits"]) == 0


def test_literature_search_citation_count_filter(
    api_client, db, es_clear, create_record_factory
):
    paper_with_requested_number_of_citations = create_record_factory(
        "lit", data={"citation_count": 101}, with_indexing=True
    )

    papers_citation_count = [409, 83, 26]
    for count in papers_citation_count:
        create_record_factory("lit", data={"citation_count": count}, with_indexing=True)

    response = api_client.get("/literature?citation_count=101--102")

    response_data = json.loads(response.data)
    response_status_code = response.status_code
    assert response_status_code == 200
    assert response_data["hits"]["total"] == 1
    assert (
        response_data["hits"]["hits"][0]["metadata"]["control_number"]
        == paper_with_requested_number_of_citations.json["control_number"]
    )


def test_literature_search_refereed_filter(
    api_client, db, es_clear, create_record_factory
):
    refereed_paper = create_record_factory(
        "lit", data={"refereed": True}, with_indexing=True
    )

    create_record_factory("lit", data={"refereed": False}, with_indexing=True)

    response = api_client.get("/literature?refereed=true")
    response_data = json.loads(response.data)
    response_status_code = response.status_code
    assert response_status_code == 200
    assert response_data["hits"]["total"] == 1
    assert (
        response_data["hits"]["hits"][0]["metadata"]["control_number"]
        == refereed_paper.json["control_number"]
    )


def test_literature_search_citeable_filter(
    api_client, db, es_clear, create_record_factory
):
    citeable_paper = create_record_factory(
        "lit", data={"citeable": True}, with_indexing=True
    )

    create_record_factory("lit", data={"citeable": False}, with_indexing=True)

    response = api_client.get("/literature?citeable=true")
    response_data = json.loads(response.data)
    response_status_code = response.status_code
    assert response_status_code == 200
    assert response_data["hits"]["total"] == 1
    assert (
        response_data["hits"]["hits"][0]["metadata"]["control_number"]
        == citeable_paper.json["control_number"]
    )


def test_literature_citation_annual_summary(
    api_client, db, es_clear, create_record, redis
):
    author = create_record("aut", faker.record("aut"))
    authors = [
        {
            "record": {
                "$ref": f"http://localhost:8000/api/authors/{author['control_number']}"
            },
            "full_name": author["name"]["value"],
        }
    ]
    data = {"authors": authors, "preprint_date": "2010-01-01", "citeable": True}

    expected_response = {"value": {"2010": 1}}
    literature = create_record("lit", faker.record("lit", data=data))
    create_record(
        "lit",
        faker.record(
            "lit",
            literature_citations=[literature["control_number"]],
            data={"preprint_date": "2010-01-01"},
        ),
    )
    literature.index(delay=False)  # Index again after citation was added

    request_param = {
        "author": literature.serialize_for_es()["facet_author_name"][0],
        "facet_name": "citations-by-year",
    }
    current_search.flush_and_refresh("records-hep")

    response = api_client.get(f"/literature/facets/?{urlencode(request_param)}")

    assert response.json["aggregations"]["citations_by_year"] == expected_response


def test_literature_citation_annual_summary_for_many_records(
    api_client, db, es_clear, create_record
):
    literature1 = create_record("lit", faker.record("lit"))
    create_record(
        "lit",
        faker.record(
            "lit",
            literature_citations=[literature1["control_number"]],
            data={"preprint_date": "2010-01-01"},
        ),
    )
    create_record(
        "lit",
        faker.record(
            "lit",
            literature_citations=[literature1["control_number"]],
            data={"preprint_date": "2013-01-01"},
        ),
    )
    literature2 = create_record("lit", faker.record("lit"))
    create_record(
        "lit",
        faker.record(
            "lit",
            literature_citations=[literature2["control_number"]],
            data={"preprint_date": "2012-01-01"},
        ),
    )
    create_record(
        "lit",
        faker.record(
            "lit",
            literature_citations=[literature2["control_number"]],
            data={"preprint_date": "2013-01-01"},
        ),
    )
    literature1.index(delay=False)
    literature2.index(delay=False)
    request_param = {"facet_name": "citations-by-year"}

    current_search.flush_and_refresh("records-hep")

    response = api_client.get(f"/literature/facets/?{urlencode(request_param)}")

    expected_response = {"value": {"2013": 2, "2012": 1, "2010": 1}}
    assert response.json["aggregations"]["citations_by_year"] == expected_response


def test_literature_search_user_does_not_get_fermilab_collection(
    api_client, db, es_clear, create_record, datadir
):
    data = {
        "$schema": "http://localhost:5000/schemas/records/hep.json",
        "_collections": ["Fermilab"],
        "control_number": 666,
        "document_type": ["article"],
        "titles": [{"title": "Partner walk again seek job."}],
    }

    create_record("lit", data=data)

    expected_status_code = 200

    response = api_client.get("/literature")
    response_status_code = response.status_code
    response_data = json.loads(response.data)

    assert response_data["hits"]["total"] == 0
    assert expected_status_code == response_status_code


def test_literature_search_cataloger_gets_fermilab_collection(
    api_client, db, es_clear, create_record, datadir, create_user
):
    data = {
        "$schema": "http://localhost:5000/schemas/records/hep.json",
        "_collections": ["Fermilab"],
        "control_number": 666,
        "document_type": ["article"],
        "titles": [{"title": "Partner walk again seek job."}],
    }
    user = create_user(role=Roles.cataloger.value)
    login_user_via_session(api_client, email=user.email)

    record = create_record("lit", data=data)

    expected_status_code = 200
    expected_data = {
        "$schema": "http://localhost:5000/schemas/records/hep.json",
        "_collections": ["Fermilab"],
        "control_number": 666,
        "document_type": ["article"],
        "titles": [{"title": "Partner walk again seek job."}],
        "citation_count": 0,
        "author_count": 0,
    }

    response = api_client.get("/literature")
    response_status_code = response.status_code
    response_data = json.loads(response.data)
    assert response_data["hits"]["total"] == 1

    response_data_metadata = response_data["hits"]["hits"][0]["metadata"]

    assert expected_status_code == response_status_code
    assert expected_data == response_data_metadata


def test_literature_search_permissions(
    api_client, db, es_clear, create_record, datadir, create_user, logout
):
    create_record("lit", data={"_collections": ["Fermilab"]})
    rec_literature = create_record("lit", data={"_collections": ["Literature"]})

    response = api_client.get("/literature")
    response_data = json.loads(response.data)
    assert response_data["hits"]["total"] == 1
    assert (
        response_data["hits"]["hits"][0]["metadata"]["control_number"]
        == rec_literature["control_number"]
    )

    user = create_user(role=Roles.cataloger.value)
    login_user_via_session(api_client, email=user.email)

    response = api_client.get("/literature")
    response_data = json.loads(response.data)
    assert response_data["hits"]["total"] == 2

    logout(api_client)

    response = api_client.get("/literature")
    response_data = json.loads(response.data)
    assert response_data["hits"]["total"] == 1
    assert (
        response_data["hits"]["hits"][0]["metadata"]["control_number"]
        == rec_literature["control_number"]
    )


def test_literature_hidden_collection_as_anonymous_user(api_client, db, create_record):
    expected_status_code = 401
    rec = create_record("lit", data={"_collections": ["Fermilab"]})
    response = api_client.get(f"/literature/{rec['control_number']}")
    assert response.status_code == expected_status_code


def test_literature_hidden_collection_as_cataloger(
    api_client, db, create_record, create_user
):
    expected_status_code = 200
    rec = create_record("lit", data={"_collections": ["Fermilab"]})

    user = create_user(role=Roles.cataloger.value)
    login_user_via_session(api_client, email=user.email)

    response = api_client.get(f"/literature/{rec['control_number']}")
    assert response.status_code == expected_status_code


def test_literature_hidden_collection_as_logged_in_user_not_cataloger(
    api_client, db, create_record, create_user
):
    expected_status_code = 403
    rec = create_record("lit", data={"_collections": ["Fermilab"]})

    user = create_user()
    login_user_via_session(api_client, email=user.email)

    response = api_client.get(f"/literature/{rec['control_number']}")
    assert response.status_code == expected_status_code
