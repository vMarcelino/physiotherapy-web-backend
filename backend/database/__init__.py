from __future__ import annotations
from backend.jwt_classes.classes import Patient
from dataclasses import dataclass
import datetime
from enum import unique
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


def init_app(app):
    db.init_app(app)


class Authorization(Base, Gettable):
    id = Column(Index, primary_key=True)
    email = Column(StringSmall, unique=True)
    password = Column(Binary(64))
    salt = Column(Binary(128))

    # relationships
    _patient: Optional[Patient] = relationship('Patient', back_populates='authorization', uselist=False)
    _professional: Optional[Professional] = relationship('Professional', back_populates='authorization', uselist=False)

    @property
    def owner(self):
        if self._patient is not None:
            return self._patient
        elif self._professional is not None:
            return self._professional
        else:
            raise Exception('patient or professional must be valid')

    def to_jwt_object(self, subject: Union[Authorization, int]):
        s: int
        if isinstance(subject, Authorization):
            s = subject.id
        else:
            s = subject

        return jwt_classes.Authorization(subject=s, _id=self.id)

    def to_jwt(self, subject: Union[Authorization, int]):
        jwt_obj = self.to_jwt_object(subject=subject)
        return jwt_obj.to_jwt()


class Patient(Base, Gettable):
    # required
    id = Column(Index, primary_key=True)
    name = Column(StringSmall)
    cpf = Column(StringSmall, unique=True)
    authorization_id = Column(Index, ForeignKey(Authorization.id))

    # relationships
    authorization: Authorization = relationship(Authorization, back_populates='_patient')
    _links: List[Link] = relationship('Link', back_populates='patient')
    sessions: List[Session] = relationship('Session', back_populates='patient')

    @property
    def links(self):
        return [l for l in self._links if l.accepted]

    @property
    def invites(self):
        return [l for l in self._links if not l.accepted]

    def to_jwt_object(self, subject: Union[Authorization, int], access_level: AccessLevels):
        s: int
        if isinstance(subject, Authorization):
            s = subject.id
        else:
            s = subject

        return jwt_classes.Patient(subject=s,
                                   access_level=access_level,
                                   _id=self.id,
                                   name=self.name,
                                   email=self.authorization.email,
                                   cpf=self.cpf)

    def to_jwt(self, subject: Union[Authorization, int], access_level: AccessLevels):
        jwt_obj = self.to_jwt_object(subject=subject, access_level=access_level)
        return jwt_obj.to_jwt()


class Professional(Base, Gettable):
    # required
    id = Column(Index, primary_key=True)
    name = Column(StringSmall)
    cpf = Column(StringSmall, unique=True)
    registration_id = Column(StringSmall, unique=True)
    institution = Column(StringSmall)
    authorization_id = Column(Index, ForeignKey(Authorization.id))

    # relationships
    authorization: Authorization = relationship(Authorization, back_populates='_professional')
    _links: List[Link] = relationship('Link', back_populates='professional')

    @property
    def links(self):
        return [l for l in self._links if l.accepted]

    @property
    def invites(self):
        return [l for l in self._links if not l.accepted]

    def to_jwt_object(self, subject: Union[Authorization, int], access_level: AccessLevels):
        s: int
        if isinstance(subject, Authorization):
            s = subject.id
        else:
            s = subject

        return jwt_classes.Professional(subject=s,
                                        access_level=access_level,
                                        _id=self.id,
                                        name=self.name,
                                        email=self.authorization.email,
                                        cpf=self.cpf,
                                        registration_id=self.registration_id,
                                        institution=self.institution)

    def to_jwt(self, subject: Union[Authorization, int], access_level: AccessLevels):
        jwt_obj = self.to_jwt_object(subject=subject, access_level=access_level)
        return jwt_obj.to_jwt()


class Link(Base, Gettable):
    id = Column(Index, primary_key=True)
    patient_id = Column(Index, ForeignKey(Patient.id))
    professional_id = Column(Index, ForeignKey(Professional.id))
    accepted = Column(Boolean, default=False)

    # relationships
    patient: Patient = relationship(Patient, back_populates='_links')
    professional: Professional = relationship(Professional, back_populates='_links')


class Session(Base, Gettable):
    id = Column(Index, primary_key=True)
    date = Column(DateTime)
    patient_id = Column(Index, ForeignKey(Patient.id))

    # relationships
    patient: Patient = relationship(Patient, back_populates='sessions')
    videos: List[VideoInfo] = relationship('VideoInfo', back_populates='session')


class VideoInfo(Base, Gettable):
    id = Column(Index, primary_key=True)
    path = Column(StringSmall, unique=True)
    session_id = Column(Index, ForeignKey(Session.id))

    # relationships
    session: Session = relationship(Session, back_populates='videos')