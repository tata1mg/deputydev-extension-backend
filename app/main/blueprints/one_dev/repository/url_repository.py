from app.main.blueprints.one_dev.models.dto.url import UrlDto
from app.main.blueprints.one_dev.models.dao.postgres.urls import Url
from app.backend_common.repository.db import DB


class UrlRepository:
    @classmethod
    async def save_url(cls, payload: UrlDto) -> UrlDto:
        where_clause = {"url": payload.url, "user_team_id": payload.user_team_id}
        url = await DB.by_filters(Url, where_clause=where_clause, fetch_one=True)
        if url:
            payload.id = url["id"]
            await DB.update_by_filters(url, Url, payload.model_dump(exclude={"id"}), where_clause=where_clause)
        else:
            url = await DB.insert_row(Url, payload.model_dump(exclude={"id"}))
            payload.id = url.id
        return payload

    @classmethod
    async def delete_url(cls, url_id: int):
        await Url.filter(id=url_id).update(is_deleted=True)

    @classmethod
    async def update_url(cls, paylaod: UrlDto) -> UrlDto:
        await Url.filter(id=paylaod.id).update(name=paylaod.name)
        url_dict = await DB.by_filters(Url, where_clause={"id": paylaod.id}, fetch_one=True)
        paylaod.url, paylaod.last_indexed = url_dict.get("url"), url_dict.get("last_indexed")
        return paylaod

    @classmethod
    async def list_urls_with_count(cls, user_team_id, limit, offset):
        urls = (
            await Url.filter(user_team_id=user_team_id, is_deleted=False)
            .order_by("-created_at")
            .offset(offset)
            .limit(limit)
        )
        urls = [await url.to_dict() for url in urls]
        count = await Url.filter(user_team_id=user_team_id, is_deleted=False).count()
        return urls, count
