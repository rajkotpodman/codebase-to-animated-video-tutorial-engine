# codevideo_client.VideoGenerationPipelineApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**download_video_api_v1_jobs_job_id_download_get**](VideoGenerationPipelineApi.md#download_video_api_v1_jobs_job_id_download_get) | **GET** /api/v1/jobs/{job_id}/download | Download the final rendered MP4 tutorial video
[**generate_video_api_v1_generate_video_post**](VideoGenerationPipelineApi.md#generate_video_api_v1_generate_video_post) | **POST** /api/v1/generate-video | Trigger asynchronous codebase tutorial video generation
[**get_job_status_api_v1_jobs_job_id_get**](VideoGenerationPipelineApi.md#get_job_status_api_v1_jobs_job_id_get) | **GET** /api/v1/jobs/{job_id} | Query background task status and progress
[**stream_job_progress_api_v1_jobs_job_id_stream_get**](VideoGenerationPipelineApi.md#stream_job_progress_api_v1_jobs_job_id_stream_get) | **GET** /api/v1/jobs/{job_id}/stream | Stream live video generation progress via Server-Sent Events (SSE)


# **download_video_api_v1_jobs_job_id_download_get**
> object download_video_api_v1_jobs_job_id_download_get(job_id)

Download the final rendered MP4 tutorial video

Stream or download the final synthesized HD tutorial video.

### Example


```python
import codevideo_client
from codevideo_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = codevideo_client.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with codevideo_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = codevideo_client.VideoGenerationPipelineApi(api_client)
    job_id = 'job_id_example' # str | 

    try:
        # Download the final rendered MP4 tutorial video
        api_response = api_instance.download_video_api_v1_jobs_job_id_download_get(job_id)
        print("The response of VideoGenerationPipelineApi->download_video_api_v1_jobs_job_id_download_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling VideoGenerationPipelineApi->download_video_api_v1_jobs_job_id_download_get: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **job_id** | **str**|  | 

### Return type

**object**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **generate_video_api_v1_generate_video_post**
> GenerateVideoResponse generate_video_api_v1_generate_video_post(generate_video_request)

Trigger asynchronous codebase tutorial video generation

Triggers the 5-stage background video generation pipeline:

1. Ingestion / Repomix codebase packaging
2. Gemini AI architecture topology & script generation
3. Manim Community animation rendering
4. Neural voiceover TTS & .srt subtitle synthesis
5. FFmpeg final resolution scaling, duration sync, & subtitle burn-in

### Example


```python
import codevideo_client
from codevideo_client.models.generate_video_request import GenerateVideoRequest
from codevideo_client.models.generate_video_response import GenerateVideoResponse
from codevideo_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = codevideo_client.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with codevideo_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = codevideo_client.VideoGenerationPipelineApi(api_client)
    generate_video_request = codevideo_client.GenerateVideoRequest() # GenerateVideoRequest | 

    try:
        # Trigger asynchronous codebase tutorial video generation
        api_response = api_instance.generate_video_api_v1_generate_video_post(generate_video_request)
        print("The response of VideoGenerationPipelineApi->generate_video_api_v1_generate_video_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling VideoGenerationPipelineApi->generate_video_api_v1_generate_video_post: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **generate_video_request** | [**GenerateVideoRequest**](GenerateVideoRequest.md)|  | 

### Return type

[**GenerateVideoResponse**](GenerateVideoResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**202** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_job_status_api_v1_jobs_job_id_get**
> JobStatusResponse get_job_status_api_v1_jobs_job_id_get(job_id)

Query background task status and progress

Poll the status and progress of a video generation task with short-lived caching.

### Example


```python
import codevideo_client
from codevideo_client.models.job_status_response import JobStatusResponse
from codevideo_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = codevideo_client.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with codevideo_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = codevideo_client.VideoGenerationPipelineApi(api_client)
    job_id = 'job_id_example' # str | 

    try:
        # Query background task status and progress
        api_response = api_instance.get_job_status_api_v1_jobs_job_id_get(job_id)
        print("The response of VideoGenerationPipelineApi->get_job_status_api_v1_jobs_job_id_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling VideoGenerationPipelineApi->get_job_status_api_v1_jobs_job_id_get: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **job_id** | **str**|  | 

### Return type

[**JobStatusResponse**](JobStatusResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **stream_job_progress_api_v1_jobs_job_id_stream_get**
> object stream_job_progress_api_v1_jobs_job_id_stream_get(job_id)

Stream live video generation progress via Server-Sent Events (SSE)

Stream live progress updates (0% to 100% and stage changes) directly via Server-Sent Events.

### Example


```python
import codevideo_client
from codevideo_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = codevideo_client.Configuration(
    host = "http://localhost"
)


# Enter a context with an instance of the API client
with codevideo_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = codevideo_client.VideoGenerationPipelineApi(api_client)
    job_id = 'job_id_example' # str | 

    try:
        # Stream live video generation progress via Server-Sent Events (SSE)
        api_response = api_instance.stream_job_progress_api_v1_jobs_job_id_stream_get(job_id)
        print("The response of VideoGenerationPipelineApi->stream_job_progress_api_v1_jobs_job_id_stream_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling VideoGenerationPipelineApi->stream_job_progress_api_v1_jobs_job_id_stream_get: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **job_id** | **str**|  | 

### Return type

**object**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

