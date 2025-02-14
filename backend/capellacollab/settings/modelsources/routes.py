# SPDX-FileCopyrightText: Copyright DB Netz AG and the capella-collab-manager contributors
# SPDX-License-Identifier: Apache-2.0

import fastapi

from capellacollab.settings.modelsources.git import (
    routes as settings_git_routes,
)
from capellacollab.settings.modelsources.t4c import (
    routes as settings_t4c_routes,
)

router = fastapi.APIRouter()

router.include_router(
    settings_git_routes.router,
    prefix="/git",
    tags=["Settings - Modelsources - Git"],
)
router.include_router(
    settings_t4c_routes.router,
    prefix="/t4c",
    tags=["Settings - Modelsources - T4C"],
)
