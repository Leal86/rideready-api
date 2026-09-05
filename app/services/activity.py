from typing import Any

from sqlalchemy.orm import Session

from app.models.activity import Activity
from app.repositories import activity as activity_repository


def list_activities(db: Session) -> list[Activity]:
    return activity_repository.get_all(db)


def get_activity(db: Session, activity_id: int) -> Activity | None:
    return activity_repository.get_by_id(db, activity_id)


def create_activity(
    db: Session,
    data: dict[str, Any],
) -> Activity:
    return activity_repository.create(db, data)


def update_activity(
    db: Session,
    activity: Activity,
    data: dict[str, Any],
) -> Activity:
    return activity_repository.update(db, activity, data)


def delete_activity(
    db: Session,
    activity: Activity,
) -> None:
    activity_repository.delete(db, activity)


def get_activity_by_schedule(
    db: Session,
    scheduled_date,
    scheduled_time,
):
    return activity_repository.get_by_schedule(
        db,
        scheduled_date,
        scheduled_time,
    )
