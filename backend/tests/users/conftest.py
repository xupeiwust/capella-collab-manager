# SPDX-FileCopyrightText: Copyright DB Netz AG and the capella-collab-manager contributors
# SPDX-License-Identifier: Apache-2.0

from uuid import uuid1

import pytest

import capellacollab.users.crud as users_crud
from capellacollab.__main__ import app
from capellacollab.users import injectables as users_injectables
from capellacollab.users import models as users_models


@pytest.fixture(name="unauthenticated_user")
def fixture_unauthenticated_user(db):
    user = users_crud.create_user(db, str(uuid1()), users_models.Role.USER)

    def get_mock_own_user():
        return user

    app.dependency_overrides[
        users_injectables.get_own_user
    ] = get_mock_own_user
    yield user
    del app.dependency_overrides[users_injectables.get_own_user]
