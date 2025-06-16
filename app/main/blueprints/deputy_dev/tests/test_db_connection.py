from app.backend_common.repository.db import DB
from app.main.blueprints.deputy_dev.models.dao.postgres import PRComments


class TestDbConnection:
    @classmethod
    async def test_organisations(cls):
        # validated
        # Organisations
        # OrgScmAccounts
        # Repos
        # Workspaces
        # PullRequests
        # PRComments
        rows = await DB.by_filters(
            PRComments,
            where_clause={},
            offset=0,
            limit=100,
            order_by=[],
        )
        return rows
