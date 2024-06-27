from app.main.blueprints.jiva.models.initialize_jiva import InitializeJivaResponseModel


class InitializeJivaSerializer:
    @classmethod
    def format_jiva(cls, show_jiva):
        return InitializeJivaResponseModel(show_jiva=show_jiva)
