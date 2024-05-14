/*
 * SPDX-FileCopyrightText: Copyright DB InfraGO AG and contributors
 * SPDX-License-Identifier: Apache-2.0
 *
 * Capella Collaboration
 *
 * NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).
 * Do not edit the class manually.
 + To generate a new version, run `make openapi` in the root directory of this repository.
 */

import { ToolSessionConfigurationOutput } from './tool-session-configuration-output';
import { ToolIntegrationsOutput } from './tool-integrations-output';


export interface Tool { 
    /**
     * Unique identifier of the resource.
     */
    id: number;
    name: string;
    integrations: ToolIntegrationsOutput;
    config: ToolSessionConfigurationOutput;
}

