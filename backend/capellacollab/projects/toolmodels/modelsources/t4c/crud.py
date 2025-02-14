# SPDX-FileCopyrightText: Copyright DB Netz AG and the capella-collab-manager contributors
# SPDX-License-Identifier: Apache-2.0

from collections import abc

import sqlalchemy as sa
from sqlalchemy import orm

from capellacollab.core import database
from capellacollab.projects.toolmodels import models as toolmodels_models
from capellacollab.projects.toolmodels.modelsources.t4c import models
from capellacollab.settings.modelsources.t4c.repositories import (
    models as repositories_models,
)


def get_t4c_model_by_id(
    db: orm.Session, t4c_model_id: int
) -> models.DatabaseT4CModel | None:
    return db.execute(
        sa.select(models.DatabaseT4CModel).where(
            models.DatabaseT4CModel.id == t4c_model_id
        )
    ).scalar_one_or_none()


def get_t4c_models(db: orm.Session) -> abc.Sequence[models.DatabaseT4CModel]:
    return db.execute(sa.select(models.DatabaseT4CModel)).scalars().all()


def get_t4c_models_for_tool_model(
    db: orm.Session, model: toolmodels_models.DatabaseCapellaModel
) -> abc.Sequence[models.DatabaseT4CModel]:
    return (
        db.execute(
            sa.select(models.DatabaseT4CModel).where(
                models.DatabaseT4CModel.model_id == model.id
            )
        )
        .scalars()
        .all()
    )


def create_t4c_model(
    db: orm.Session,
    model: toolmodels_models.DatabaseCapellaModel,
    repository: repositories_models.DatabaseT4CRepository,
    name: str,
) -> models.DatabaseT4CModel:
    t4c_model = models.DatabaseT4CModel(
        name=name, model=model, repository=repository
    )
    db.add(t4c_model)
    db.commit()
    return t4c_model


def patch_t4c_model(
    db: orm.Session,
    t4c_model: models.DatabaseT4CModel,
    patch_model: models.SubmitT4CModel,
) -> models.DatabaseT4CModel:
    database.patch_database_with_pydantic_object(t4c_model, patch_model)

    db.commit()
    return t4c_model


def delete_t4c_model(db: orm.Session, t4c_model: models.DatabaseT4CModel):
    db.delete(t4c_model)
    db.commit()
