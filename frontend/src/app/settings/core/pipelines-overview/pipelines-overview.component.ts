/*
 * SPDX-FileCopyrightText: Copyright DB Netz AG and the capella-collab-manager contributors
 * SPDX-License-Identifier: Apache-2.0
 */

import { Component, OnInit } from '@angular/core';
import {
  MonitoringService,
  ProjectStatus,
  ToolmodelStatus,
  GeneralHealth,
} from 'src/app/settings/core/pipelines-overview/service/monitoring.service';

@Component({
  selector: 'app-pipelines-overview',
  templateUrl: './pipelines-overview.component.html',
  styleUrls: ['./pipelines-overview.component.css'],
})
export class PipelinesOverviewComponent implements OnInit {
  constructor(private monitoringService: MonitoringService) {}

  toolmodelStatuses?: ToolmodelStatus[];
  projectStatuses?: ProjectStatus[];
  generalHealth?: GeneralHealth;

  ngOnInit(): void {
    this.monitoringService
      .fetchGeneralHealth()
      .subscribe((generalHealth) => (this.generalHealth = generalHealth));

    this.monitoringService
      .fetchProjectHealth()
      .subscribe((projectStatuses) => (this.projectStatuses = projectStatuses));

    this.monitoringService
      .fetchModelHealth()
      .subscribe(
        (toolmodelStatuses) => (this.toolmodelStatuses = toolmodelStatuses),
      );
  }
}
