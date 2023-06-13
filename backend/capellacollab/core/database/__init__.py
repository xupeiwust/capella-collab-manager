# SPDX-FileCopyrightText: Copyright DB Netz AG and the capella-collab-manager contributors
# SPDX-License-Identifier: Apache-2.0


import pydantic
import sqlalchemy as sa
from sqlalchemy import orm

from capellacollab.config import config

engine = sa.create_engine(
    config["database"]["url"], connect_args={"connect_timeout": 5}
)
SessionLocal = orm.sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(orm.DeclarativeBase):
    pass


### SQL MODELS ARE IMPORTED HERE ###
from . import models  # isort:skip # pylint: disable=unused-import


def get_db() -> orm.Session:
    with SessionLocal() as session:
        yield session


def patch_database_with_pydantic_object(
    database_object: Base, pydantic_object: pydantic.BaseModel
):
    for key, value in pydantic_object.dict().items():
        if value is not None:
            setattr(database_object, key, value)
