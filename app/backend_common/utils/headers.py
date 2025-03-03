import json


class Headers:
    def __init__(self, headers):
        self.shared_context = json.loads(headers.get("X-SHARED-CONTEXT", "{}"))
        self.client = headers.get("X-CLIENT")
        self.client_version = headers.get("X-CLIENT-VERSION")

    def __str__(self):
        return json.dumps(self.shared_context)

    def user_context(self):
        return self.shared_context.get("user_context") or {}

    def user_id(self):
        return self.user_context().get("user_id")

    def email(self):
        return self.user_context().get("email")

    def pincode_context(self):
        return self.shared_context.get("pincode_context") or {}

    def client(self):
        return self.client

    def client_version(self):
        return self.client_version

    def pin_code(self):
        return self.pincode_context().get("pincode")

    def is_mobileweb(self):
        return True if self.client == "mobileweb" else False

    def is_android(self):
        return True if self.client == "android" else False

    def is_city_serviceable(self):
        return self.pincode_context().get("is_city_serviceable")

    def user_last_order_info(self):
        return self.user_context().get("user_last_order_info") or None

    def pincode(self):
        return self.pincode_context().get("pincode")

    def city(self):
        city = self.pincode_context().get("city")
        return city.lower() if city else None

    def corporate_details(self):
        return self.user_context().get("corporate_details")

    def corporate_id(self):
        if self.corporate_details():
            return self.corporate_details().get("name")

    def user_cohort(self):
        return None

    def visitor_id(self):
        return self.user_context().get("visitor_id")
