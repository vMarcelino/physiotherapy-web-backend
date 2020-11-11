from backend.jwt_classes.access_levels import Private
from typing import Optional, TypeVar
from backend.jwt_classes import JwtObject

AL = TypeVar('AL')


class User(JwtObject[AL]):
    __type__ = 1
    user_id: int
    auth: bool
    name: str
    email: str
