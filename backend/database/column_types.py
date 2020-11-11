backend_level_encryption = False

import datetime
import functools
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    Set,
    TYPE_CHECKING,
    Type,
    TypeVar,
    Union,
    cast,
    Tuple,
    overload,
)

try:
    from typing import Literal # type: ignore

except:
    from typing_extensions import Literal

import flask_sqlalchemy
import datetime
from backend.constants import CONSTANTS

if TYPE_CHECKING:
    from sqlalchemy.ext.declarative import DeclarativeMeta
    import sqlalchemy.sql.type_api as type_api
    import sqlalchemy.sql.schema as schema
    import sqlalchemy.orm as orm

    class Modell:
        metadata: schema.MetaData
        query: Any

        def __init__(self, *args, **kwargs) -> None:
            pass

    class Session(orm.scoping.scoped_session):
        delete: Callable[[Modell], None]
        add: Callable[[Modell], None]
        commit: Callable[[], None]
        query: Any

    class SqlA(flask_sqlalchemy.SQLAlchemy):
        Column: Type[schema.Column]
        ForeignKey: Type[schema.ForeignKey]
        relationship: Type[orm.relationship]
        TypeDecorator: Type[type_api.TypeDecorator]
        Table: Type[schema.Table]
        session: Session
        Model: Type[Modell]
        Integer: Any
        Float: Any
        String: Any
        LargeBinary: Any
        DateTime: Any
        Boolean: Any


db = flask_sqlalchemy.SQLAlchemy()
db = cast('SqlA', db)
T = TypeVar('T')
#print('imported')
#print('making adapter')

models = db
Base = models.Model
TB = TypeVar('TB', bound=Base)
class Gettable():
    
    @classmethod
    def get(cls:Type[TB], id: int):
        u: Optional[TB] = cls.query.get(id)
        return u

_Column = models.Column
_Integer: Type[int] = models.Integer
_Float: Type[float] = models.Float
_String = models.String
_Binary = models.LargeBinary
_DateTime: Type[datetime.datetime] = models.DateTime(timezone=True)
_Boolean: Type[bool] = models.Boolean

ForeignKey = models.ForeignKey
_relationship = models.relationship
# backref = models.backref # chose to not use this. Zen of python: explicit is better than implicit. Use back_populates

Table = models.Table
TypeDecorator = db.TypeDecorator


class TZDateTime(TypeDecorator):
    impl = _DateTime

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            return value.replace(tzinfo=datetime.timezone.utc)


def NullColumn(t: T, *args, **kwargs) -> Optional[T]:
    assert 'nullable' not in kwargs
    return _Column(t, *args, **kwargs, nullable=True)


def Column(t: T, *args, **kwargs) -> T:
    assert 'nullable' not in kwargs
    return _Column(t, *args, **kwargs, nullable=False)


@functools.wraps(_relationship)
def relationship(*args, lazy=True, **kwargs):
    return _relationship(*args, **kwargs, lazy=lazy)


if backend_level_encryption:
    from sqlalchemy_utils import EncryptedType
    from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine

    def enc(t: Type[T]) -> T:
        return EncryptedType(t, CONSTANTS.key, AesEngine, 'pkcs5')
else:

    def enc(t: Type[T]) -> T:
        return t


def fix_sqlalch_type(t: Type[T]) -> T:
    return t


def __String(size: Optional[int]) -> str:
    if size is None:
        return enc(_String)
    else:
        return enc(_String(size))


def Binary(size: Optional[int]) -> bytes:
    if size is None:
        return enc(_Binary)
    else:
        return enc(_Binary(size))


Boolean = enc(_Boolean)
DateTime = cast(datetime.datetime, enc(TZDateTime))
Float = enc(_Float)
Index = fix_sqlalch_type(_Integer)
EncryptedInteger = enc(_Integer)
StringBig = __String(10000)
StringMedium = __String(512)
StringSmall = __String(128)
