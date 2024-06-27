from enum import Enum


class ExtendedEnum(Enum):
    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


class CtaActions(Enum):
    ADD_TO_CART = "ADD_TO_CART"


class LabSkuCardImage(Enum):
    Lab_Test = "https://onemg.gumlet.io/lab_test_03_01_24.png"
    Lab_Package = "https://onemg.gumlet.io/lab_package_03_01_24.png"


class JivaChatTypes(Enum):
    ChatTypeMsg = "ChatTypeMsg"
    ChatTypeCallAgent = "ChatTypeCallAgent"
    ChatTypeSkuCard = "ChatTypeSkuCard"
    ChatTypePdf = "ChatTypePdf"
