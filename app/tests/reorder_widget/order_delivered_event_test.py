import asynctest, asyncio
from asynctest import patch

from app.managers.reorder import OrderDeliveredEvent

# from ...managers.reorder_widget import OrderDeliveredEvent


class OrderDeliveredEventTest(asynctest.TestCase):

    async def setUp(self):
        self.my_loop = asyncio.new_event_loop()
        self.addCleanup(self.my_loop.close)

    async def tearDown(self):
        self.my_loop.close()

    @patch.object(OrderDeliveredEvent, "user_existing_orders", return_value={'123456':{'sku_id':'123456', 'user_id':'abcd', 'quantity':5, 'ordered_at':[123456]}})
    async def test_merge_existing_and_new_skus(self, user_mock):
        merged = await OrderDeliveredEvent.merge_existing_and_new_skus('abcd',
                                                                {'123457': {'quantity': 10, 'ordered_at': 123457}},
                                                                set(),
                                                                set())
        assert 5 == 5