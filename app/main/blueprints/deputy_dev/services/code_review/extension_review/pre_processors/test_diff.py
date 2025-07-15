diff = """diff --git a/app/managers/sku_offer/sku_offer_manager.py b/app/managers/sku_offer/sku_offer_manager.py
index 3c03ff2e..df5fa3d1 100644
--- a/app/managers/sku_offer/sku_offer_manager.py
+++ b/app/managers/sku_offer/sku_offer_manager.py
@@ -4,7 +4,6 @@ import json
 from sanic.log import logger
 
 from app.constants.enum import DiscountingPhaseTwoExperiment
-from app.service_clients.order.order import OrdersClient
 from app.service_clients.search.search import SearchClient
 from app.service_clients.subscription.subscription import SubscriptionServiceClient
 from app.utils import (
@@ -39,16 +38,6 @@ class SkuOfferManager:
             return False
         return True
 
-    async def get_user_type(self):
-        response = await OrdersClient.get_count(self.headers.user_id())
-        if response and sum(
-            response.get("status_wise_count", {}).get(status, 0)
-            for status in {"delivered", "refunded", "in_process"}
-        ):
-            return "repeated"
-        else:
-            return "new"
-
     def _get_cache_key_for_offer_data(self, filters):
         return f"{filters.get('city')}_{filters.get('user_transaction_state')}_{filters.get('plan_id')}"  # noqa : E501
 
@@ -56,7 +45,7 @@ class SkuOfferManager:
         discounting_phase_two_cohort = get_experiment_cohort_discounting_phase_two(
             self.headers
         )
-        self.headers.shared_context["user_type"] = await self.get_user_type()
+        self.headers.shared_context["user_type"] = "repeated"
         if (
             not discounting_phase_two_cohort
             or discounting_phase_two_cohort != DiscountingPhaseTwoExperiment.Test.value
diff --git a/app/service_clients/order/order.py b/app/service_clients/order/order.py
index 4406e468..bd486ad3 100644
--- a/app/service_clients/order/order.py
+++ b/app/service_clients/order/order.py
@@ -1,7 +1,5 @@
-from sanic.log import logger
 from torpedo import CONFIG
 
-from ...utils import service_client_wrapper
 from ..base import Base
 
 
@@ -9,17 +7,3 @@ class OrdersClient(Base):
     _host = CONFIG.config["ORDER_SERVICE"]["HOST"]
     _timeout = CONFIG.config["ORDER_SERVICE"]["TIMEOUT"]
     _service_name = "Order Service"
-
-    @classmethod
-    @service_client_wrapper(service_name=_service_name)
-    async def get_count(cls, user_id):  # pragma: no cover
-        params = {"user_id": user_id}
-        data = {}
-        result = None
-        try:
-            result = await cls.get("/v4/order_count", query_params=params)
-            data = result.data
-        except Exception as e:
-            logger.exception(e)
-            logger.info(f"OrdersCount get_count Params:{params} result {result}")
-        return data
diff --git a/app/tests/reorder_widget/test_reorder.py b/app/tests/reorder_widget/test_reorder.py
index e5194dc5..df2722c2 100644
--- a/app/tests/reorder_widget/test_reorder.py
+++ b/app/tests/reorder_widget/test_reorder.py
@@ -5,7 +5,6 @@ from unittest.mock import patch
 import pytest
 
 from app.managers.reorder.order_delivered_event import OrderDeliveredEvent
-from app.service_clients.order.order import OrdersClient
 from app.service_clients.search.search import SearchClient
 from app.service_clients.subscription.subscription import SubscriptionServiceClient
 from app.tests.fixtures.end_user_headers import (
@@ -450,10 +449,8 @@ class TestRule(Base):
     @patch.object(SearchClient, "sku_by_ids")
     @patch.object(SubscriptionServiceClient, "preferred_plan")
     @patch.object(SearchClient, "applicable_coupons")
-    @patch.object(OrdersClient, "get_count")
     async def test_detailed_v2_with_discounting(
         self,
-        mock_get_count,
         mock_get_applicable_coupons,
         mock_preferred_plan,
         search_mock,
@@ -475,7 +472,6 @@ class TestRule(Base):
             "sku_id": 651662,
             "plan_type": "mini_care_plan",
         }
-        mock_get_count.return_value = {"status_wise_count": {"delivered": 0}}
 
         response = await test_cli.get(
             "/end_user/v3/reorder_widget/?type={}&page={}&per_page={}".format(
diff --git a/config_template.json b/config_template.json
index 583ae777..5ee4dd93 100644
--- a/config_template.json
+++ b/config_template.json
@@ -67,12 +67,14 @@
     "zeus": {
       "LABEL": "global",
       "REDIS_HOST": "localhost",
-      "REDIS_PORT": 6379
+      "REDIS_PORT": 6379,
+      "CONN_LIMIT": 100
     },
     "merch_service": {
       "REDIS_HOST": "pharma-redis-master.{{ env_name }}.svc.{{ cluster_domain }}",
       "REDIS_PORT": 6379,
-      "LABEL": "merch_service"
+      "LABEL": "merch_service",
+      "CONN_LIMIT": 100
     }
   },
   "REFILL_TEST_EXPERIMENT": {
diff --git a/poetry.lock b/poetry.lock
index 60cc3560..748b1ef8 100644
--- a/poetry.lock
+++ b/poetry.lock
@@ -358,7 +358,7 @@ crt = ["awscrt (==0.19.19)"]
 
 [[package]]
 name = "cache-wrapper"
-version = "4.0.0"
+version = "4.1.0"
 description = "Wrapper module for cache related utilities."
 optional = false
 python-versions = ">=3.8,<4.0"
@@ -372,18 +372,18 @@ ujson = "5.9.0"
 [package.source]
 type = "git"
 url = "ssh://git@bitbucket.org/tata1mg/cache_wrapper.git"
-reference = "4.0.0"
-resolved_reference = "ed973fb64bf1325f431a7f5bf4915b2adaf486f0"
+reference = "feat/conn-limit"
+resolved_reference = "a8fd9a7dd66dbf2b832bb0786fbb3ecd7e81649d"
 
 [[package]]
 name = "certifi"
-version = "2024.12.14"
+version = "2025.1.31"
 description = "Python package for providing Mozilla's CA Bundle."
 optional = false
 python-versions = ">=3.6"
 files = [
-    {file = "certifi-2024.12.14-py3-none-any.whl", hash = "sha256:1275f7a45be9464efc1173084eaa30f866fe2e47d389406136d332ed4967ec56"},
-    {file = "certifi-2024.12.14.tar.gz", hash = "sha256:b650d30f370c2b724812bee08008be0c4163b163ddaec3f2546c1caf65f191db"},
+    {file = "certifi-2025.1.31-py3-none-any.whl", hash = "sha256:ca78db4565a652026a4db2bcdf68f2fb589ea80d0be70e03929ed730746b84fe"},
+    {file = "certifi-2025.1.31.tar.gz", hash = "sha256:3d5da6925056f6f18f119200434a4780a94263f10d1c21d032a6f6b2baa20651"},
 ]
 
 [[package]]
@@ -535,73 +535,74 @@ resolved_reference = "32e067a8f76a916c4edaaf3c0e619777305fda9a"
 
 [[package]]
 name = "coverage"
-version = "7.6.10"
+version = "7.6.12"
 description = "Code coverage measurement for Python"
 optional = false
 python-versions = ">=3.9"
 files = [
-    {file = "coverage-7.6.10-cp310-cp310-macosx_10_9_x86_64.whl", hash = "sha256:5c912978f7fbf47ef99cec50c4401340436d200d41d714c7a4766f377c5b7b78"},
-    {file = "coverage-7.6.10-cp310-cp310-macosx_11_0_arm64.whl", hash = "sha256:a01ec4af7dfeb96ff0078ad9a48810bb0cc8abcb0115180c6013a6b26237626c"},
-    {file = "coverage-7.6.10-cp310-cp310-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:a3b204c11e2b2d883946fe1d97f89403aa1811df28ce0447439178cc7463448a"},
-    {file = "coverage-7.6.10-cp310-cp310-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:32ee6d8491fcfc82652a37109f69dee9a830e9379166cb73c16d8dc5c2915165"},
-    {file = "coverage-7.6.10-cp310-cp310-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:675cefc4c06e3b4c876b85bfb7c59c5e2218167bbd4da5075cbe3b5790a28988"},
-    {file = "coverage-7.6.10-cp310-cp310-musllinux_1_2_aarch64.whl", hash = "sha256:f4f620668dbc6f5e909a0946a877310fb3d57aea8198bde792aae369ee1c23b5"},
-    {file = "coverage-7.6.10-cp310-cp310-musllinux_1_2_i686.whl", hash = "sha256:4eea95ef275de7abaef630c9b2c002ffbc01918b726a39f5a4353916ec72d2f3"},
-    {file = "coverage-7.6.10-cp310-cp310-musllinux_1_2_x86_64.whl", hash = "sha256:e2f0280519e42b0a17550072861e0bc8a80a0870de260f9796157d3fca2733c5"},
-    {file = "coverage-7.6.10-cp310-cp310-win32.whl", hash = "sha256:bc67deb76bc3717f22e765ab3e07ee9c7a5e26b9019ca19a3b063d9f4b874244"},
-    {file = "coverage-7.6.10-cp310-cp310-win_amd64.whl", hash = "sha256:0f460286cb94036455e703c66988851d970fdfd8acc2a1122ab7f4f904e4029e"},
-    {file = "coverage-7.6.10-cp311-cp311-macosx_10_9_x86_64.whl", hash = "sha256:ea3c8f04b3e4af80e17bab607c386a830ffc2fb88a5484e1df756478cf70d1d3"},
-    {file = "coverage-7.6.10-cp311-cp311-macosx_11_0_arm64.whl", hash = "sha256:507a20fc863cae1d5720797761b42d2d87a04b3e5aeb682ef3b7332e90598f43"},
-    {file = "coverage-7.6.10-cp311-cp311-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:d37a84878285b903c0fe21ac8794c6dab58150e9359f1aaebbeddd6412d53132"},
-    {file = "coverage-7.6.10-cp311-cp311-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:a534738b47b0de1995f85f582d983d94031dffb48ab86c95bdf88dc62212142f"},
-    {file = "coverage-7.6.10-cp311-cp311-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:0d7a2bf79378d8fb8afaa994f91bfd8215134f8631d27eba3e0e2c13546ce994"},
-    {file = "coverage-7.6.10-cp311-cp311-musllinux_1_2_aarch64.whl", hash = "sha256:6713ba4b4ebc330f3def51df1d5d38fad60b66720948112f114968feb52d3f99"},
-    {file = "coverage-7.6.10-cp311-cp311-musllinux_1_2_i686.whl", hash = "sha256:ab32947f481f7e8c763fa2c92fd9f44eeb143e7610c4ca9ecd6a36adab4081bd"},
-    {file = "coverage-7.6.10-cp311-cp311-musllinux_1_2_x86_64.whl", hash = "sha256:7bbd8c8f1b115b892e34ba66a097b915d3871db7ce0e6b9901f462ff3a975377"},
-    {file = "coverage-7.6.10-cp311-cp311-win32.whl", hash = "sha256:299e91b274c5c9cdb64cbdf1b3e4a8fe538a7a86acdd08fae52301b28ba297f8"},
-    {file = "coverage-7.6.10-cp311-cp311-win_amd64.whl", hash = "sha256:489a01f94aa581dbd961f306e37d75d4ba16104bbfa2b0edb21d29b73be83609"},
-    {file = "coverage-7.6.10-cp312-cp312-macosx_10_13_x86_64.whl", hash = "sha256:27c6e64726b307782fa5cbe531e7647aee385a29b2107cd87ba7c0105a5d3853"},
-    {file = "coverage-7.6.10-cp312-cp312-macosx_11_0_arm64.whl", hash = "sha256:c56e097019e72c373bae32d946ecf9858fda841e48d82df7e81c63ac25554078"},
-    {file = "coverage-7.6.10-cp313-cp313t-macosx_10_13_x86_64.whl", hash = "sha256:2ccf240eb719789cedbb9fd1338055de2761088202a9a0b73032857e53f612fe"},
-    {file = "coverage-7.6.10-cp313-cp313t-macosx_11_0_arm64.whl", hash = "sha256:0c807ca74d5a5e64427c8805de15b9ca140bba13572d6d74e262f46f50b13273"},
-    {file = "coverage-7.6.10-cp313-cp313t-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:2bcfa46d7709b5a7ffe089075799b902020b62e7ee56ebaed2f4bdac04c508d8"},
-    {file = "coverage-7.6.10-cp313-cp313t-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:4e0de1e902669dccbf80b0415fb6b43d27edca2fbd48c74da378923b05316098"},
-    {file = "coverage-7.6.10-cp313-cp313t-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:3f7b444c42bbc533aaae6b5a2166fd1a797cdb5eb58ee51a92bee1eb94a1e1cb"},
+    {file = "coverage-7.6.12-cp310-cp310-macosx_10_9_x86_64.whl", hash = "sha256:704c8c8c6ce6569286ae9622e534b4f5b9759b6f2cd643f1c1a61f666d534fe8"},
+    {file = "coverage-7.6.12-cp310-cp310-macosx_11_0_arm64.whl", hash = "sha256:ad7525bf0241e5502168ae9c643a2f6c219fa0a283001cee4cf23a9b7da75879"},
+    {file = "coverage-7.6.12-cp310-cp310-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:06097c7abfa611c91edb9e6920264e5be1d6ceb374efb4986f38b09eed4cb2fe"},
+    {file = "coverage-7.6.12-cp310-cp310-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:220fa6c0ad7d9caef57f2c8771918324563ef0d8272c94974717c3909664e674"},
+    {file = "coverage-7.6.12-cp313-cp313-musllinux_1_2_x86_64.whl", hash = "sha256:8bec2ac5da793c2685ce5319ca9bcf4eee683b8a1679051f8e6ec04c4f2fd7dc"},
+    {file = "coverage-7.6.12-cp313-cp313-win32.whl", hash = "sha256:200e10beb6ddd7c3ded322a4186313d5ca9e63e33d8fab4faa67ef46d3460af3"},
+    {file = "coverage-7.6.12-cp313-cp313-win_amd64.whl", hash = "sha256:2b996819ced9f7dbb812c701485d58f261bef08f9b85304d41219b1496b591ef"},
+    {file = "coverage-7.6.12-cp313-cp313t-macosx_10_13_x86_64.whl", hash = "sha256:299cf973a7abff87a30609879c10df0b3bfc33d021e1adabc29138a48888841e"},
+    {file = "coverage-7.6.12-cp313-cp313t-macosx_11_0_arm64.whl", hash = "sha256:4b467a8c56974bf06e543e69ad803c6865249d7a5ccf6980457ed2bc50312703"},
+    {file = "coverage-7.6.12-cp313-cp313t-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:2458f275944db8129f95d91aee32c828a408481ecde3b30af31d552c2ce284a0"},
+    {file = "coverage-7.6.12-cp313-cp313t-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:0a9d8be07fb0832636a0f72b80d2a652fe665e80e720301fb22b191c3434d924"},
+    {file = "coverage-7.6.12-cp313-cp313t-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:14d47376a4f445e9743f6c83291e60adb1b127607a3618e3185bbc8091f0467b"},
+    {file = "coverage-7.6.12-cp313-cp313t-musllinux_1_2_aarch64.whl", hash = "sha256:b95574d06aa9d2bd6e5cc35a5bbe35696342c96760b69dc4287dbd5abd4ad51d"},
+    {file = "coverage-7.6.12-cp313-cp313t-musllinux_1_2_i686.whl", hash = "sha256:ecea0c38c9079570163d663c0433a9af4094a60aafdca491c6a3d248c7432827"},
+    {file = "coverage-7.6.12-cp313-cp313t-musllinux_1_2_x86_64.whl", hash = "sha256:2251fabcfee0a55a8578a9d29cecfee5f2de02f11530e7d5c5a05859aa85aee9"},
+    {file = "coverage-7.6.12-cp313-cp313t-win32.whl", hash = "sha256:eb5507795caabd9b2ae3f1adc95f67b1104971c22c624bb354232d65c4fc90b3"},
+    {file = "coverage-7.6.12-cp313-cp313t-win_amd64.whl", hash = "sha256:f60a297c3987c6c02ffb29effc70eadcbb412fe76947d394a1091a3615948e2f"},
+    {file = "coverage-7.6.12-cp39-cp39-macosx_10_9_x86_64.whl", hash = "sha256:e7575ab65ca8399c8c4f9a7d61bbd2d204c8b8e447aab9d355682205c9dd948d"},
+    {file = "coverage-7.6.12-cp39-cp39-macosx_11_0_arm64.whl", hash = "sha256:8161d9fbc7e9fe2326de89cd0abb9f3599bccc1287db0aba285cb68d204ce929"},
+    {file = "coverage-7.6.12-cp39-cp39-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:3a1e465f398c713f1b212400b4e79a09829cd42aebd360362cd89c5bdc44eb87"},
+    {file = "coverage-7.6.12-cp39-cp39-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:f25d8b92a4e31ff1bd873654ec367ae811b3a943583e05432ea29264782dc32c"},
+    {file = "coverage-7.6.12-cp39-cp39-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:1a936309a65cc5ca80fa9f20a442ff9e2d06927ec9a4f54bcba9c14c066323f2"},
+    {file = "coverage-7.6.12-cp39-cp39-musllinux_1_2_aarch64.whl", hash = "sha256:aa6f302a3a0b5f240ee201297fff0bbfe2fa0d415a94aeb257d8b461032389bd"},
+    {file = "coverage-7.6.12-cp39-cp39-musllinux_1_2_i686.whl", hash = "sha256:f973643ef532d4f9be71dd88cf7588936685fdb576d93a79fe9f65bc337d9d73"},
+    {file = "coverage-7.6.12-cp39-cp39-musllinux_1_2_x86_64.whl", hash = "sha256:78f5243bb6b1060aed6213d5107744c19f9571ec76d54c99cc15938eb69e0e86"},
+    {file = "coverage-7.6.12-cp39-cp39-win32.whl", hash = "sha256:69e62c5034291c845fc4df7f8155e8544178b6c774f97a99e2734b05eb5bed31"},
+    {file = "coverage-7.6.12-cp39-cp39-win_amd64.whl", hash = "sha256:b01a840ecc25dce235ae4c1b6a0daefb2a203dba0e6e980637ee9c2f6ee0df57"},
+    {file = "coverage-7.6.12-pp39.pp310-none-any.whl", hash = "sha256:7e39e845c4d764208e7b8f6a21c541ade741e2c41afabdfa1caa28687a3c98cf"},
+    {file = "coverage-7.6.12-py3-none-any.whl", hash = "sha256:eb8668cfbc279a536c633137deeb9435d2962caec279c3f8cf8b91fff6ff8953"},
+    {file = "coverage-7.6.12.tar.gz", hash = "sha256:48cfc4641d95d34766ad41d9573cc0f22a48aa88d22657a1fe01dca0dbae4de2"},
 ]
 
 [package.extras]
@@ -1556,93 +1557,109 @@ testing = ["pytest", "pytest-benchmark"]
 
 [[package]]
 name = "propcache"
-version = "0.2.1"
+version = "0.3.0"
 description = "Accelerated property cache"
 optional = false
 python-versions = ">=3.9"
 files = [
-    {file = "propcache-0.2.1-cp310-cp310-macosx_10_9_universal2.whl", hash = "sha256:6b3f39a85d671436ee3d12c017f8fdea38509e4f25b28eb25877293c98c243f6"},
-    {file = "propcache-0.2.1-cp310-cp310-macosx_10_9_x86_64.whl", hash = "sha256:39d51fbe4285d5db5d92a929e3e21536ea3dd43732c5b177c7ef03f918dff9f2"},
-    {file = "propcache-0.2.1-cp310-cp310-macosx_11_0_arm64.whl", hash = "sha256:6445804cf4ec763dc70de65a3b0d9954e868609e83850a47ca4f0cb64bd79fea"},
-    {file = "propcache-0.2.1-cp310-cp310-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:f9479aa06a793c5aeba49ce5c5692ffb51fcd9a7016e017d555d5e2b0045d212"},
-    {file = "propcache-0.2.1-cp310-cp310-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:d9631c5e8b5b3a0fda99cb0d29c18133bca1e18aea9effe55adb3da1adef80d3"},
-    {file = "propcache-0.2.1-cp310-cp310-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:3156628250f46a0895f1f36e1d4fbe062a1af8718ec3ebeb746f1d23f0c5dc4d"},
-    {file = "propcache-0.2.1-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:6b6fb63ae352e13748289f04f37868099e69dba4c2b3e271c46061e82c745634"},
-    {file = "propcache-0.2.1-cp310-cp310-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:887d9b0a65404929641a9fabb6452b07fe4572b269d901d622d8a34a4e9043b2"},
-    {file = "propcache-0.2.1-cp310-cp310-musllinux_1_2_aarch64.whl", hash = "sha256:a96dc1fa45bd8c407a0af03b2d5218392729e1822b0c32e62c5bf7eeb5fb3958"},
-    {file = "propcache-0.2.1-cp310-cp310-musllinux_1_2_armv7l.whl", hash = "sha256:a7e65eb5c003a303b94aa2c3852ef130230ec79e349632d030e9571b87c4698c"},
-    {file = "propcache-0.2.1-cp310-cp310-musllinux_1_2_i686.whl", hash = "sha256:999779addc413181912e984b942fbcc951be1f5b3663cd80b2687758f434c583"},
-    {file = "propcache-0.2.1-cp310-cp310-musllinux_1_2_ppc64le.whl", hash = "sha256:19a0f89a7bb9d8048d9c4370c9c543c396e894c76be5525f5e1ad287f1750ddf"},
+    {file = "propcache-0.3.0-cp311-cp311-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:a254537b9b696ede293bfdbc0a65200e8e4507bc9f37831e2a0318a9b333c85c"},
+    {file = "propcache-0.3.0-cp311-cp311-musllinux_1_2_aarch64.whl", hash = "sha256:2b975528998de037dfbc10144b8aed9b8dd5a99ec547f14d1cb7c5665a43f075"},
+    {file = "propcache-0.3.0-cp311-cp311-musllinux_1_2_armv7l.whl", hash = "sha256:19d36bb351ad5554ff20f2ae75f88ce205b0748c38b146c75628577020351e3c"},
+    {file = "propcache-0.3.0-cp311-cp311-musllinux_1_2_i686.whl", hash = "sha256:6032231d4a5abd67c7f71168fd64a47b6b451fbcb91c8397c2f7610e67683810"},
+    {file = "propcache-0.3.0-cp311-cp311-musllinux_1_2_ppc64le.whl", hash = "sha256:6985a593417cdbc94c7f9c3403747335e450c1599da1647a5af76539672464d3"},
+    {file = "propcache-0.3.0-cp311-cp311-musllinux_1_2_s390x.whl", hash = "sha256:6a1948df1bb1d56b5e7b0553c0fa04fd0e320997ae99689488201f19fa90d2e7"},
+    {file = "propcache-0.3.0-cp311-cp311-musllinux_1_2_x86_64.whl", hash = "sha256:8319293e85feadbbfe2150a5659dbc2ebc4afdeaf7d98936fb9a2f2ba0d4c35c"},
+    {file = "propcache-0.3.0-cp311-cp311-win32.whl", hash = "sha256:63f26258a163c34542c24808f03d734b338da66ba91f410a703e505c8485791d"},
+    {file = "propcache-0.3.0-cp311-cp311-win_amd64.whl", hash = "sha256:cacea77ef7a2195f04f9279297684955e3d1ae4241092ff0cfcef532bb7a1c32"},
+    {file = "propcache-0.3.0-cp312-cp312-macosx_10_13_universal2.whl", hash = "sha256:e53d19c2bf7d0d1e6998a7e693c7e87300dd971808e6618964621ccd0e01fe4e"},
+    {file = "propcache-0.3.0-cp312-cp312-macosx_10_13_x86_64.whl", hash = "sha256:a61a68d630e812b67b5bf097ab84e2cd79b48c792857dc10ba8a223f5b06a2af"},
+    {file = "propcache-0.3.0-cp312-cp312-macosx_11_0_arm64.whl", hash = "sha256:fb91d20fa2d3b13deea98a690534697742029f4fb83673a3501ae6e3746508b5"},
+    {file = "propcache-0.3.0-cp312-cp312-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:67054e47c01b7b349b94ed0840ccae075449503cf1fdd0a1fdd98ab5ddc2667b"},
+    {file = "propcache-0.3.0-cp312-cp312-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:997e7b8f173a391987df40f3b52c423e5850be6f6df0dcfb5376365440b56667"},
+    {file = "propcache-0.3.0-cp312-cp312-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:8d663fd71491dde7dfdfc899d13a067a94198e90695b4321084c6e450743b8c7"},
+    {file = "propcache-0.3.0-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:8884ba1a0fe7210b775106b25850f5e5a9dc3c840d1ae9924ee6ea2eb3acbfe7"},
+    {file = "propcache-0.3.0-cp312-cp312-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:aa806bbc13eac1ab6291ed21ecd2dd426063ca5417dd507e6be58de20e58dfcf"},
+    {file = "propcache-0.3.0-cp312-cp312-musllinux_1_2_aarch64.whl", hash = "sha256:6f4d7a7c0aff92e8354cceca6fe223973ddf08401047920df0fcb24be2bd5138"},
+    {file = "propcache-0.3.0-cp312-cp312-musllinux_1_2_armv7l.whl", hash = "sha256:9be90eebc9842a93ef8335291f57b3b7488ac24f70df96a6034a13cb58e6ff86"},
+    {file = "propcache-0.3.0-cp312-cp312-musllinux_1_2_i686.whl", hash = "sha256:bf15fc0b45914d9d1b706f7c9c4f66f2b7b053e9517e40123e137e8ca8958b3d"},
+    {file = "propcache-0.3.0-cp312-cp312-musllinux_1_2_ppc64le.whl", hash = "sha256:5a16167118677d94bb48bfcd91e420088854eb0737b76ec374b91498fb77a70e"},
+    {file = "propcache-0.3.0-cp312-cp312-musllinux_1_2_s390x.whl", hash = "sha256:41de3da5458edd5678b0f6ff66691507f9885f5fe6a0fb99a5d10d10c0fd2d64"},
+    {file = "propcache-0.3.0-cp312-cp312-musllinux_1_2_x86_64.whl", hash = "sha256:728af36011bb5d344c4fe4af79cfe186729efb649d2f8b395d1572fb088a996c"},
+    {file = "propcache-0.3.0-cp312-cp312-win32.whl", hash = "sha256:6b5b7fd6ee7b54e01759f2044f936dcf7dea6e7585f35490f7ca0420fe723c0d"},
+    {file = "propcache-0.3.0-cp312-cp312-win_amd64.whl", hash = "sha256:2d15bc27163cd4df433e75f546b9ac31c1ba7b0b128bfb1b90df19082466ff57"},
+    {file = "propcache-0.3.0-cp313-cp313-macosx_10_13_universal2.whl", hash = "sha256:a2b9bf8c79b660d0ca1ad95e587818c30ccdb11f787657458d6f26a1ea18c568"},
+    {file = "propcache-0.3.0-cp313-cp313-macosx_10_13_x86_64.whl", hash = "sha256:b0c1a133d42c6fc1f5fbcf5c91331657a1ff822e87989bf4a6e2e39b818d0ee9"},
+    {file = "propcache-0.3.0-cp313-cp313-macosx_11_0_arm64.whl", hash = "sha256:bb2f144c6d98bb5cbc94adeb0447cfd4c0f991341baa68eee3f3b0c9c0e83767"},
+    {file = "propcache-0.3.0-cp313-cp313-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:d1323cd04d6e92150bcc79d0174ce347ed4b349d748b9358fd2e497b121e03c8"},
+    {file = "propcache-0.3.0-cp313-cp313-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:3b812b3cb6caacd072276ac0492d249f210006c57726b6484a1e1805b3cfeea0"},
+    {file = "propcache-0.3.0-cp313-cp313-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:742840d1d0438eb7ea4280f3347598f507a199a35a08294afdcc560c3739989d"},
+    {file = "propcache-0.3.0-cp313-cp313-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:7c6e7e4f9167fddc438cd653d826f2222222564daed4116a02a184b464d3ef05"},
+    {file = "propcache-0.3.0-cp313-cp313-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:a94ffc66738da99232ddffcf7910e0f69e2bbe3a0802e54426dbf0714e1c2ffe"},
+    {file = "propcache-0.3.0-cp313-cp313-musllinux_1_2_aarch64.whl", hash = "sha256:3c6ec957025bf32b15cbc6b67afe233c65b30005e4c55fe5768e4bb518d712f1"},
+    {file = "propcache-0.3.0-cp313-cp313-musllinux_1_2_armv7l.whl", hash = "sha256:549722908de62aa0b47a78b90531c022fa6e139f9166be634f667ff45632cc92"},
+    {file = "propcache-0.3.0-cp313-cp313-musllinux_1_2_i686.whl", hash = "sha256:5d62c4f6706bff5d8a52fd51fec6069bef69e7202ed481486c0bc3874912c787"},
+    {file = "propcache-0.3.0-cp313-cp313-musllinux_1_2_ppc64le.whl", hash = "sha256:24c04f8fbf60094c531667b8207acbae54146661657a1b1be6d3ca7773b7a545"},
+    {file = "propcache-0.3.0-cp313-cp313-musllinux_1_2_s390x.whl", hash = "sha256:7c5f5290799a3f6539cc5e6f474c3e5c5fbeba74a5e1e5be75587746a940d51e"},
+    {file = "propcache-0.3.0-cp313-cp313-musllinux_1_2_x86_64.whl", hash = "sha256:4fa0e7c9c3cf7c276d4f6ab9af8adddc127d04e0fcabede315904d2ff76db626"},
+    {file = "propcache-0.3.0-cp313-cp313-win32.whl", hash = "sha256:ee0bd3a7b2e184e88d25c9baa6a9dc609ba25b76daae942edfb14499ac7ec374"},
+    {file = "propcache-0.3.0-cp313-cp313-win_amd64.whl", hash = "sha256:1c8f7d896a16da9455f882870a507567d4f58c53504dc2d4b1e1d386dfe4588a"},
+    {file = "propcache-0.3.0-cp313-cp313t-macosx_10_13_universal2.whl", hash = "sha256:e560fd75aaf3e5693b91bcaddd8b314f4d57e99aef8a6c6dc692f935cc1e6bbf"},
+    {file = "propcache-0.3.0-cp313-cp313t-macosx_10_13_x86_64.whl", hash = "sha256:65a37714b8ad9aba5780325228598a5b16c47ba0f8aeb3dc0514701e4413d7c0"},
+    {file = "propcache-0.3.0-cp313-cp313t-macosx_11_0_arm64.whl", hash = "sha256:07700939b2cbd67bfb3b76a12e1412405d71019df00ca5697ce75e5ef789d829"},
+    {file = "propcache-0.3.0-cp313-cp313t-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:7c0fdbdf6983526e269e5a8d53b7ae3622dd6998468821d660d0daf72779aefa"},
+    {file = "propcache-0.3.0-cp313-cp313t-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:794c3dd744fad478b6232289c866c25406ecdfc47e294618bdf1697e69bd64a6"},
+    {file = "propcache-0.3.0-cp313-cp313t-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:4544699674faf66fb6b4473a1518ae4999c1b614f0b8297b1cef96bac25381db"},
+    {file = "propcache-0.3.0-cp313-cp313t-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:fddb8870bdb83456a489ab67c6b3040a8d5a55069aa6f72f9d872235fbc52f54"},
+    {file = "propcache-0.3.0-cp313-cp313t-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:f857034dc68d5ceb30fb60afb6ff2103087aea10a01b613985610e007053a121"},
+    {file = "propcache-0.3.0-cp313-cp313t-musllinux_1_2_aarch64.whl", hash = "sha256:02df07041e0820cacc8f739510078f2aadcfd3fc57eaeeb16d5ded85c872c89e"},
+    {file = "propcache-0.3.0-cp313-cp313t-musllinux_1_2_armv7l.whl", hash = "sha256:f47d52fd9b2ac418c4890aad2f6d21a6b96183c98021f0a48497a904199f006e"},
+    {file = "propcache-0.3.0-cp313-cp313t-musllinux_1_2_i686.whl", hash = "sha256:9ff4e9ecb6e4b363430edf2c6e50173a63e0820e549918adef70515f87ced19a"},
+    {file = "propcache-0.3.0-cp313-cp313t-musllinux_1_2_ppc64le.whl", hash = "sha256:ecc2920630283e0783c22e2ac94427f8cca29a04cfdf331467d4f661f4072dac"},
+    {file = "propcache-0.3.0-cp313-cp313t-musllinux_1_2_s390x.whl", hash = "sha256:c441c841e82c5ba7a85ad25986014be8d7849c3cfbdb6004541873505929a74e"},
+    {file = "propcache-0.3.0-cp313-cp313t-musllinux_1_2_x86_64.whl", hash = "sha256:6c929916cbdb540d3407c66f19f73387f43e7c12fa318a66f64ac99da601bcdf"},
+    {file = "propcache-0.3.0-cp313-cp313t-win32.whl", hash = "sha256:0c3e893c4464ebd751b44ae76c12c5f5c1e4f6cbd6fbf67e3783cd93ad221863"},
+    {file = "propcache-0.3.0-cp313-cp313t-win_amd64.whl", hash = "sha256:75e872573220d1ee2305b35c9813626e620768248425f58798413e9c39741f46"},
+    {file = "propcache-0.3.0-cp39-cp39-macosx_10_9_universal2.whl", hash = "sha256:03c091bb752349402f23ee43bb2bff6bd80ccab7c9df6b88ad4322258d6960fc"},
+    {file = "propcache-0.3.0-cp39-cp39-macosx_10_9_x86_64.whl", hash = "sha256:46ed02532cb66612d42ae5c3929b5e98ae330ea0f3900bc66ec5f4862069519b"},
+    {file = "propcache-0.3.0-cp39-cp39-macosx_11_0_arm64.whl", hash = "sha256:11ae6a8a01b8a4dc79093b5d3ca2c8a4436f5ee251a9840d7790dccbd96cb649"},
+    {file = "propcache-0.3.0-cp39-cp39-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:df03cd88f95b1b99052b52b1bb92173229d7a674df0ab06d2b25765ee8404bce"},
+    {file = "propcache-0.3.0-cp39-cp39-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:03acd9ff19021bd0567582ac88f821b66883e158274183b9e5586f678984f8fe"},
+    {file = "propcache-0.3.0-cp39-cp39-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:cd54895e4ae7d32f1e3dd91261df46ee7483a735017dc6f987904f194aa5fd14"},
+    {file = "propcache-0.3.0-cp39-cp39-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:26a67e5c04e3119594d8cfae517f4b9330c395df07ea65eab16f3d559b7068fe"},
+    {file = "propcache-0.3.0-cp39-cp39-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:ee25f1ac091def37c4b59d192bbe3a206298feeb89132a470325bf76ad122a1e"},
+    {file = "propcache-0.3.0-cp39-cp39-musllinux_1_2_aarch64.whl", hash = "sha256:58e6d2a5a7cb3e5f166fd58e71e9a4ff504be9dc61b88167e75f835da5764d07"},
+    {file = "propcache-0.3.0-cp39-cp39-musllinux_1_2_armv7l.whl", hash = "sha256:be90c94570840939fecedf99fa72839aed70b0ced449b415c85e01ae67422c90"},
+    {file = "propcache-0.3.0-cp39-cp39-musllinux_1_2_i686.whl", hash = "sha256:49ea05212a529c2caffe411e25a59308b07d6e10bf2505d77da72891f9a05641"},
+    {file = "propcache-0.3.0-cp39-cp39-musllinux_1_2_ppc64le.whl", hash = "sha256:119e244ab40f70a98c91906d4c1f4c5f2e68bd0b14e7ab0a06922038fae8a20f"},
+    {file = "propcache-0.3.0-cp39-cp39-musllinux_1_2_s390x.whl", hash = "sha256:507c5357a8d8b4593b97fb669c50598f4e6cccbbf77e22fa9598aba78292b4d7"},
+    {file = "propcache-0.3.0-cp39-cp39-musllinux_1_2_x86_64.whl", hash = "sha256:8526b0941ec5a40220fc4dfde76aed58808e2b309c03e9fa8e2260083ef7157f"},
+    {file = "propcache-0.3.0-cp39-cp39-win32.whl", hash = "sha256:7cedd25e5f678f7738da38037435b340694ab34d424938041aa630d8bac42663"},
+    {file = "propcache-0.3.0-cp39-cp39-win_amd64.whl", hash = "sha256:bf4298f366ca7e1ad1d21bbb58300a6985015909964077afd37559084590c929"},
+    {file = "propcache-0.3.0-py3-none-any.whl", hash = "sha256:67dda3c7325691c2081510e92c561f465ba61b975f481735aefdfc845d2cd043"},
+    {file = "propcache-0.3.0.tar.gz", hash = "sha256:a8fd93de4e1d278046345f49e2238cdb298589325849b2645d4a94c53faeffc5"},
 ]
 
 [[package]]
@@ -1890,13 +1907,13 @@ files = [
 
 [[package]]
 name = "pytz"
-version = "2024.2"
+version = "2025.1"
 description = "World timezone definitions, modern and historical"
 optional = false
 python-versions = "*"
 files = [
-    {file = "pytz-2024.2-py2.py3-none-any.whl", hash = "sha256:31c7c1817eb7fae7ca4b8c7ee50c72f93aa2dd863de768e1ef4245d426aa0725"},
-    {file = "pytz-2024.2.tar.gz", hash = "sha256:2aa355083c50a0f93fa581709deac0c9ad65cca8a9e9beac660adcbd493c798a"},
+    {file = "pytz-2025.1-py2.py3-none-any.whl", hash = "sha256:89dd22dca55b46eac6eda23b2d72721bf1bdfef212645d81513ef5d03038de57"},
+    {file = "pytz-2025.1.tar.gz", hash = "sha256:c2db42be2a2518b28e65f9207c4d05e6ff547d1efa4086469ef855e4ab70178e"},
 ]
 
 [[package]]
@@ -2713,4 +2730,4 @@ propcache = ">=0.2.0"
 [metadata]
 lock-version = "2.0"
 python-versions = "^3.11"
-content-hash = "e5d1e788122489e06ea88034aaa51ecefbe7a7b98fc4ea352e6267d0bb5120d9"
+content-hash = "48979e4774bf2313198739af31eb5a4927d143b50b44d3696340e2287a49de18"
diff --git a/pyproject.toml b/pyproject.toml
index c8c9106c..b5ecf040 100644
--- a/pyproject.toml
+++ b/pyproject.toml
@@ -9,7 +9,7 @@ readme = "README.md"
 python = "^3.11"
 torpedo = {git = "ssh://git@bitbucket.org/tata1mg/torpedo.git", tag = "4.0.0"}
 commonutils = {git = "ssh://git@bitbucket.org/tata1mg/commonutils.git", tag = "1.8.6"}
-cache_wrapper = {git = "ssh://git@bitbucket.org/tata1mg/cache_wrapper.git", tag = "4.0.0"}
+cache_wrapper = {git = "ssh://git@bitbucket.org/tata1mg/cache_wrapper.git", rev = "feat/conn-limit"}
 tortoise_wrapper = {git = "ssh://git@bitbucket.org/tata1mg/tortoise_wrapper.git", tag = "4.0.0"}
 packaging = "^24.1"
 feature_flag_sdk = {git = "ssh://git@bitbucket.org/tata1mg/feature_flag_sdk.git", python = ">=3.9,<3.13", branch = "FD-1681-updated"}
"""
