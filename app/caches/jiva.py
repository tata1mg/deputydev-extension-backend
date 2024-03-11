from .base import Base


class Jiva(Base):
    _key_prefix = "jiva"
    expiry_time = 1296000  # 15 days 15*24*60*60 = 1296000
