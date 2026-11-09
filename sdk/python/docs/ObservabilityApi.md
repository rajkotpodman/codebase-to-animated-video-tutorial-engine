# codevideo_client.ObservabilityApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**metrics_metrics_get**](ObservabilityApi.md#metrics_metrics_get) | **GET** /metrics | Metrics


# **metrics_metrics_get**
> object metrics_metrics_get()

Metrics

Endpoint that serves Prometheus metrics.

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
    api_instance = codevideo_client.ObservabilityApi(api_client)

    try:
        # Metrics
        api_response = api_instance.metrics_metrics_get()
        print("The response of ObservabilityApi->metrics_metrics_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling ObservabilityApi->metrics_metrics_get: %s\n" % e)
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

