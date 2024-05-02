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

import { HTTPPortsOutput } from './http-ports-output';
import { Environment1 } from './environment1';


export interface HTTPConnectionMethodOutput { 
    id: string;
    type: HTTPConnectionMethodOutput.TypeEnum;
    name: string;
    description: string;
    ports: HTTPPortsOutput;
    /**
     * Connection method specific environment variables. Check the global environment field for more information. 
     */
    environment: object;
    redirect_url: string;
    /**
     * Cookies, which are required to connect to the session. 
     */
    cookies: { [key: string]: string; };
}
export namespace HTTPConnectionMethodOutput {
    export type TypeEnum = 'http';
    export const TypeEnum = {
        Http: 'http' as TypeEnum
    };
}


