from app.constants import InitializeBoatFields
from app.models.initialize_boat import InitializeBoatResponseModel


class InitializeBoatSerializer:
    @classmethod
    def format_boat(cls, show_boat):
        return InitializeBoatResponseModel(
            show_boat=show_boat,
            boat_name=InitializeBoatFields.BOAT_NAME.value,
            boat_logo=InitializeBoatFields.BOAT_LOGO.value,
            welcome_msg=InitializeBoatFields.WELCOME_MESSAGE.value
        )

