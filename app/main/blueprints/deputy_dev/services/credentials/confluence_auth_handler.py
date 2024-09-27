from __future__ import annotations

from .atlassian_auth_handler import AtlassianAuthHandler


class ConfluenceAuthHandler(AtlassianAuthHandler):
    __integration__ = "confluence"
    __tokenable_type__ = "integration"
