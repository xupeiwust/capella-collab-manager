# SPDX-FileCopyrightText: Copyright DB InfraGO AG and contributors
# SPDX-License-Identifier: Apache-2.0

import typing as t

from capellacollab.core import pydantic as core_pydantic

T = t.TypeVar("T")


class Message(core_pydantic.BaseModel):
    err_code: str | None = None
    title: str | None = None
    reason: str | tuple | None = None
    technical: str | None = None


class ResponseModel(core_pydantic.BaseModel):
    warnings: list[Message] | None = None
    errors: list[Message] | None = None


class PayloadResponseModel(ResponseModel, t.Generic[T]):
    payload: T
