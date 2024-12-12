/*
 * SPDX-FileCopyrightText: Copyright DB InfraGO AG and contributors
 * SPDX-License-Identifier: Apache-2.0
 *
 * Capella Collaboration Manager API
 *
 * NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).
 * Do not edit the class manually.
 + To generate a new version, run `make openapi` in the root directory of this repository.
 */

/* tslint:disable:no-unused-variable member-ordering */

import { Inject, Injectable, Optional }                      from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams,
         HttpResponse, HttpEvent, HttpParameterCodec, HttpContext 
        }       from '@angular/common/http';
import { CustomHttpParameterCodec }                          from '../encoder';
import { Observable }                                        from 'rxjs';

// @ts-ignore
import { DiagramCacheMetadata } from '../model/diagram-cache-metadata';
// @ts-ignore
import { HTTPValidationError } from '../model/http-validation-error';

// @ts-ignore
import { BASE_PATH, COLLECTION_FORMATS }                     from '../variables';
import { Configuration }                                     from '../configuration';



@Injectable({
  providedIn: 'root'
})
export class ProjectsModelsDiagramsService {

    protected basePath = 'http://localhost';
    public defaultHeaders = new HttpHeaders();
    public configuration = new Configuration();
    public encoder: HttpParameterCodec;

    constructor(protected httpClient: HttpClient, @Optional()@Inject(BASE_PATH) basePath: string|string[], @Optional() configuration: Configuration) {
        if (configuration) {
            this.configuration = configuration;
        }
        if (typeof this.configuration.basePath !== 'string') {
            const firstBasePath = Array.isArray(basePath) ? basePath[0] : undefined;
            if (firstBasePath != undefined) {
                basePath = firstBasePath;
            }

            if (typeof basePath !== 'string') {
                basePath = this.basePath;
            }
            this.configuration.basePath = basePath;
        }
        this.encoder = this.configuration.encoder || new CustomHttpParameterCodec();
    }


    // @ts-ignore
    private addToHttpParams(httpParams: HttpParams, value: any, key?: string): HttpParams {
        if (typeof value === "object" && value instanceof Date === false) {
            httpParams = this.addToHttpParamsRecursive(httpParams, value);
        } else {
            httpParams = this.addToHttpParamsRecursive(httpParams, value, key);
        }
        return httpParams;
    }

    private addToHttpParamsRecursive(httpParams: HttpParams, value?: any, key?: string): HttpParams {
        if (value == null) {
            return httpParams;
        }

        if (typeof value === "object") {
            if (Array.isArray(value)) {
                (value as any[]).forEach( elem => httpParams = this.addToHttpParamsRecursive(httpParams, elem, key));
            } else if (value instanceof Date) {
                if (key != null) {
                    httpParams = httpParams.append(key, (value as Date).toISOString().substring(0, 10));
                } else {
                   throw Error("key may not be null if value is Date");
                }
            } else {
                Object.keys(value).forEach( k => httpParams = this.addToHttpParamsRecursive(
                    httpParams, value[k], key != null ? `${key}.${k}` : k));
            }
        } else if (key != null) {
            httpParams = httpParams.append(key, value);
        } else {
            throw Error("key may not be null if value is not object or array");
        }
        return httpParams;
    }

