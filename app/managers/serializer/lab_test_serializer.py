from app.constants.constants import CtaActions


class LabTestSerializer:
    @classmethod
    def get_test_relevant_data(cls, lab_test_details):
        test_basic_details = None
        test_price_details = None
        test_sku_ga_details = None
        for data in lab_test_details:
            if data["type"] == "basic_details":
                test_basic_details = data.get("data")
            elif data["type"] == "lab_price":
                test_price_details = data.get("data")
            elif data["type"] == "lab_education":
                test_sku_ga_details = (
                    data.get("data", {}).get("ga_data", {}).get("label")
                )
        return {
            "basic_details": test_basic_details,
            "price_details": test_price_details,
            "ga_details": test_sku_ga_details,
        }

    @classmethod
    def format_lab_test_data(cls, lab_test_details):
        lab_test_relevant_data = cls.get_test_relevant_data(lab_test_details)
        lab_test_basic_details = lab_test_relevant_data.get("basic_details")
        lab_test_price_details = lab_test_relevant_data.get("price_details")
        lab_ga_details = lab_test_relevant_data.get("ga_details")

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
            "sku_id": lab_ga_details.get("sku_id"),
        }
