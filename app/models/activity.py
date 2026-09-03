from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import Date, DateTime, Index, Numeric, String, Text, Time, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Activity(Base):
    __tablename__ = "activities"  # Nome da tabela no banco de dados

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    activity_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    location_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    latitude: Mapped[Decimal] = mapped_column(
        Numeric(9, 6),
        nullable=False,
    )

    longitude: Mapped[Decimal] = mapped_column(
        Numeric(9, 6),
        nullable=False,
    )

    scheduled_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    scheduled_time: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PLANNED",
        server_default="PLANNED",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        Index("ix_activities_scheduled_date", "scheduled_date"),
        Index("ix_activities_status", "status"),
        Index("ix_activities_activity_type", "activity_type"),
    )
