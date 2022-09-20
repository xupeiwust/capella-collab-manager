/*
 * SPDX-FileCopyrightText: Copyright DB Netz AG and the capella-collab-manager contributors
 * SPDX-License-Identifier: Apache-2.0
 */

import { Component } from '@angular/core';

import { NavBarService } from '../general/navbar/service/nav-bar.service';
import {
  Project,
  ProjectService,
} from 'src/app/services/project/project.service';
import { SessionService } from '../services/session/session.service';

@Component({
  selector: 'app-workspace',
  templateUrl: './workspace.component.html',
  styleUrls: ['./workspace.component.css'],
})
export class WorkspaceComponent {
  repositories: Project[] = [];
  showSpinner = true;

  constructor(
    public sessionService: SessionService,
    private projectService: ProjectService,
    private navbarService: NavBarService
  ) {
    this.navbarService.title = 'Workspaces';
  }

  ngOnInit() {
    this.projectService.list().forEach((res: Project[]) => {
      this.repositories = res;
    });
  }
}
