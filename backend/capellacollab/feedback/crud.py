# SPDX-FileCopyrightText: Copyright DB InfraGO AG and contributors
# SPDX-License-Identifier: Apache-2.0

import datetime

import sqlalchemy as sa
from sqlalchemy import orm

from capellacollab.users import models as users_models

from . import models


def count_feedback_by_rating(
    db: orm.Session,
) -> dict[models.FeedbackRating, int]:
    return {
        value[0]: value[1]
        for value in db.execute(
            sa.select(
                models.DatabaseFeedback.rating, sa.func.count()
            ).group_by(models.DatabaseFeedback.rating)
        ).all()
    }


def save_feedback(
    db: orm.Session,
    rating: models.FeedbackRating,
    user: users_models.DatabaseUser | None,
    feedback_text: str | None,
    created_at: datetime.datetime,
    trigger: str | None,
) -> models.DatabaseFeedback:
    model = models.DatabaseFeedback(
        rating=rating,
        user=user,
        feedback_text=feedback_text,
        created_at=created_at,
        trigger=trigger,
    )

    db.add(model)
    db.commit()
    db.refresh(model)
    return model


def anonymize_feedback_of_user(
    db: orm.Session, user: users_models.DatabaseUser
):
    db.execute(
        sa.update(models.DatabaseFeedback)
        .where(models.DatabaseFeedback.user_id == user.id)
        .values(user_id=None)
    )
    db.commit()
