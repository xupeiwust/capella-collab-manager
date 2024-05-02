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

import { GitModel } from './git-model';
import { T4CModel } from './t4-c-model';
import { ToolVersion } from './tool-version';
import { ToolModelRestrictions } from './tool-model-restrictions';
import { Tool } from './tool';
import { ToolNature } from './tool-nature';


export interface CapellaModel { 
    id: number;
    slug: string;
    name: string;
    description: string;
    display_order: number | null;
    tool: Tool;
    version: ToolVersion | null;
    nature: ToolNature | null;
    git_models: Array<GitModel> | null;
    t4c_models: Array<T4CModel> | null;
    restrictions: ToolModelRestrictions | null;
}

