/*
 * SPDX-FileCopyrightText: Copyright DB Netz AG and the capella-collab-manager contributors
 * SPDX-License-Identifier: Apache-2.0
 */

import { Component, Input } from '@angular/core';
import { ToastService } from 'src/app/helpers/toast/toast.service';

@Component({
  selector: 'app-display-value',
  templateUrl: './display-value.component.html',
  styleUrls: ['./display-value.component.css'],
})
export class DisplayValueComponent {
  constructor(private toastService: ToastService) {}

  @Input()
  value?: string = undefined;

  @Input()
  blurValue = false;

  @Input()
  valueName?: string = undefined;

  showClipboardMessage(): void {
    this.toastService.showSuccess(
      `${
        this.valueName ? this.capitalizeString(this.valueName) : 'Value'
      } copied`,
      `The ${this.valueName || 'value'} was copied to your clipboard.`,
    );
  }

  capitalizeString(value: string) {
    return value.charAt(0).toUpperCase() + value.slice(1);
  }

  valueRevealed = false;
}
