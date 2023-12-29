from app.tests.fixtures.reorder_api import (
    es_data_payload_3,
    es_data_payload_10,
    es_data_payload_corporate,
)

payload_1 = {
    "sku_info": {
        "124033": {
            "ordered_at": 1632992514.0,
            "quantity": "2",
            "created_at": "2021-09-30 09:01:54",
        },
    },
    "user_id": "***REMOVED***",
    "order_id": "1201",
}

payload_2 = {
    "sku_info": {
        "124033": {
            "ordered_at": 1632992514.0,
            "quantity": "2",
            "created_at": "2021-09-30 09:01:54",
        },
        "370717": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
    },
    "user_id": "***REMOVED***",
    "order_id": "1202",
}

payload_3 = {
    "sku_info": {
        "124033": {
            "ordered_at": 1632992514.0,
            "quantity": "2",
            "created_at": "2021-09-30 09:01:54",
        },
        "370717": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
        "470414": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
    },
    "user_id": "***REMOVED***",
    "order_id": "1203",
}

payload_4 = {
    "sku_info": {
        "124033": {
            "ordered_at": 1632992514.0,
            "quantity": "2",
            "created_at": "2021-09-30 09:01:54",
        },
        "370717": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
        "470414": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
        "515387": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
    },
    "user_id": "***REMOVED***",
    "order_id": "1204",
}

payload_5 = {
    "sku_info": {
        "124033": {
            "ordered_at": 1632992514.0,
            "quantity": "2",
            "created_at": "2021-09-30 09:01:54",
        },
        "370717": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
        "470414": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
        "515387": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
        "587736": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
    },
    "user_id": "***REMOVED***",
    "order_id": "1205",
}

payload_6 = {
    "sku_info": {
        "124033": {
            "ordered_at": 1632992514.0,
            "quantity": "2",
            "created_at": "2021-09-30 09:01:54",
        },
        "370717": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
        "470414": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
        "515387": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
        "587736": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
        "604424": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
    },
    "user_id": "***REMOVED***",
    "order_id": "1206",
}

payload_7 = {
    "sku_info": {
        "124033": {
            "ordered_at": 1632992514.0,
            "quantity": "2",
            "created_at": "2021-09-30 09:01:54",
        },
        "370717": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
        "470414": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
        "515387": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
        "587736": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
        "604424": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
        "327460": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
    },
    "user_id": "***REMOVED***",
    "order_id": "1207",
}

payload_8 = {
    "sku_info": {
        "124033": {
            "ordered_at": 1632992514.0,
            "quantity": "2",
            "created_at": "2021-09-30 09:01:54",
        },
        "370717": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
        "470414": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
        "515387": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
        "587736": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
        "604424": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
        "327460": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
        "138818": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
    },
    "user_id": "***REMOVED***",
    "order_id": "1208",
}

payload_9 = {
    "sku_info": {
        "124033": {
            "ordered_at": 1632992514.0,
            "quantity": "2",
            "created_at": "2021-09-30 09:01:54",
        },
        "370717": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
        "470414": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
        "515387": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
        "587736": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
        "604424": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
        "138818": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
        "327460": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
        "326130": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
    },
    "user_id": "***REMOVED***",
    "order_id": "1209",
}

payload_10 = {
    "sku_info": {
        "124033": {
            "ordered_at": 1632992514.0,
            "quantity": "2",
            "created_at": "2021-09-30 09:01:54",
        },
        "370717": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
        "470414": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
        "515387": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
        "587736": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
        "604424": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
        "138818": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
        "327460": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
        "326130": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
        "148015": {
            "ordered_at": 1632992514.0,
            "quantity": "4",
            "created_at": "2021-09-30 09:01:54",
        },
    },
    "user_id": "***REMOVED***",
    "order_id": "1210",
}

# (payload, type_name, page, per_page)
rules = [
    (payload_3, es_data_payload_3, "minimal", 1, 2),
    (payload_3, es_data_payload_3, "minimal", 0, 2),
    (payload_3, es_data_payload_3, "minimal", 2, 1),
]

rules_2 = [
    (payload_3, es_data_payload_3, "detailed", 1, 2),
    (payload_3, es_data_payload_3, "detailed", 0, 2),
    (payload_3, es_data_payload_3, "detailed", 0, 1),
]

rules_3 = [
    (payload_3, es_data_payload_3, "minimal", 1, 2),
    (payload_3, es_data_payload_3, "detailed", 0, 2),
    (payload_3, es_data_payload_3, "minimal", 2, 1),
    (payload_3, es_data_payload_3, "detailed", 2, 1),
]

# (First payload, Second payload, type_name, page, per_page, expected output)
rules_len = [
    (payload_9, payload_6, es_data_payload_10, "detailed", 0, 15, 9),
    (payload_10, payload_4, es_data_payload_10, "minimal", 0, 14, 4),
    (payload_1, payload_7, es_data_payload_10, "detailed", 0, 8, 7),
    (payload_1, payload_2, es_data_payload_10, "minimal", 0, 5, 2),
]

rules_has_more = [
    (payload_3, es_data_payload_3, "detailed", 1, 2, False),
    (payload_3, es_data_payload_3, "detailed", 0, 2, True),
    (payload_3, es_data_payload_3, "detailed", 0, 1, True),
]

corporate_payload = {
    "sku_info": {
        "470414": {
            "ordered_at": 1632992514.0,
            "quantity": "2",
            "created_at": "2021-09-30 09:01:54",
        },
    },
    "user_id": "ad9780da-f16e-43b5-8640-dd7752580793",
    "order_id": "1201",
}
corporate_user_headers = {
    "x-client": "android",
    "x-client-version": "15.0.1",
    "X-SHARED-CONTEXT": '{"user_context":{"user_id":"ad9780da-f16e-43b5-8640-dd7752580793","auth_token":"***REMOVED***","email":null,"name":null,"number":null,"visitor_id":"***REMOVED***","is_guest":true,"roles":[],"merchants":[],"affiliate_source":"","signup_source":null,"care_plan_info":{"name":null,"active":false},"corporate_details":{"name":"sbi"},"care_plan_in_cart":{},"profession":null,"has_delivered_order":false,"merchant_name":null,"merchant_key":null},"pincode_context":{"city":"gurgaon","pincode":"122001","cluster_id":1}}',
}
corporate_rule = [
    (corporate_payload, es_data_payload_corporate, "detailed", corporate_user_headers)
]
