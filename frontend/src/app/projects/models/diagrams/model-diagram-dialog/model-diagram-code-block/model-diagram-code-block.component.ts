/*
 * SPDX-FileCopyrightText: Copyright DB Netz AG and the capella-collab-manager contributors
 * SPDX-License-Identifier: Apache-2.0
 */

import {
  AfterViewInit,
  Component,
  Input,
  Pipe,
  PipeTransform,
} from '@angular/core';
import hljs from 'highlight.js';
import {
  BackendMetadata,
  MetadataService,
} from 'src/app/general/metadata/metadata.service';
import { ToastService } from 'src/app/helpers/toast/toast.service';
import {
  Model,
  getPrimaryGitModel,
} from 'src/app/projects/models/service/model.service';
import { Project } from 'src/app/projects/service/project.service';
import { UserService } from 'src/app/services/user/user.service';
import { TokenService } from 'src/app/users/basic-auth-service/basic-auth-token.service';

@Component({
  selector: 'app-model-diagram-code-block',
  styles: [
    '::ng-deep .mat-expansion-indicator::after { border-color: black; }',
  ],
  templateUrl: './model-diagram-code-block.component.html',
})
export class ModelDiagramCodeBlockComponent implements AfterViewInit {
  passwordValue?: string;

  metadata?: BackendMetadata;

  constructor(
    private metadataService: MetadataService,
    private userService: UserService,
    private tokenService: TokenService,
    private toastService: ToastService,
  ) {
    this.metadataService.backendMetadata.subscribe((metadata) => {
      this.metadata = metadata;
    });
  }

  @Input({ required: true })
  model!: Model;

  @Input({ required: true })
  project!: Project;

  ngAfterViewInit(): void {
    hljs.highlightAll();
  }

  get codeBlockContent(): string {
    const basePath = `${this.metadata?.protocol}://${this.metadata?.host}:${this.metadata?.port}`;
    let capellaMBSEFlags =
      '"path": "<Path to the .aird file on your host system>",';

    const primaryGitModel = getPrimaryGitModel(this.model);
    if (primaryGitModel) {
      capellaMBSEFlags = `path="git+${primaryGitModel.path}",
  entrypoint="${primaryGitModel.entrypoint}",
  revision="${primaryGitModel.revision}",`;
    }

    if (primaryGitModel?.password) {
      capellaMBSEFlags += `
  username=input("Please enter the username to access the Git repository."),
  password=getpass.getpass("Please enter the password or personal access token to access the Git repository."),`;
    }

    return `import capellambse
import getpass

model = capellambse.MelodyModel(
  ${capellaMBSEFlags}
  diagram_cache={
    "path": "${basePath}/api/v1/projects/${this.project!.slug}/models/${
      this.model.slug
    }/diagrams/%s",
    "username": "${this.userService.user?.name}",
    "password": "${this.passwordValue ? this.passwordValue : '**************'}",
  }
)`;
  }

  async insertToken() {
    const expirationDate = new Date();
    expirationDate.setDate(expirationDate.getDate() + 30);
    this.tokenService
      .createToken(
        'Created in diagram cache dialog',
        expirationDate,
        'Diagram-cache',
      )
      .subscribe((token) => {
        this.passwordValue = token.password;
      });
  }

  showClipboardMessage(): void {
    this.toastService.showSuccess(
      'Code snippet copied to clipboard',
      this.passwordValue
        ? "The code snipped contains a personal access token for the Collaboration Manager. Be careful with it and don't share it with others!"
        : "The code snipped doesn't contain a personal access token. You can insert one with 'Insert token'.",
    );
  }
}

@Pipe({
  name: 'hightlight',
})
export class HighlightPipeTransform implements PipeTransform {
  transform(value: string, language: string): string {
    return hljs.highlight(language, value).value;
  }
}
