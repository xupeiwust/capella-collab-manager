# SPDX-FileCopyrightText: Copyright DB Netz AG and the capella-collab-manager contributors
# SPDX-License-Identifier: Apache-2.0

from capellacollab.tools import models as tools_models

from . import interface, jupyter, persistent_workspace, pure_variants, t4c

REGISTERED_HOOKS: dict[str, interface.HookRegistration] = {
    "jupyter": jupyter.JupyterIntegration(),
    "t4c": t4c.T4CIntegration(),
    "pure_variants": pure_variants.PureVariantsIntegration(),
}

REGISTER_HOOKS_AUTO_USE: dict[str, interface.HookRegistration] = {
    "persistent_workspace": persistent_workspace.PersistentWorkspaceHook(),
}


def get_activated_integration_hooks(
    tool: tools_models.DatabaseTool,
) -> list[interface.HookRegistration]:
    """Returns a list of all activated integration hooks for a tool."""
    return [
        hook
        for integration, hook in REGISTERED_HOOKS.items()
        if getattr(tool.integrations, integration, False)
    ] + list(REGISTER_HOOKS_AUTO_USE.values())
