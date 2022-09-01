# SPDX-FileCopyrightText: Copyright DB Netz AG and the capella-collab-manager contributors
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import enum
import typing as t

from pydantic import BaseModel
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

import capellacollab.projects.capellamodels.models

# Import required for sqlalchemy
from capellacollab.core.database import Base


class UserMetadata(BaseModel):
    leads: int
    contributors: int
    subscribers: int


class Project(BaseModel):
    name: str
    slug: str
    description: t.Optional[str]
    users: UserMetadata

    class Config:
        orm_mode = True


class PatchProject(BaseModel):
    description: str


class PostProjectRequest(BaseModel):
    name: str
    description: t.Optional[str]


class DatabaseProject(Base):
    __tablename__ = "projects"

    id = Column(Integer, unique=True, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    slug = Column(String, unique=True, index=True, nullable=False)
    description = Column(String)
    users = relationship(
        "ProjectUserAssociation",
        back_populates="projects",
    )
    models = relationship("DatabaseCapellaModel", back_populates="project")
