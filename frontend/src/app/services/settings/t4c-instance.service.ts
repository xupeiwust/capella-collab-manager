/*
 * SPDX-FileCopyrightText: Copyright DB Netz AG and the capella-collab-manager contributors
 * SPDX-License-Identifier: Apache-2.0
 */

import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, tap } from 'rxjs';
import { environment } from 'src/environments/environment';

export type Protocol = 'tcp' | 'ssl' | 'ws' | 'wss';

export type BaseT4CInstance = {
  version_id: number;
  license: string;
  host: string;
  port: number;
  cdo_port: number;
  usage_api: string;
  rest_api: string;
  username: string;
  password: string;
  protocol: Protocol;
};

export type NewT4CInstance = BaseT4CInstance & {
  name: string;
};

export type T4CInstance = NewT4CInstance & {
  id: number;
  version: {
    id: number;
    name: string;
  };
};

@Injectable({
  providedIn: 'root',
})
export class T4CInstanceService {
  constructor(private http: HttpClient) {}

  base_url = `${environment.backend_url}/settings/modelsources/t4c`;

  private _t4cInstances = new BehaviorSubject<T4CInstance[] | undefined>(
    undefined
  );
  readonly t4cInstances = this._t4cInstances.asObservable();

  private _t4cInstance = new BehaviorSubject<T4CInstance | undefined>(
    undefined
  );
  readonly t4cInstance = this._t4cInstance.asObservable();

  loadInstances(): void {
    this.http.get<T4CInstance[]>(this.base_url).subscribe({
      next: (instances) => this._t4cInstances.next(instances),
      error: () => this._t4cInstances.next(undefined),
    });
  }

  loadInstance(id: number): void {
    this.http.get<T4CInstance>(this.base_url + '/' + id).subscribe({
      next: (instance) => this._t4cInstance.next(instance),
      error: () => this._t4cInstance.next(undefined),
    });
  }

  createInstance(instance: NewT4CInstance): Observable<T4CInstance> {
    return this.http.post<T4CInstance>(this.base_url, instance).pipe(
      tap((instance) => {
        this._t4cInstance.next(instance);
        this.loadInstances();
      })
    );
  }

  updateInstance(
    id: number,
    instance: BaseT4CInstance
  ): Observable<T4CInstance> {
    return this.http
      .patch<T4CInstance>(this.base_url + '/' + id, instance)
      .pipe(
        tap((instance) => {
          this._t4cInstance.next(instance);
          this.loadInstances();
        })
      );
  }

  reset(): void {
    this._t4cInstance.next(undefined);
    this._t4cInstances.next(undefined);
  }

  getLicenses(t4cInstanceId: number): Observable<SessionUsage> {
    return this.http.get<SessionUsage>(
      `${this.base_url}/${t4cInstanceId}/licenses`
    );
  }
}

export type SessionUsage = {
  free: number;
  total: number;
};
