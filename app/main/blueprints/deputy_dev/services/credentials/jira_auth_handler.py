from __future__ import annotations

from .atlassian_auth_handler import AtlassianAuthHandler


class JiraAuthHandler(AtlassianAuthHandler):
    __integration__ = "jira"
    __tokenable_type__ = "integration"
