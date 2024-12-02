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
import { HTTPConnectionMethodOutput } from './http-connection-method-output';
import { GuacamoleConnectionMethodOutput } from './guacamole-connection-method-output';
import { HTTPPortsOutput } from './http-ports-output';
import { EnvironmentValue1 } from './environment-value1';


export interface ToolSessionConnectionOutputMethodsInner { 
    id: string;
    type: ToolSessionConnectionOutputMethodsInner.TypeEnum;
    name: string;
    description: string;
    ports: HTTPPortsOutput;
    /**
     * Connection method specific environment variables. Check the global environment field for more information. 
     */
    environment: { [key: string]: EnvironmentValue1; };
    sharing: ToolSessionSharingConfigurationOutput;
    redirect_url: string;
    /**
     * Cookies, which are required to connect to the session. 
     */
    cookies: { [key: string]: string; };
}
export namespace ToolSessionConnectionOutputMethodsInner {
    export type TypeEnum = 'guacamole' | 'http';
    export const TypeEnum = {
        Guacamole: 'guacamole' as TypeEnum,
        Http: 'http' as TypeEnum
    };
}


