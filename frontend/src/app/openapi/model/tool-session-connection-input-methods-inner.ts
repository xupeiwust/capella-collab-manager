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

import { GuacamoleConnectionMethodInput } from './guacamole-connection-method-input';
import { Environment } from './environment';
import { HTTPConnectionMethodInput } from './http-connection-method-input';
import { ToolSessionSharingConfigurationInput } from './tool-session-sharing-configuration-input';
import { HTTPPortsInput } from './http-ports-input';


export interface ToolSessionConnectionInputMethodsInner { 
    id?: string;
    type?: ToolSessionConnectionInputMethodsInner.TypeEnum;
    name?: string;
    description?: string;
    ports?: HTTPPortsInput;
    /**
     * Connection method specific environment variables. Check the global environment field for more information. 
     */
    environment?: { [key: string]: Environment; };
    sharing?: ToolSessionSharingConfigurationInput;
    redirect_url?: string;
    /**
     * Cookies, which are required to connect to the session. 
     */
    cookies?: { [key: string]: any; };
}
export namespace ToolSessionConnectionInputMethodsInner {
    export type TypeEnum = 'guacamole' | 'http';
    export const TypeEnum = {
        Guacamole: 'guacamole' as TypeEnum,
        Http: 'http' as TypeEnum
    };
}


