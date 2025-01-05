from app.backend_common.caches.base import Base


class RepoSettingCache(Base):
    _key_prefix = "deputy_dev:repo_setting"
