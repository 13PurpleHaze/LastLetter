from enum import IntEnum, StrEnum


class RoleId(IntEnum):
    ADMIN = 1
    PARENT = 2
    CHILD = 3
    VERIFIER = 4


class RoleSlug(StrEnum):
    ADMIN = "admin"
    PARENT = "parent"
    CHILD = "child"
    VERIFIER = "verifier"
