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

import { ToolSessionSharingConfigurationOutput } from './tool-session-sharing-configuration-output';
import { RDPPortsOutput } from './rdp-ports-output';
import { EnvironmentValue1 } from './environment-value1';


export interface GuacamoleConnectionMethodOutput { 
    id: string;
    type: GuacamoleConnectionMethodOutput.TypeEnum;
    name: string;
    description: string;
    ports: RDPPortsOutput;
    /**
     * Connection method specific environment variables. Check the global environment field for more information. 
     */
    environment: { [key: string]: EnvironmentValue1; };
    sharing: ToolSessionSharingConfigurationOutput;
}
export namespace GuacamoleConnectionMethodOutput {
    export type TypeEnum = 'guacamole';
    export const TypeEnum = {
        Guacamole: 'guacamole' as TypeEnum
    };
}


