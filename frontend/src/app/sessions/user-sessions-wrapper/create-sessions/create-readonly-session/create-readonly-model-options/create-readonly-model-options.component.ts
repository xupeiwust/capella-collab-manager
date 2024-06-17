/*
 * SPDX-FileCopyrightText: Copyright DB InfraGO AG and contributors
 * SPDX-License-Identifier: Apache-2.0
 */

import { NgFor, NgIf } from '@angular/common';
import { Component, Input, OnInit } from '@angular/core';
import {
  Validators,
  FormBuilder,
  ReactiveFormsModule,
  FormsModule,
} from '@angular/forms';
import {
  MatAutocomplete,
  MatAutocompleteTrigger,
  MatOptgroup,
  MatOption,
} from '@angular/material/autocomplete';
import { MatCheckbox } from '@angular/material/checkbox';
import { MatError, MatFormField, MatLabel } from '@angular/material/form-field';
import { MatInput } from '@angular/material/input';
import { MatSlideToggle } from '@angular/material/slide-toggle';
import { filter } from 'rxjs';
import { Tool, ToolModel, ToolVersion } from 'src/app/openapi';
import { GetGitModel } from 'src/app/projects/project-detail/model-overview/model-detail/git-model.service';
import {
  Revisions,
  GitService,
  existingRevisionValidator,
} from 'src/app/services/git/git.service';

export type ModelOptions = {
  model: ToolModel;
  primaryGitModel: GetGitModel;
  include: boolean;
  revision: string;
  deepClone: boolean;
};

@Component({
  selector: 'create-readonly-model-options',
  templateUrl: './create-readonly-model-options.component.html',
  styleUrls: ['./create-readonly-model-options.component.css'],
  standalone: true,
  imports: [
    FormsModule,
    ReactiveFormsModule,
    MatCheckbox,
    NgIf,
    MatFormField,
    MatLabel,
    MatInput,
    MatAutocompleteTrigger,
    MatError,
    MatAutocomplete,
    MatOptgroup,
    NgFor,
    MatOption,
    MatSlideToggle,
  ],
})
export class CreateReadonlyModelOptionsComponent implements OnInit {
  @Input() projectSlug!: string;
  @Input() modelOptions!: ModelOptions;
  @Input() tool!: Tool;
  @Input() toolVersion!: ToolVersion;

  constructor(
    private gitService: GitService,
    private fb: FormBuilder,
  ) {}

  private revisions?: Revisions;
  public filteredRevisions?: Revisions;

  public form = this.fb.group({
    include: [true],
    revision: this.fb.control('', Validators.required),
    deepClone: [false],
  });

  ngOnInit(): void {
    this.form.controls.deepClone.setValue(this.modelOptions.deepClone);
    this.form.controls.include.setValue(this.modelOptions.include);

    // Okay, this is kinda lame, but I need the modelOptions to be up to date with the form
    this.form.controls.deepClone.valueChanges.subscribe((value) => {
      this.modelOptions.deepClone = value || false;
    });
    this.form.controls.include.valueChanges.subscribe((value) => {
      this.modelOptions.include = value || false;
    });
    this.form.controls.revision.valueChanges.subscribe((value) => {
      this.modelOptions.revision =
        value || this.modelOptions.primaryGitModel.revision;
    });

    this.gitService
      .getPrivateRevision(
        this.modelOptions.primaryGitModel.path,
        this.projectSlug,
        this.modelOptions.model.slug,
        this.modelOptions.primaryGitModel.id,
      )
      .pipe(filter(Boolean))
      .subscribe((revisions) => {
        this.revisions = revisions;
        this.filteredRevisions = revisions;

        const revisionControl = this.form.controls.revision;

        revisionControl.addValidators(existingRevisionValidator(revisions));
        revisionControl.setValue(this.modelOptions.primaryGitModel.revision);
        revisionControl.updateValueAndValidity();
      });
  }

  filterRevisionsByPrefix(prefix: string): void {
    if (!this.revisions) {
      this.filteredRevisions = undefined;
      return;
    }

    this.filteredRevisions = {
      branches: this.revisions!.branches.filter((branch) =>
        branch.toLowerCase().startsWith(prefix.toLowerCase()),
      ),
      tags: this.revisions!.tags.filter((tag) =>
        tag.toLowerCase().startsWith(prefix.toLowerCase()),
      ),
    };
  }
}
