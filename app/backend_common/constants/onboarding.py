from enum import Enum


class UserRoles(str, Enum):
    ADMIN = "admin"
    MEMBER = "member"

class SubscriptionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    CANCELLED = "CANCELLED"
