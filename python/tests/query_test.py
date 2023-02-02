def test_basic_query(client):
    response = client.post(
        "/query",
        json={
            "sql": "SELECT * FROM CUSTOMER ORDER BY created_at ASC LIMIT 1",
            "data_source_id": 1,
        },
    )

    # TODO this will be brittle, but I'm also curious when it will break
    assert response.json == {
        "results": [
            {
                "ACCEPTS_MARKETING": None,
                "ACCEPTS_MARKETING_UPDATED_AT": None,
                "CAN_DELETE": True,
                "CREATED_AT": "Fri, 22 Feb 2019 09:14:18 GMT",
                "CURRENCY": None,
                "EMAIL": "sam@3dcart.com",
                "EMAIL_MARKETING_CONSENT_CONSENT_UPDATED_AT": "Fri, 22 Feb 2019 " "09:14:18 GMT",
                "EMAIL_MARKETING_CONSENT_OPT_IN_LEVEL": None,
                "EMAIL_MARKETING_CONSENT_STATE": "SUBSCRIBED",
                "FIRST_NAME": "Samantha",
                "ID": 1305140297787,
                "LAST_NAME": "Harris",
                "LIFETIME_DURATION": "almost 4 years",
                "MARKETING_OPT_IN_LEVEL": None,
                "METAFIELD": None,
                "MULTIPASS_IDENTIFIER": None,
                "NOTE": "",
                "ORDERS_COUNT": 0,
                "PHONE": "+18004708730",
                "STATE": "INVITED",
                "TAX_EXEMPT": False,
                "TOTAL_SPENT": 0.0,
                "UPDATED_AT": "Fri, 27 Aug 2021 23:19:26 GMT",
                "VERIFIED_EMAIL": True,
                "_FIVETRAN_DELETED": False,
                "_FIVETRAN_SYNCED": "Mon, 23 Jan 2023 21:44:22 GMT",
            }
        ],
        "sql": "SELECT * FROM CUSTOMER ORDER BY created_at ASC LIMIT 1",
    }
