"""SQLAlchemy ORM models for ESG Copilot."""

from datetime import datetime
from typing import List, Optional
import uuid

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    Boolean,
    TypeDecorator,
    CHAR,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class UUID(TypeDecorator):
    """Platform-independent UUID type.

    Uses PostgreSQL's UUID type when available, otherwise stores as CHAR(36).
    """
    impl = CHAR(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value
        if isinstance(value, uuid.UUID):
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


# Association table for many-to-many relationship between Portfolio and Asset
portfolio_assets = Table(
    "portfolio_assets",
    Base.metadata,
    Column("portfolio_id", UUID(), ForeignKey("portfolios.id", ondelete="CASCADE"), primary_key=True),
    Column("asset_id", UUID(), ForeignKey("assets.id", ondelete="CASCADE"), primary_key=True),
)


class UserDB(Base):
    """User model for portfolio ownership."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    portfolios: Mapped[List["PortfolioDB"]] = relationship("PortfolioDB", back_populates="user", cascade="all, delete-orphan")


class AssetDB(Base):
    """Asset model representing a portfolio holding."""

    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    ticker: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    sector: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    region: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    revenue_usd_m: Mapped[float] = mapped_column(Float, nullable=False)
    scope1_tco2e: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    scope2_tco2e: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    green_revenue_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    controversies: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    portfolios: Mapped[List["PortfolioDB"]] = relationship(
        "PortfolioDB", secondary=portfolio_assets, back_populates="assets"
    )


class PortfolioDB(Base):
    """Portfolio model containing multiple assets."""

    __tablename__ = "portfolios"

    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    user: Mapped[Optional["UserDB"]] = relationship("UserDB", back_populates="portfolios")
    assets: Mapped[List["AssetDB"]] = relationship(
        "AssetDB", secondary=portfolio_assets, back_populates="portfolios", lazy="selectin"
    )


class ScenarioDB(Base):
    """Climate scenario model for stress testing."""

    __tablename__ = "scenarios"

    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    carbon_price: Mapped[float] = mapped_column(Float, nullable=False)
    revenue_shock: Mapped[float] = mapped_column(Float, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
