import json
from app.managers.db import DB

import pytest
from sanic import Sanic
from torpedo import common_utils

from app.routes import blueprints
from app.tests.setup_test import setup_test

_env = common_utils.CONFIG.config.get("TEST_ENVIRONMENT", "dev")


@pytest.fixture(scope="session")
async def app():
    """Create an app for tests"""
    app = Sanic("test_cart_app")

    # Managers through main routes may invoke APIs from external service
    # clients
    # Mocks need to be written here so that this response is returned instead
    # of actual response from the
    # external service

    # *Note*: Ensure that the service path mentioned here is same as the
    # service HOST path in config.json.
    # Base endpoint is automatically replaced with test app server endpoint
    # if _env.lower() != "stag":
    #
    #     @app.route("/location-service/v4/address", methods=["GET"])
    #     async def test_get(request):
    #         return send_response(
    #             body=address_apis.GetAddressByIdApi().success_response_dict()
    #         )

    # else:
    #     pass

    yield app


@pytest.fixture(scope="session")
async def test_cli(loop, app, sanic_client):
    """Setup a test sanic app"""

    yield await setup_test(loop, sanic_client, app, blueprints)


class Base:
    """
    Main Test Class for all Rules.
    Classes like these can be used to create Tests for a particular model
    or entity
    """

    @staticmethod
    async def setup():
        """
        helper method for setting up data in test mongo db
        :return:
        """
        # TODO: use delete manager here
        # await Rules.all().delete()
        
        await DB.raw_sql("DROP TABLE IF EXISTS user_delivered_skus_mapping")

        sql_1 ='''CREATE TABLE user_delivered_skus_mapping(
            ID SERIAL PRIMARY KEY,
            USER_ID TEXT NOT NULL,
            SKU_ID TEXT NOT NULL,
            QUANTITY INT NOT NULL,
            ORDERED_AT BIGINT[] NOT NULL,
            SORTING_FACTOR INT NOT NULL DEFAULT 0,
            CREATED_AT TIMESTAMP NOT NULL,
            UPDATED_AT TIMESTAMP NOT NULL,
            MOST_RECENT_ORDER BIGINT NOT NULL
        )'''
        await DB.raw_sql(sql_1)

        await DB.raw_sql("DROP TABLE IF EXISTS recency_logic_table")

        sql_2 = '''CREATE TABLE recency_logic_table(
            ID SERIAL PRIMARY KEY,
            LOWER_LIMIT INT NOT NULL,
            VALUE DOUBLE PRECISION NOT NULL
        )'''
        await DB.raw_sql(sql_2)

    @staticmethod
    async def teardown():
        """
        helper method for deleting the setup up data in test mongo db
        :return:
        """
        # TODO: use delete manager here
        # await Rules.all().delete()

        await DB.raw_sql("DROP TABLE IF EXISTS user_delivered_skus_mapping")
        await DB.raw_sql("DROP TABLE IF EXISTS recency_logic_table")