    /**
     * Get Diagram
     * This route requires the following permissions in the corresponding project: &#x60;diagram_cache:get&#x60;
     * @param diagramUuidOrFilename 
     * @param projectSlug 
     * @param modelSlug 
     * @param jobId 
     * @param observe set whether or not to return the data Observable as the body, response or events. defaults to returning the body.
     * @param reportProgress flag to report request and response progress.
     */
    public getDiagram(diagramUuidOrFilename: string, projectSlug: string, modelSlug: string, jobId?: string, observe?: 'body', reportProgress?: boolean, options?: {httpHeaderAccept?: 'image/svg+xml' | 'application/json', context?: HttpContext, transferCache?: boolean}): Observable<Blob>;
    public getDiagram(diagramUuidOrFilename: string, projectSlug: string, modelSlug: string, jobId?: string, observe?: 'response', reportProgress?: boolean, options?: {httpHeaderAccept?: 'image/svg+xml' | 'application/json', context?: HttpContext, transferCache?: boolean}): Observable<HttpResponse<Blob>>;
    public getDiagram(diagramUuidOrFilename: string, projectSlug: string, modelSlug: string, jobId?: string, observe?: 'events', reportProgress?: boolean, options?: {httpHeaderAccept?: 'image/svg+xml' | 'application/json', context?: HttpContext, transferCache?: boolean}): Observable<HttpEvent<Blob>>;
    public getDiagram(diagramUuidOrFilename: string, projectSlug: string, modelSlug: string, jobId?: string, observe: any = 'body', reportProgress: boolean = false, options?: {httpHeaderAccept?: 'image/svg+xml' | 'application/json', context?: HttpContext, transferCache?: boolean}): Observable<any> {
        if (diagramUuidOrFilename === null || diagramUuidOrFilename === undefined) {
            throw new Error('Required parameter diagramUuidOrFilename was null or undefined when calling getDiagram.');
        }
        if (projectSlug === null || projectSlug === undefined) {
            throw new Error('Required parameter projectSlug was null or undefined when calling getDiagram.');
        }
        if (modelSlug === null || modelSlug === undefined) {
            throw new Error('Required parameter modelSlug was null or undefined when calling getDiagram.');
        }

        let localVarQueryParameters = new HttpParams({encoder: this.encoder});
        if (jobId !== undefined && jobId !== null) {
          localVarQueryParameters = this.addToHttpParams(localVarQueryParameters,
            <any>jobId, 'job_id');
        }

        let localVarHeaders = this.defaultHeaders;

        let localVarCredential: string | undefined;
        // authentication (Cookie) required
        localVarCredential = this.configuration.lookupCredential('Cookie');
        if (localVarCredential) {
        }

        // authentication (PersonalAccessToken) required
        localVarCredential = this.configuration.lookupCredential('PersonalAccessToken');
        if (localVarCredential) {
            localVarHeaders = localVarHeaders.set('Authorization', 'Basic ' + localVarCredential);
        }

        let localVarHttpHeaderAcceptSelected: string | undefined = options && options.httpHeaderAccept;
        if (localVarHttpHeaderAcceptSelected === undefined) {
            // to determine the Accept header
            const httpHeaderAccepts: string[] = [
                'image/svg+xml',
                'application/json'
            ];
            localVarHttpHeaderAcceptSelected = this.configuration.selectHeaderAccept(httpHeaderAccepts);
        }
        if (localVarHttpHeaderAcceptSelected !== undefined) {
            localVarHeaders = localVarHeaders.set('Accept', localVarHttpHeaderAcceptSelected);
        }

        let localVarHttpContext: HttpContext | undefined = options && options.context;
        if (localVarHttpContext === undefined) {
            localVarHttpContext = new HttpContext();
        }

        let localVarTransferCache: boolean | undefined = options && options.transferCache;
        if (localVarTransferCache === undefined) {
            localVarTransferCache = true;
        }


        let localVarPath = `/api/v1/projects/${this.configuration.encodeParam({name: "projectSlug", value: projectSlug, in: "path", style: "simple", explode: false, dataType: "string", dataFormat: undefined})}/models/${this.configuration.encodeParam({name: "modelSlug", value: modelSlug, in: "path", style: "simple", explode: false, dataType: "string", dataFormat: undefined})}/diagrams/${this.configuration.encodeParam({name: "diagramUuidOrFilename", value: diagramUuidOrFilename, in: "path", style: "simple", explode: false, dataType: "string", dataFormat: undefined})}`;
        return this.httpClient.request('get', `${this.configuration.basePath}${localVarPath}`,
            {
                context: localVarHttpContext,
                params: localVarQueryParameters,
                responseType: "blob",
                withCredentials: this.configuration.withCredentials,
                headers: localVarHeaders,
                observe: observe,
                transferCache: localVarTransferCache,
                reportProgress: reportProgress
            }
        );
    }

