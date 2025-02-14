/*
 * SPDX-FileCopyrightText: Copyright DB Netz AG and the capella-collab-manager contributors
 * SPDX-License-Identifier: Apache-2.0
 */

import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import {
  AbstractControl,
  AsyncValidatorFn,
  ValidationErrors,
} from '@angular/forms';
import { BehaviorSubject, forkJoin, map, Observable, take, tap } from 'rxjs';
import slugify from 'slugify';
import { ModelRestrictions } from 'src/app/projects/models/model-restrictions/service/model-restrictions.service';
import { T4CModel } from 'src/app/projects/models/model-source/t4c/service/t4c-model.service';
import { GetGitModel } from 'src/app/projects/project-detail/model-overview/model-detail/git-model.service';
import {
  Tool,
  ToolNature,
  ToolVersion,
} from 'src/app/settings/core/tools-settings/tool.service';
import { environment } from 'src/environments/environment';

@Injectable({
  providedIn: 'root',
})
export class ModelService {
  base_url = environment.backend_url + '/projects/';

  constructor(private http: HttpClient) {}

  private _model = new BehaviorSubject<Model | undefined>(undefined);
  private _models = new BehaviorSubject<Model[] | undefined>(undefined);

  public readonly model$ = this._model.asObservable();
  public readonly models$ = this._models.asObservable();

  backendURLFactory(projectSlug: string, modelSlug: string) {
    return `${this.base_url}${projectSlug}/models/${modelSlug}`;
  }

  loadModels(projectSlug: string): void {
    this.http.get<Model[]>(`${this.base_url}${projectSlug}/models`).subscribe({
      next: (models) => this._models.next(models),
      error: () => this._models.next(undefined),
    });
  }

  loadModelbySlug(modelSlug: string, projectSlug: string): void {
    this.http
      .get<Model>(`${this.base_url}${projectSlug}/models/${modelSlug}/`)
      .subscribe({
        next: (model) => this._model.next(model),
        error: () => this._model.next(undefined),
      });
  }

  createModel(projectSlug: string, model: NewModel): Observable<Model> {
    return this.http
      .post<Model>(`${this.base_url}${projectSlug}/models`, model)
      .pipe(
        tap({
          next: (model) => {
            this.loadModels(projectSlug);
            this._model.next(model);
          },
          error: () => this._model.next(undefined),
        }),
      );
  }

  setToolDetailsForModel(
    projectSlug: string,
    modelSlug: string,
    version_id: number,
    nature_id: number,
  ): Observable<Model> {
    return this.http
      .patch<Model>(`${this.base_url}${projectSlug}/models/${modelSlug}/`, {
        version_id,
        nature_id,
      })
      .pipe(
        tap({
          next: (model) => {
            this.loadModels(projectSlug);
            this._model.next(model);
          },
          error: () => this._model.next(undefined),
        }),
      );
  }

  private applyModelPatch(
    projectSlug: string,
    modelSlug: string,
    patchData: PatchModel,
  ): Observable<Model> {
    return this.http.patch<Model>(
      `${this.base_url}${projectSlug}/models/${modelSlug}/`,
      patchData,
    );
  }

  updateModel(
    projectSlug: string,
    modelSlug: string,
    patchModel: PatchModel,
  ): Observable<Model> {
    return this.applyModelPatch(projectSlug, modelSlug, patchModel).pipe(
      tap({
        next: (model) => {
          this.loadModels(projectSlug);
          this._model.next(model);
        },
      }),
    );
  }

  updateModels(
    projectSlug: string,
    modelUpdates: { modelSlug: string; patchModel: PatchModel }[],
  ): Observable<Model[]> {
    const updateObservables = modelUpdates.map(({ modelSlug, patchModel }) =>
      this.applyModelPatch(projectSlug, modelSlug, patchModel),
    );

    return forkJoin(updateObservables).pipe(
      tap({
        next: (models: Model[]) => {
          this.loadModels(projectSlug);
          this._model.next(models[models.length - 1]);
        },
      }),
    );
  }

  deleteModel(projectSlug: string, modelSlug: string): Observable<void> {
    return this.http
      .delete<void>(`${this.base_url}${projectSlug}/models/${modelSlug}`)
      .pipe(
        tap(() => {
          this.loadModels(projectSlug);
          this._model.next(undefined);
        }),
      );
  }

  clearModel(): void {
    this._model.next(undefined);
  }

  clearModels(): void {
    this._models.next(undefined);
  }

  asyncSlugValidator(ignoreModel?: Model): AsyncValidatorFn {
    const ignoreSlug = !!ignoreModel ? ignoreModel.slug : -1;
    return (control: AbstractControl): Observable<ValidationErrors | null> => {
      const modelSlug = slugify(control.value, { lower: true });
      return this.models$.pipe(
        take(1),
        map((models) => {
          return models?.find(
            (model) => model.slug === modelSlug && model.slug !== ignoreSlug,
          )
            ? { uniqueSlug: { value: modelSlug } }
            : null;
        }),
      );
    };
  }

  moveModelToProject(
    projectSlug: string,
    modelSlug: string,
    project_slug: string,
  ): Observable<Model> {
    return this.http
      .patch<Model>(`${this.backendURLFactory(projectSlug, modelSlug)}/move`, {
        project_slug,
      })
      .pipe(
        tap(() => {
          this.loadModels(projectSlug);
          this._model.next(undefined);
        }),
      );
  }
}

export type NewModel = {
  name: string;
  description: string;
  tool_id: number;
};

export type Model = {
  id: number;
  project_slug: string;
  slug: string;
  name: string;
  description: string;
  tool: Tool;
  version?: ToolVersion;
  nature?: ToolNature;
  t4c_models: T4CModel[];
  git_models: GetGitModel[];
  restrictions: ModelRestrictions;
  display_order: number;
};

export type PatchModel = {
  name?: string;
  description?: string;
  nature_id?: number;
  version_id?: number;
  project_slug?: string;
  display_order?: number;
};

export function getPrimaryGitModel(model: Model): GetGitModel | undefined {
  return model.git_models.find((gitModel) => gitModel.primary);
}
