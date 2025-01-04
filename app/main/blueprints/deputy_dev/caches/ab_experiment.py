from app.backend_common.caches.base import Base


class ABExperimentCache(Base):
    _key_prefix = "ab_experiment"
