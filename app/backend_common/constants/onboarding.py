from enum import Enum


class UserRoles(str, Enum):
    ADMIN = "admin"
    MEMBER = "member"

class SubscriptionStatus(Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"
