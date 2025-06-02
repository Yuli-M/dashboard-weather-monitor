from sqlalchemy import Column, String, Text, DateTime, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from api.models.base import Base

class Payment(Base):
    __tablename__ = 'payments'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('profiles.id'))
    amount = Column(Numeric, nullable=False)
    payment_date = Column(DateTime)
    method = Column(Text)
    status = Column(Text)
    expires_at = Column(DateTime)