    /**
     * Get Diagram Metadata
     * This route requires the following permissions in the corresponding project: &#x60;diagram_cache:get&#x60;
     * @param projectSlug 
     * @param modelSlug 
     * @param observe set whether or not to return the data Observable as the body, response or events. defaults to returning the body.
     * @param reportProgress flag to report request and response progress.
     */
    public getDiagramMetadata(projectSlug: string, modelSlug: string, observe?: 'body', reportProgress?: boolean, options?: {httpHeaderAccept?: 'application/json', context?: HttpContext, transferCache?: boolean}): Observable<DiagramCacheMetadata>;
    public getDiagramMetadata(projectSlug: string, modelSlug: string, observe?: 'response', reportProgress?: boolean, options?: {httpHeaderAccept?: 'application/json', context?: HttpContext, transferCache?: boolean}): Observable<HttpResponse<DiagramCacheMetadata>>;
    public getDiagramMetadata(projectSlug: string, modelSlug: string, observe?: 'events', reportProgress?: boolean, options?: {httpHeaderAccept?: 'application/json', context?: HttpContext, transferCache?: boolean}): Observable<HttpEvent<DiagramCacheMetadata>>;
    public getDiagramMetadata(projectSlug: string, modelSlug: string, observe: any = 'body', reportProgress: boolean = false, options?: {httpHeaderAccept?: 'application/json', context?: HttpContext, transferCache?: boolean}): Observable<any> {
        if (projectSlug === null || projectSlug === undefined) {
            throw new Error('Required parameter projectSlug was null or undefined when calling getDiagramMetadata.');
        }
        if (modelSlug === null || modelSlug === undefined) {
            throw new Error('Required parameter modelSlug was null or undefined when calling getDiagramMetadata.');
        }

        let localVarHeaders = this.defaultHeaders;

        let localVarCredential: string | undefined;
        // authentication (Cookie) required
        localVarCredential = this.configuration.lookupCredential('Cookie');
        if (localVarCredential) {
        }

        // authentication (PersonalAccessToken) required
        localVarCredential = this.configuration.lookupCredential('PersonalAccessToken');
        if (localVarCredential) {
            localVarHeaders = localVarHeaders.set('Authorization', 'Basic ' + localVarCredential);
        }

        let localVarHttpHeaderAcceptSelected: string | undefined = options && options.httpHeaderAccept;
        if (localVarHttpHeaderAcceptSelected === undefined) {
            // to determine the Accept header
            const httpHeaderAccepts: string[] = [
                'application/json'
            ];
            localVarHttpHeaderAcceptSelected = this.configuration.selectHeaderAccept(httpHeaderAccepts);
        }
        if (localVarHttpHeaderAcceptSelected !== undefined) {
            localVarHeaders = localVarHeaders.set('Accept', localVarHttpHeaderAcceptSelected);
        }

        let localVarHttpContext: HttpContext | undefined = options && options.context;
        if (localVarHttpContext === undefined) {
            localVarHttpContext = new HttpContext();
        }

        let localVarTransferCache: boolean | undefined = options && options.transferCache;
        if (localVarTransferCache === undefined) {
            localVarTransferCache = true;
        }


        let responseType_: 'text' | 'json' | 'blob' = 'json';
        if (localVarHttpHeaderAcceptSelected) {
            if (localVarHttpHeaderAcceptSelected.startsWith('text')) {
                responseType_ = 'text';
            } else if (this.configuration.isJsonMime(localVarHttpHeaderAcceptSelected)) {
                responseType_ = 'json';
            } else {
                responseType_ = 'blob';
            }
        }

        let localVarPath = `/api/v1/projects/${this.configuration.encodeParam({name: "projectSlug", value: projectSlug, in: "path", style: "simple", explode: false, dataType: "string", dataFormat: undefined})}/models/${this.configuration.encodeParam({name: "modelSlug", value: modelSlug, in: "path", style: "simple", explode: false, dataType: "string", dataFormat: undefined})}/diagrams`;
        return this.httpClient.request<DiagramCacheMetadata>('get', `${this.configuration.basePath}${localVarPath}`,
            {
                context: localVarHttpContext,
                responseType: <any>responseType_,
                withCredentials: this.configuration.withCredentials,
                headers: localVarHeaders,
                observe: observe,
                transferCache: localVarTransferCache,
                reportProgress: reportProgress
            }
        );
    }

}
