# SPDX-FileCopyrightText: Copyright DB Netz AG and the capella-collab-manager contributors
# SPDX-License-Identifier: Apache-2.0


from __future__ import annotations

import typing as t

from pydantic import BaseModel
from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from capellacollab.core.database import Base

from .integrations.models import ToolIntegrations

if t.TYPE_CHECKING:
    from .integrations.models import DatabaseToolIntegrations


class Tool(Base):
    __tablename__ = "tools"

    id: int = Column(Integer, primary_key=True)
    name: str = Column(String)
    docker_image_template: str = Column(String)
    docker_image_backup_template: str = Column(String)
    readonly_docker_image_template = Column(String)

    versions: list[Version] = relationship("Version", back_populates="tool")
    natures: list[Nature] = relationship("Nature", back_populates="tool")

    integrations: DatabaseToolIntegrations = relationship(
        "DatabaseToolIntegrations", back_populates="tool", uselist=False
    )


class Version(Base):
    __tablename__ = "versions"
    __table_args__ = (UniqueConstraint("tool_id", "name"),)

    id: int = Column(Integer, primary_key=True)
    name: str = Column(String)
    is_recommended: bool = Column(Boolean)
    is_deprecated: bool = Column(Boolean)

    tool_id: int = Column(Integer, ForeignKey(Tool.id))
    tool: Tool = relationship("Tool", back_populates="versions")


class Nature(Base):
    __tablename__ = "types"
    __table_args__ = (UniqueConstraint("tool_id", "name"),)

    id: int = Column(Integer, primary_key=True)
    name: str = Column(String)

    tool_id: int = Column(Integer, ForeignKey(Tool.id))
    tool: Tool = relationship("Tool", back_populates="natures")


class ToolBase(BaseModel):
    id: int
    name: str
    integrations: ToolIntegrations

    class Config:
        orm_mode = True


class ToolDockerimage(BaseModel):
    persistent: str
    readonly: str | None
    backup: str | None

    @classmethod
    def from_orm(cls, obj: Tool) -> ToolDockerimage:
        return ToolDockerimage(
            persistent=obj.docker_image_template,
            readonly=obj.readonly_docker_image_template,
            backup=obj.docker_image_backup_template,
        )

    class Config:
        orm_mode = True


class PatchToolDockerimage(BaseModel):
    persistent: str | None
    readonly: str | None
    backup: str | None


class CreateToolVersion(BaseModel):
    name: str


class CreateToolNature(BaseModel):
    name: str


class UpdateToolVersion(BaseModel):
    name: str | None
    is_recommended: bool | None
    is_deprecated: bool | None


class ToolVersionBase(BaseModel):
    id: int
    name: str
    is_recommended: bool
    is_deprecated: bool

    class Config:
        orm_mode = True


class ToolVersionWithTool(ToolVersionBase):
    tool: ToolBase


class ToolNatureBase(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class CreateTool(BaseModel):
    name: str
