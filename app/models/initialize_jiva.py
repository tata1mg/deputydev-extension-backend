from pydantic import BaseModel


class InitializeJivaResponseModel(BaseModel):
    show_jiva: bool = True
    thumbnail_url: str = "https://onemg.gumlet.io/jiva_thumbnail.png"
