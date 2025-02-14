/*
 * SPDX-FileCopyrightText: Copyright DB Netz AG and the capella-collab-manager contributors
 * SPDX-License-Identifier: Apache-2.0
 */

import { Component, OnDestroy, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { UntilDestroy, untilDestroyed } from '@ngneat/until-destroy';
import { map } from 'rxjs';
import { BreadcrumbsService } from 'src/app/general/breadcrumbs/breadcrumbs.service';
import { ModelService } from 'src/app/projects/models/service/model.service';
import { ProjectService } from '../service/project.service';

@UntilDestroy()
@Component({
  selector: 'app-project-wrapper',
  templateUrl: './project-wrapper.component.html',
  styleUrls: ['./project-wrapper.component.css'],
})
export class ProjectWrapperComponent implements OnInit, OnDestroy {
  constructor(
    private route: ActivatedRoute,
    public projectService: ProjectService,
    public modelService: ModelService,
    private breadcrumbsService: BreadcrumbsService,
  ) {}

  ngOnInit(): void {
    this.route.params
      .pipe(
        map((params) => params.project),
        untilDestroyed(this),
      )
      .subscribe((projectSlug: string) => {
        this.projectService.loadProjectBySlug(projectSlug);
        this.modelService.loadModels(projectSlug);
      });

    this.projectService.project$
      .pipe(untilDestroyed(this))
      .subscribe((project) =>
        this.breadcrumbsService.updatePlaceholder({ project }),
      );
  }

  ngOnDestroy(): void {
    this.projectService.clearProject();
    this.modelService.clearModel();
    this.modelService.clearModels();
    this.breadcrumbsService.updatePlaceholder({
      project: undefined,
    });
  }
}
