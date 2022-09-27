/*
 * SPDX-FileCopyrightText: Copyright DB Netz AG and the capella-collab-manager contributors
 * SPDX-License-Identifier: Apache-2.0
 */

import { Component, OnDestroy, OnInit } from '@angular/core';
import {
  AbstractControl,
  FormControl,
  FormGroup,
  ValidationErrors,
  ValidatorFn,
  Validators,
} from '@angular/forms';
import { MatDialog, MatDialogRef } from '@angular/material/dialog';
import { Subscription } from 'rxjs';
import { NavBarService } from 'src/app/general/navbar/service/nav-bar.service';
import { absoluteUrlSafetyValidator } from 'src/app/helpers/validators/url-validator';
import {
  GitSetting,
  GitSettingsService,
  GitType,
} from 'src/app/services/settings/git-settings.service';
import { DeleteGitSettingsDialogComponent } from 'src/app/settings/modelsources/git-settings/delete-git-settings-dialog/delete-git-settings-dialog.component';

@Component({
  selector: 'app-git-settings',
  templateUrl: './git-settings.component.html',
  styleUrls: ['./git-settings.component.css'],
})
export class GitSettingsComponent implements OnInit, OnDestroy {
  public cmpGitSettings: GitSetting[];

  gitInstancesForm = new FormGroup({
    type: new FormControl('', Validators.required),
    name: new FormControl('', [Validators.required, this.nameValidator()]),
    url: new FormControl('', [
      Validators.required,
      absoluteUrlSafetyValidator(),
    ]),
  });

  private gitSettingsSubscription?: Subscription;

  constructor(
    private navbarService: NavBarService,
    private gitSettingsService: GitSettingsService,
    public dialog: MatDialog,
    public dialogRef: MatDialogRef<DeleteGitSettingsDialogComponent>
  ) {
    this.navbarService.title = 'Settings / Modelsources / Git';
    this.cmpGitSettings = [];
  }

  ngOnInit(): void {
    this.gitSettingsService.gitSettings.subscribe((gitSettings) => {
      this.cmpGitSettings = gitSettings;
    });

    this.gitSettingsService.loadGitSettings();
  }

  createGitSettings(): void {
    if (this.gitInstancesForm.valid) {
      let url = this.gitInstancesForm.value.url!;
      if (url.endsWith('/')) {
        url = url.slice(0, -1);
      }

      this.gitSettingsService
        .createGitSettings({
          name: this.gitInstancesForm.value.name!,
          url: url,
          type: this.gitInstancesForm.value.type as GitType,
        })
        .subscribe((_) => this.gitInstancesForm.reset());
    }
  }

  deleteGitSettings(id: number): void {
    const toDeleteGitSetting: GitSetting = this.cmpGitSettings.find(
      (gitSetting) => gitSetting.id == id
    )!;
    this.dialog
      .open(DeleteGitSettingsDialogComponent, {
        data: toDeleteGitSetting,
      })
      .afterClosed()
      .subscribe((response) => {
        if (response) {
          this.gitSettingsService.deleteGitSettings(id).subscribe((_) => {});
        }
      });
  }

  nameValidator(): ValidatorFn {
    return (control: AbstractControl): ValidationErrors | null => {
      let newInstanceName = control.value;
      let gitSettingNames: string[] = this.cmpGitSettings?.map(
        (gitSetting) => gitSetting.name
      );
      gitSettingNames ??= [];

      for (let gitSettingName of gitSettingNames) {
        if (gitSettingName == newInstanceName) {
          return { uniqueName: { value: gitSettingName } };
        }
      }
      return null;
    };
  }
}
