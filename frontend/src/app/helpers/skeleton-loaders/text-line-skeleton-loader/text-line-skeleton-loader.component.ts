/*
 * SPDX-FileCopyrightText: Copyright DB Netz AG and the capella-collab-manager contributors
 * SPDX-License-Identifier: Apache-2.0
 */

import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-text-line-skeleton-loader',
  templateUrl: './text-line-skeleton-loader.component.html',
  styleUrls: ['./text-line-skeleton-loader.component.css'],
})
export class TextLineSkeletonLoaderComponent {
  @Input()
  width = '20%';
}
