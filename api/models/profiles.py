from sqlalchemy import Column, String, Boolean, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import validates
from dateutil.parser import parse

from api.models.base import Base

class Profile(Base):
    __tablename__ = 'profiles'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(Text)
    lastname = Column(Text)
    updated_at = Column(DateTime)
    active = Column(Boolean, default=False)
    role = Column(Text)

    @validates('updated_at')
    def validate_updated_at(self, key, value):
        if isinstance(value, str):
            return parse(value)
        return value
