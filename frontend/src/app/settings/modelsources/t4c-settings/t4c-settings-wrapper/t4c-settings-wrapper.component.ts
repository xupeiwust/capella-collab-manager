/*
 * SPDX-FileCopyrightText: Copyright DB Netz AG and the capella-collab-manager contributors
 * SPDX-License-Identifier: Apache-2.0
 */

import { Component, OnDestroy, OnInit } from '@angular/core';
import { T4CInstanceService } from 'src/app/services/settings/t4c-instance.service';

@Component({
  selector: 'app-t4c-settings-wrapper',
  templateUrl: './t4c-settings-wrapper.component.html',
  styleUrls: ['./t4c-settings-wrapper.component.css'],
})
export class T4CSettingsWrapperComponent implements OnInit, OnDestroy {
  constructor(public t4cInstanceService: T4CInstanceService) {}

  ngOnInit(): void {
    this.t4cInstanceService.loadInstances();
  }

  ngOnDestroy(): void {
    this.t4cInstanceService.reset();
  }
}
