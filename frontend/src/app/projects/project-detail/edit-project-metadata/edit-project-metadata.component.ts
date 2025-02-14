/*
 * SPDX-FileCopyrightText: Copyright DB Netz AG and the capella-collab-manager contributors
 * SPDX-License-Identifier: Apache-2.0
 */

import { Component, OnChanges, OnInit, SimpleChanges } from '@angular/core';
import { FormControl, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { UntilDestroy, untilDestroyed } from '@ngneat/until-destroy';
import { filter } from 'rxjs';
import slugify from 'slugify';
import { ToastService } from 'src/app/helpers/toast/toast.service';
import { ProjectUserService } from 'src/app/projects/project-detail/project-users/service/project-user.service';
import {
  PatchProject,
  Project,
  ProjectService,
} from '../../service/project.service';

@UntilDestroy()
@Component({
  selector: 'app-edit-project-metadata',
  templateUrl: './edit-project-metadata.component.html',
  styleUrls: ['./edit-project-metadata.component.css'],
})
export class EditProjectMetadataComponent implements OnInit, OnChanges {
  canDelete = false;
  project?: Project;

  constructor(
    public projectService: ProjectService,
    public projectUserService: ProjectUserService,
    private toastService: ToastService,
    private router: Router,
  ) {}

  form = new FormGroup({
    name: new FormControl<string>('', Validators.required),
    description: new FormControl<string>(''),
    visibility: new FormControl(''),
    type: new FormControl(''),
  });

  ngOnInit(): void {
    this.projectService.project$
      .pipe(untilDestroyed(this), filter(Boolean))
      .subscribe((project) => {
        this.project = project;
        this.form.controls.name.setAsyncValidators(
          this.projectService.asyncSlugValidator(project),
        );
        this.form.patchValue(project);
      });
  }

  ngOnChanges(_changes: SimpleChanges): void {
    if (this.project) {
      this.projectService.loadProjectBySlug(this.project.slug);
    }
  }

  updateProject() {
    if (this.form.valid && this.project) {
      this.projectService
        .updateProject(this.project.slug, this.form.value as PatchProject)
        .subscribe((project) => {
          this.router.navigateByUrl(`/project/${project.slug}`);
          this.toastService.showSuccess(
            'Project updated',
            `The new name is: '${project.name}' and the new description is '${
              project.description || ''
            }'`,
          );
        });
    }
  }

  get newSlug(): string | null {
    return this.form.value.name
      ? slugify(this.form.value.name, { lower: true })
      : null;
  }
}
