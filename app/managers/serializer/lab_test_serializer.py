from app.constants.constants import CtaActions
from app.constants.constants import LabSkuCardImage


class LabSkuSerializer:
    @classmethod
    def get_test_relevant_data(cls, lab_test_data):
        test_basic_details, test_price_details = {}, {}
        for data in lab_test_data:
            if data["type"] == "basic_details":
                test_basic_details = data.get("data")
            elif data["type"] == "lab_price":
                test_price_details = data.get("data")
        return {
            "basic_details": test_basic_details,
            "price_details": test_price_details,
        }

    @classmethod
    def format_lab_sku_data(cls, lab_sku_details):
        lab_test_relevant_data = cls.get_test_relevant_data(lab_sku_details.get("data"))
        lab_test_basic_details = lab_test_relevant_data.get("basic_details")
        lab_test_price_details = lab_test_relevant_data.get("price_details")
        lab_ga_details = lab_sku_details.get("analytics_data", {}).get("event_properties")
        lab_sku_type = lab_sku_details.get("meta", {}).get("type")
        lab_sku_image = (
            LabSkuCardImage.Lab_Test.value
            if lab_sku_type == "test"
            else LabSkuCardImage.Lab_Package.value
        )

        return {
            "header": lab_test_basic_details.get("title"),
            "sub_header": lab_test_basic_details.get("acronym"),
            "cta": {
                "action": CtaActions.ADD_TO_CART.value,
                "text": "Book",
                "details": {
                    "target_url": lab_test_basic_details.get("cta")
                    .get("details")
                    .get("target_url")
                },
            },
            "eta": lab_test_basic_details.get("eta"),
            "slug_url": lab_test_basic_details.get("pdp_slug_url"),
            "price": lab_test_price_details.get("price"),
            "sku_id": str(lab_ga_details.get("entity_id")),
            "sku_type": lab_sku_type,
            "sku_image": lab_sku_image,
            "target_url": lab_test_basic_details.get("cta").get("details").get("target_url"),
        }
