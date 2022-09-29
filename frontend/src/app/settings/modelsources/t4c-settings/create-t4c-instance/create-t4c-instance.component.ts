/*
 * SPDX-FileCopyrightText: Copyright DB Netz AG and the capella-collab-manager contributors
 * SPDX-License-Identifier: Apache-2.0
 */

import { Component, OnInit } from '@angular/core';
import { FormControl, FormGroup, Validators } from '@angular/forms';
import {
  BaseT4CInstance,
  NewT4CInstance,
  T4CInstance,
  T4CInstanceService,
} from '../../../../services/settings/t4c-model.service';
import { BehaviorSubject, filter, map, switchMap, tap } from 'rxjs';
import { ActivatedRoute, Router } from '@angular/router';
import { ToastService } from '../../../../toast/toast.service';
import { NavBarService } from '../../../../navbar/service/nav-bar.service';
import { ToolService } from '../../../../services/tools/tool.service';

type State = 'existing' | 'editing';

@Component({
  selector: 'app-create-t4c-instance',
  templateUrl: './create-t4c-instance.component.html',
  styleUrls: ['./create-t4c-instance.component.css'],
})
export class CreateT4cInstanceComponent implements OnInit {
  existing?: State;
  _instance = new BehaviorSubject<T4CInstance | undefined>(undefined);
  get instance() {
    return this._instance.value;
  }

  public form = new FormGroup({
    name: new FormControl('', Validators.required),
    version_id: new FormControl(-1, Validators.required),
    license: new FormControl('', Validators.required),
    host: new FormControl('', Validators.required),
    port: new FormControl(null as number | null, [
      Validators.required,
      Validators.pattern(/[\d^0]\d*/),
      Validators.min(0),
      Validators.max(65535),
    ]),
    usage_api: new FormControl('', [
      Validators.required,
      Validators.pattern(/^https?:\/\//),
    ]),
    rest_api: new FormControl('', [
      Validators.required,
      Validators.pattern(/^https?:\/\//),
    ]),
    username: new FormControl('', Validators.required),
    password: new FormControl('', Validators.required),
  });

  constructor(
    private navBarService: NavBarService,
    private t4CInstanceService: T4CInstanceService,
    private route: ActivatedRoute,
    private router: Router,
    private toastService: ToastService,
    private toolService: ToolService
  ) {}

  ngOnInit(): void {
    this.navBarService.title = '/ Settings / Modelsources / T4C / Create';

    this.route.params
      .pipe(
        map((params) => params.instance),
        filter((instance) => instance !== undefined),
        tap(() => {
          this.existing = 'existing';
          this.form.disable();
        }),
        switchMap((instance) => this.t4CInstanceService.getInstance(instance))
      )
      .subscribe((instance) => {
        this._instance.next(instance);
      });

    this._instance
      .pipe(tap(console.log), filter(Boolean))
      .subscribe((instance) => {
        this.navBarService.title = `Settings / Modelsources / T4C / ${instance.name}`;
        this.existing = 'existing';
        this.form.patchValue(instance);
      });
  }

  enableEditing(): void {
    this.existing = 'editing';
    this.form.enable();
    this.form.controls.name.disable();
    this.form.controls.version_id.disable();
  }

  cancelEditing(): void {
    this.existing = 'existing';
    this.form.disable();
    this.form.patchValue(this.instance as NewT4CInstance);
  }

  create(): void {
    if (this.form.valid) {
      this.t4CInstanceService
        .createInstance(this.form.value as NewT4CInstance)
        .subscribe((instance) => {
          this.toastService.showSuccess(
            'Instance created',
            `The instance “${instance.name}” was created.`
          );
          this.router.navigate(['..'], { relativeTo: this.route });
        });
    }
  }

  update(): void {
    if (this.form.valid) {
      this.t4CInstanceService
        .updateInstance(this.instance!.id, this.form.value as BaseT4CInstance)
        .subscribe((instance) => {
          this.existing = 'existing';
          this.form.disable();
          this.toastService.showSuccess(
            'Instance updated',
            `The instance “${instance.name}” was updated.`
          );
        });
    }
  }

  submit(): void {
    if (!this.existing) {
      this.create();
    }
    if (this.existing == 'editing') {
      this.update();
    }
  }
}
