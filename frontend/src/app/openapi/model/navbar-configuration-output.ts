/*
 * SPDX-FileCopyrightText: Copyright DB InfraGO AG and contributors
 * SPDX-License-Identifier: Apache-2.0
 *
 * Capella Collaboration Manager API
 *
 * NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).
 * Do not edit the class manually.
 + To generate a new version, run `make openapi` in the root directory of this repository.
 */

import { NavbarConfigurationInputExternalLinksInner } from './navbar-configuration-input-external-links-inner';
import { BadgeOutput } from './badge-output';


export interface NavbarConfigurationOutput { 
    /**
     * Links to display in the navigation bar.
     */
    external_links: Array<NavbarConfigurationInputExternalLinksInner>;
    logo_url: string | null;
    /**
     * Badge to display in the navigation bar.
     */
    badge: BadgeOutput;
}

