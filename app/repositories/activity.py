from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.activity import Activity


def get_all(db: Session) -> list[Activity]:
    statement = select(Activity).order_by(Activity.scheduled_date, Activity.scheduled_time)

    return list(db.scalars(statement).all())


def get_by_id(db: Session, activity_id: int) -> Activity | None:
    return db.get(Activity, activity_id)


def create(db: Session, data: dict[str, Any]) -> Activity:
    activity = Activity(**data)

    db.add(activity)
    db.commit()
    db.refresh(activity)

    return activity


def update(
    db: Session,
    activity: Activity,
    data: dict[str, Any],
) -> Activity:
    for field, value in data.items():
        setattr(activity, field, value)

    db.commit()
    db.refresh(activity)

    return activity


def delete(db: Session, activity: Activity) -> None:
    db.delete(activity)
    db.commit()