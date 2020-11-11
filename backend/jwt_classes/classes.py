from backend.jwt_classes.access_levels import Private, Personal, Public
from typing import Optional, TypeVar
from backend.jwt_classes import JwtObject

AL = TypeVar('AL')


class Authorization(JwtObject[AL]):
    __type__ = 1
    _id: int


class Patient(JwtObject[AL]):
    __type__ = 2
    _id: int
    name: str
    email: str
    cpf: str


class Professional(JwtObject[AL]):
    __type__ = 3
    _id: int
    name: Public.wrap(str)
    registration_id: Public.wrap(str)
    email: Personal.wrap(str)
    institution: Personal.wrap(str)
    cpf: Private.wrap(str)
