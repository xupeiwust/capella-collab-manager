/*
 * SPDX-FileCopyrightText: Copyright DB Netz AG and the capella-collab-manager contributors
 * SPDX-License-Identifier: Apache-2.0
 */

import {
  Component,
  EventEmitter,
  OnChanges,
  OnInit,
  Output,
  SimpleChanges,
} from '@angular/core';
import { FormControl, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { UntilDestroy, untilDestroyed } from '@ngneat/until-destroy';
import { filter } from 'rxjs';
import slugify from 'slugify';
import { ToastService } from 'src/app/helpers/toast/toast.service';
import { ModelService } from 'src/app/projects/models/service/model.service';
import {
  PatchProject,
  Project,
  ProjectService,
} from '../../service/project.service';

@UntilDestroy()
@Component({
  selector: 'app-project-metadata',
  templateUrl: './project-metadata.component.html',
  styleUrls: ['./project-metadata.component.css'],
})
export class ProjectMetadataComponent implements OnInit, OnChanges {
  @Output() changeProject = new EventEmitter<Project>();

  public canDelete: boolean = false;

  public projectSlug?: string = undefined;
  public projectName?: string = undefined;

  constructor(
    private toastService: ToastService,
    private projectService: ProjectService,
    private modelService: ModelService,
    private router: Router,
    private route: ActivatedRoute
  ) {}

  public form = new FormGroup({
    name: new FormControl<string>('', {
      validators: Validators.required,
      asyncValidators: this.projectService.asyncSlugValidator(),
    }),
    description: new FormControl<string>(''),
  });

  ngOnInit(): void {
    this.projectService.project
      .pipe(untilDestroyed(this), filter(Boolean))
      .subscribe((project) => {
        this.projectSlug = project.slug;
        this.projectName = project.name;
        this.form.patchValue(project);
      });

    this.modelService.models
      .pipe(untilDestroyed(this), filter(Boolean))
      .subscribe((models) => (this.canDelete = !models.length));
  }

  ngOnChanges(_changes: SimpleChanges): void {
    this.projectService.loadProjectBySlug(this.projectSlug!);
  }

  updateDescription() {
    if (this.form.valid && this.projectSlug) {
      this.projectService
        .updateProject(this.projectSlug, this.form.value as PatchProject)
        .subscribe((project) => {
          this.router.navigateByUrl(`/project/${project.slug}`);
          this.toastService.showSuccess(
            'Project updated',
            `The new name is: '${project.name}' and the new description is '${
              project.description || ''
            }'`
          );
        });
    }
  }

  get newSlug(): string | null {
    return this.form.value.name ? slugify(this.form.value.name) : null;
  }

  deleteProject(): void {
    if (
      !this.canDelete ||
      !this.projectSlug ||
      !window.confirm(
        `Do you really want to delete this project? All assigned users will lose access to it! The project cannot be restored!`
      )
    ) {
      return;
    }

    const projectSlug: string = this.projectSlug;

    this.projectService.deleteProject(projectSlug).subscribe({
      next: () => {
        this.toastService.showSuccess(
          'Project deleted',
          `${projectSlug} has been deleted`
        );
        this.router.navigate(['../../projects'], { relativeTo: this.route });
      },
      error: () => {
        this.toastService.showError(
          'Project deletion failed',
          `${projectSlug} has not been deleted`
        );
      },
    });
  }
}
