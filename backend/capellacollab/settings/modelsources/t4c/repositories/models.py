# SPDX-FileCopyrightText: Copyright DB Netz AG and the capella-collab-manager contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import enum
import typing as t

import pydantic
import sqlalchemy as sa
from sqlalchemy import orm

from capellacollab.core import database
from capellacollab.settings.modelsources.t4c import models as t4c_models

if t.TYPE_CHECKING:
    from capellacollab.projects.toolmodels.modelsources.t4c.models import (
        DatabaseT4CModel,
    )
    from capellacollab.settings.modelsources.t4c.models import (
        DatabaseT4CInstance,
    )


class DatabaseT4CRepository(database.Base):
    __tablename__ = "t4c_repositories"
    __table_args__ = (sa.UniqueConstraint("instance_id", "name"),)

    id: orm.Mapped[int] = orm.mapped_column(
        primary_key=True, index=True, autoincrement=True, unique=True
    )
    name: orm.Mapped[str]

    instance_id: orm.Mapped[int] = orm.mapped_column(
        sa.ForeignKey("t4c_instances.id")
    )
    instance: orm.Mapped[DatabaseT4CInstance] = orm.relationship(
        back_populates="repositories"
    )

    models: orm.Mapped[list[DatabaseT4CModel]] = orm.relationship(
        back_populates="repository", cascade="all, delete"
    )


class CreateT4CRepository(pydantic.BaseModel):
    name: str = pydantic.Field(
        pattern="^[-a-zA-Z0-9_]+$", examples=["testrepo"]
    )


class T4CRepositoryStatus(str, enum.Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    INSTANCE_UNREACHABLE = "INSTANCE_UNREACHABLE"
    NOT_FOUND = "NOT_FOUND"
    INITIAL = "INITIAL"


class T4CRepository(CreateT4CRepository):
    model_config = pydantic.ConfigDict(from_attributes=True)

    id: int
    instance: t4c_models.T4CInstance
    status: T4CRepositoryStatus | None = None


class T4CInstanceWithRepositories(t4c_models.T4CInstance):
    model_config = pydantic.ConfigDict(from_attributes=True)

    repositories: list[T4CRepository]
