# codevideo_client.GeneralApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**health_check_health_get**](GeneralApi.md#health_check_health_get) | **GET** /health | Health Check
[**root_get**](GeneralApi.md#root_get) | **GET** / | Root
[**trigger_sentry_error_sentry_debug_get**](GeneralApi.md#trigger_sentry_error_sentry_debug_get) | **GET** /sentry-debug | Trigger test exception for Sentry observability validation


# **health_check_health_get**
> object health_check_health_get()

Health Check

Liveness probe.

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
    api_instance = codevideo_client.GeneralApi(api_client)

    try:
        # Health Check
        api_response = api_instance.health_check_health_get()
        print("The response of GeneralApi->health_check_health_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling GeneralApi->health_check_health_get: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

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

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **root_get**
> object root_get()

Root

Service metadata and health check.

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
    api_instance = codevideo_client.GeneralApi(api_client)

    try:
        # Root
        api_response = api_instance.root_get()
        print("The response of GeneralApi->root_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling GeneralApi->root_get: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

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

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **trigger_sentry_error_sentry_debug_get**
> object trigger_sentry_error_sentry_debug_get()

Trigger test exception for Sentry observability validation

Triggers an intentional ZeroDivisionError to verify Sentry exception capture.

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
    api_instance = codevideo_client.GeneralApi(api_client)

    try:
        # Trigger test exception for Sentry observability validation
        api_response = api_instance.trigger_sentry_error_sentry_debug_get()
        print("The response of GeneralApi->trigger_sentry_error_sentry_debug_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling GeneralApi->trigger_sentry_error_sentry_debug_get: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

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

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

