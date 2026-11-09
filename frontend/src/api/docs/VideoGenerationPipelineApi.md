# VideoGenerationPipelineApi

All URIs are relative to *http://localhost*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**downloadVideoApiV1JobsJobIdDownloadGet**](VideoGenerationPipelineApi.md#downloadvideoapiv1jobsjobiddownloadget) | **GET** /api/v1/jobs/{job_id}/download | Download the final rendered MP4 tutorial video |
| [**generateVideoApiV1GenerateVideoPost**](VideoGenerationPipelineApi.md#generatevideoapiv1generatevideopost) | **POST** /api/v1/generate-video | Trigger asynchronous codebase tutorial video generation |
| [**getJobStatusApiV1JobsJobIdGet**](VideoGenerationPipelineApi.md#getjobstatusapiv1jobsjobidget) | **GET** /api/v1/jobs/{job_id} | Query background task status and progress |
| [**streamJobProgressApiV1JobsJobIdStreamGet**](VideoGenerationPipelineApi.md#streamjobprogressapiv1jobsjobidstreamget) | **GET** /api/v1/jobs/{job_id}/stream | Stream live video generation progress via Server-Sent Events (SSE) |



## downloadVideoApiV1JobsJobIdDownloadGet

> any downloadVideoApiV1JobsJobIdDownloadGet(jobId)

Download the final rendered MP4 tutorial video

Stream or download the final synthesized HD tutorial video.

### Example

```ts
import {
  Configuration,
  VideoGenerationPipelineApi,
} from '';
import type { DownloadVideoApiV1JobsJobIdDownloadGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new VideoGenerationPipelineApi();

  const body = {
    // string
    jobId: jobId_example,
  } satisfies DownloadVideoApiV1JobsJobIdDownloadGetRequest;

  try {
    const data = await api.downloadVideoApiV1JobsJobIdDownloadGet(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **jobId** | `string` |  | [Defaults to `undefined`] |

### Return type

**any**

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  -  |
| **422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## generateVideoApiV1GenerateVideoPost

> GenerateVideoResponse generateVideoApiV1GenerateVideoPost(generateVideoRequest)

Trigger asynchronous codebase tutorial video generation

Triggers the 5-stage background video generation pipeline:  1. Ingestion / Repomix codebase packaging 2. Gemini AI architecture topology &amp; script generation 3. Manim Community animation rendering 4. Neural voiceover TTS &amp; .srt subtitle synthesis 5. FFmpeg final resolution scaling, duration sync, &amp; subtitle burn-in

### Example

```ts
import {
  Configuration,
  VideoGenerationPipelineApi,
} from '';
import type { GenerateVideoApiV1GenerateVideoPostRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new VideoGenerationPipelineApi();

  const body = {
    // GenerateVideoRequest
    generateVideoRequest: ...,
  } satisfies GenerateVideoApiV1GenerateVideoPostRequest;

  try {
    const data = await api.generateVideoApiV1GenerateVideoPost(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **generateVideoRequest** | [GenerateVideoRequest](GenerateVideoRequest.md) |  | |

### Return type

[**GenerateVideoResponse**](GenerateVideoResponse.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **202** | Successful Response |  -  |
| **422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## getJobStatusApiV1JobsJobIdGet

> JobStatusResponse getJobStatusApiV1JobsJobIdGet(jobId)

Query background task status and progress

Poll the status and progress of a video generation task with short-lived caching.

### Example

```ts
import {
  Configuration,
  VideoGenerationPipelineApi,
} from '';
import type { GetJobStatusApiV1JobsJobIdGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new VideoGenerationPipelineApi();

  const body = {
    // string
    jobId: jobId_example,
  } satisfies GetJobStatusApiV1JobsJobIdGetRequest;

  try {
    const data = await api.getJobStatusApiV1JobsJobIdGet(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **jobId** | `string` |  | [Defaults to `undefined`] |

### Return type

[**JobStatusResponse**](JobStatusResponse.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  -  |
| **422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## streamJobProgressApiV1JobsJobIdStreamGet

> any streamJobProgressApiV1JobsJobIdStreamGet(jobId)

Stream live video generation progress via Server-Sent Events (SSE)

Stream live progress updates (0% to 100% and stage changes) directly via Server-Sent Events.

### Example

```ts
import {
  Configuration,
  VideoGenerationPipelineApi,
} from '';
import type { StreamJobProgressApiV1JobsJobIdStreamGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new VideoGenerationPipelineApi();

  const body = {
    // string
    jobId: jobId_example,
  } satisfies StreamJobProgressApiV1JobsJobIdStreamGetRequest;

  try {
    const data = await api.streamJobProgressApiV1JobsJobIdStreamGet(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **jobId** | `string` |  | [Defaults to `undefined`] |

### Return type

**any**

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  -  |
| **422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

