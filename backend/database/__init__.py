from __future__ import annotations
from dataclasses import dataclass
import datetime
import json
import math
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    Set,
    TYPE_CHECKING,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
    overload,
)

from travel_backpack.exceptions import check_and_raise

from backend import helper_functions
from backend import jwt_classes
from backend.jwt_classes.access_levels import AccessLevels
from backend.constants import CONSTANTS
from backend.database.column_types import (
    Base,
    Binary,
    Boolean,
    Column,
    DateTime,
    EncryptedInteger,
    ForeignKey,
    Index,
    NullColumn,
    StringBig,
    StringMedium,
    StringSmall,
    Table,
    db,
    relationship,
    Gettable,
)
try:
    from typing import Literal  #type: ignore
except:
    from typing_extensions import Literal

if TYPE_CHECKING:
    from backend.database.column_types import Session

_Base = Base
Base = (Base, Gettable)


def init_app(app):
    db.init_app(app)


class User(*Base):  # type: ignore
    # required
    id = Column(Index, primary_key=True)
    email = Column(StringSmall, unique=True)
    name = Column(StringSmall)
    password = Column(Binary(64))
    salt = Column(Binary(128))

    def to_jwt_object(self, auth: bool, subject: Union[User, int]):
        s: int
        if isinstance(subject, User):
            s = subject.id
        else:
            s = subject

        return jwt_classes.User(subject=s, user_id=self.id, name=self.name, auth=auth, email=self.email)

    def to_jwt(self, auth: bool, subject: Union[User, int]):
        jwt_obj = self.to_jwt_object(auth=auth, subject=subject)
        return jwt_obj.to_jwt()