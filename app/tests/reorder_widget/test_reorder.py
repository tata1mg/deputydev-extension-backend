from hashlib import new
from math import ceil, floor
from pickle import FALSE
import pytest, json
from asynctest import patch
from app.tests.reorder_widget.base import Base, test_cli, app
from app.managers.reorder.order_delivered_event import OrderDeliveredEvent
from app.tests.fixtures.end_user_headers import android_user, new_user
from app.tests.fixtures.reorder_payload import rules, rules_2, rules_3, rules_len, rules_has_more, corporate_rule
from app.service_clients.search.search import SearchClient


class TestRule(Base):

    async def test_create_reorder_success(self, test_cli):
        await self.setup()

        response_object = await test_cli.get(
            "/end_user/v3/reorder_widget/?type=minimal&page=3&per_page=4", headers = android_user
        )
        assert response_object.status_code == 200

        await self.teardown()

    async def test_param_type_missing(self, test_cli):
        await self.setup()

        response_object = await test_cli.get(
            "/end_user/v3/reorder_widget/?page=3&per_page=4", headers = android_user
        )
        assert response_object.status_code == 400
        await self.teardown()

    async def test_param_page_missing(self, test_cli):
        await self.setup()

        response_object = await test_cli.get(
            "/end_user/v3/reorder_widget/?type=minimal&per_page=4", headers = android_user
        )
        assert response_object.status_code == 400

        await self.teardown()

    async def test_param_per_page_missing(self, test_cli):
        await self.setup()

        response_object = await test_cli.get(
            "/end_user/v3/reorder_widget/?type=minimal&page=3", headers = android_user
        )
        assert response_object.status_code == 400

        await self.teardown()

    @pytest.mark.parametrize("payload, api_response, type_name, page, per_page", rules)
    @patch.object(SearchClient, "sku_by_ids")
    async def test_minimal_v2(self, search_mock, test_cli, payload, api_response, type_name, page, per_page):
        
        await self.setup()

        await OrderDeliveredEvent.handle_event(payload)
        search_mock.return_value = api_response

        response= await test_cli.get(
            "/end_user/v3/reorder_widget/?type={}&page={}&per_page={}".format(type_name, page, per_page), headers  = new_user
        )

        #Setting up expected keys
        req = {'header','sub_header','skus','cta','show_hamburger', 'navigation'}

        dict = response.json()
        res = set(dict['data'].keys())

        assert res - req == set()

        await self.teardown()
    
    @pytest.mark.parametrize("payload, api_response, type_name, page, per_page", rules_2)
    @patch.object(SearchClient, "sku_by_ids")
    async def test_detailed_v2(self, search_mock, test_cli, payload, api_response, type_name, page, per_page):

        await self.setup()

        await OrderDeliveredEvent.handle_event(payload)
        search_mock.return_value = api_response

        response= await test_cli.get(
            "/end_user/v3/reorder_widget/?type={}&page={}&per_page={}".format(type_name, page, per_page), headers  = new_user
        )

        #Setting up expected keys
        req = {'header', 'sub_header', 'navigation', 'skus', 'show_hamburger', 'has_more', 'fallback'}

        dict = response.json()
        res = set(dict['data'].keys())

        assert res - req == set()

        await self.teardown()

    @pytest.mark.parametrize("payload, api_response, type_name, page, per_page", rules_3)
    @patch.object(SearchClient, "sku_by_ids")
    async def test_is_minimal(self, search_mock, test_cli, payload, api_response, type_name, page, per_page):
        
        await self.setup()
            
        await OrderDeliveredEvent.handle_event(payload)
        search_mock.return_value = api_response

        response= await test_cli.get(
            "/end_user/v3/reorder_widget/?type={}&page={}&per_page={}".format(type_name, page, per_page), headers  = new_user
        )

        req = {}

        #Setting up expected keys
        if(type_name == "detailed"):
            req = {'header', 'sub_header', 'navigation', 'skus', 'show_hamburger', 'has_more', 'fallback'}
        else:
            req = {'header','sub_header','skus','cta','show_hamburger', 'navigation'}

        dict = response.json()
        res = set(dict['data'].keys())

        assert res - req == set()

        await self.teardown()

    @pytest.mark.parametrize("payload, api_response, type_name, page, per_page, exp", rules_has_more)
    @patch.object(SearchClient, "sku_by_ids")
    async def test_has_more(self, search_mock, test_cli, payload, api_response, type_name, page, per_page, exp):
        
        await self.setup()

        await OrderDeliveredEvent.handle_event(payload)
        search_mock.return_value = api_response

        response= await test_cli.get(
            "/end_user/v3/reorder_widget/?type={}&page={}&per_page={}".format(type_name, page, per_page), headers  = new_user
        )

        res = response.json()
        assert res['data']['has_more'] == exp

        await self.teardown()

    @pytest.mark.parametrize("payload, api_response, type_name, page, per_page", rules_2)
    @patch.object(SearchClient, "sku_by_ids")
    async def test_fallback(self, search_mock, test_cli, payload, api_response, type_name, page, per_page):
        
        await self.setup()

        await OrderDeliveredEvent.handle_event(payload)
        search_mock.return_value = api_response

        response= await test_cli.get(
            "/end_user/v3/reorder_widget/?type={}&page={}&per_page={}".format(type_name, page, per_page), headers  = new_user
        )

        count = len(payload['sku_info'])
        res = response.json()
        
        if page <= ceil(count/per_page)-1:
            assert res['data']['fallback'] is None
        else:
            assert res['data']['fallback'] is not None

        await self.teardown()

    @pytest.mark.parametrize("payload, api_response, type_name, page, per_page", rules_3)
    @patch.object(SearchClient, "sku_by_ids")
    async def test_show_hamburger(self, search_mock, test_cli, payload, api_response, type_name, page, per_page):
        
        await self.setup()
        #create()

        await OrderDeliveredEvent.handle_event(payload)
        search_mock.return_value = api_response

        response= await test_cli.get(
            "/end_user/v3/reorder_widget/?type={}&page={}&per_page={}".format(type_name, page, per_page), headers  = new_user
        )

        res = response.json()
        flag = False

        for sku in res['data']['skus']:
            if sku['available'] == True:
                flag = True
                break

        if flag:
            assert res['data']['show_hamburger'] == True
        else:
            assert res['data']['show_hamburger'] == False

        # delete()
        await self.teardown()

    @pytest.mark.parametrize("payload, api_response, type_name, page, per_page", rules_2)
    @patch.object(SearchClient, "sku_by_ids")
    async def test_limit(self, search_mock, test_cli, payload, api_response, type_name, page, per_page):

        await self.setup()
        #create()

        await OrderDeliveredEvent.handle_event(payload)
        search_mock.return_value = api_response

        response= await test_cli.get(
            "/end_user/v3/reorder_widget/?type={}&page={}&per_page={}".format(type_name, page, per_page), headers  = new_user
        )

        res = response.json()
        count = len(res['data']['skus'])

        assert count <= per_page

        # delete()
        await self.teardown()

    @pytest.mark.parametrize("payload, api_response, type_name, page, per_page", rules_2)
    @patch.object(SearchClient, "sku_by_ids")
    async def test_offset(self, search_mock, test_cli, payload, api_response, type_name, page, per_page):

        await self.setup()

        await OrderDeliveredEvent.handle_event(payload)
        search_mock.return_value = api_response

        response= await test_cli.get(
            "/end_user/v3/reorder_widget/?type={}&page={}&per_page={}".format(type_name, page, per_page), headers  = new_user
        )

        res = response.json()
        count = len(payload['sku_info'])
        cutoff = ceil(count/per_page) - 1

        if page <= cutoff:
            assert res['data']['skus'] is not None
        else:
            assert res['data']['skus'] is None

        await self.teardown()

    @pytest.mark.parametrize("payload, api_response, type_name, page, per_page", rules_3)
    @patch.object(SearchClient, "sku_by_ids")
    async def test_skus(self, search_mock, test_cli, payload, api_response, type_name, page, per_page):

        await self.setup()

        await OrderDeliveredEvent.handle_event(payload)
        search_mock.return_value = api_response

        response= await test_cli.get(
            "/end_user/v3/reorder_widget/?type={}&page={}&per_page={}".format(type_name, page, per_page), headers  = new_user
        )

        res = response.json()
        assert res['data']['skus'] is not None

        await self.teardown()

    @pytest.mark.parametrize("payload_I, payload_II, api_response, type_name, page, per_page, exp", rules_len)
    @patch.object(SearchClient, "sku_by_ids")
    async def test_len(self, search_mock, test_cli, payload_I, payload_II, api_response, type_name, page, per_page, exp):

        await self.setup()

        await OrderDeliveredEvent.handle_event(payload_I)
        await OrderDeliveredEvent.handle_event(payload_II)
        search_mock.return_value = api_response

        response= await test_cli.get(
            "/end_user/v3/reorder_widget/?type={}&page={}&per_page={}".format(type_name, page, per_page), headers  = new_user
        )

        res = response.json()
        count = len(res['data']['skus'])
        for sku in res['data'].get('skus'):
            prices = sku.get('prices')
            if prices and prices.get('discounted_price') is None:
                assert prices.get('discount') is None
        assert count == exp

        await self.teardown()

    @pytest.mark.parametrize("payload, api_response_corporate, type_name, headers", corporate_rule)
    @patch.object(SearchClient, "sku_by_ids")
    async def test_detailed_v1(self, search_mock, test_cli, payload, api_response_corporate, type_name, headers):
        await self.setup()
        await OrderDeliveredEvent.handle_event(payload)
        search_mock.return_value = api_response_corporate
        response = await test_cli.get(
            "/end_user/v1/reorder_widget/?type={}".format(type_name),
            headers=headers
        )

        # Setting up expected keys
        req = {'skus', 'cta', 'show_hamburger', 'variant', 'visible_at', 'best_price'}

        dict = response.json()
        res = set(dict['data'].keys())

        assert res - req == set()
        data = dict['data']['skus'][0]
        assert data['price'] != data['discount']['price']
        await self.teardown()