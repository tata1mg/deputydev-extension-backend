from app.main.blueprints.one_dev.models.dto.url import UrlDto
from app.main.blueprints.one_dev.models.dao.postgres.urls import Url
from app.backend_common.repository.db import DB


class UrlRepository:
    @classmethod
    async def save_url(cls, payload: UrlDto):
        where_clause = {"url": payload.url, "user_team_id": payload.user_team_id}
        url = await DB.by_filters(Url, where_clause=where_clause, fetch_one=True)
        if url:
            payload.id = url["id"]
            await DB.update_by_filters(url, Url, payload.model_dump(exclude={"id"}), where_clause=where_clause)
        else:
            url = await DB.insert_row(Url, payload.model_dump(exclude={"id"}))
            payload.id = url.id
        return payload
