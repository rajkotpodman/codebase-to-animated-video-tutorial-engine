# ObservabilityApi

All URIs are relative to *http://localhost*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**metricsMetricsGet**](ObservabilityApi.md#metricsmetricsget) | **GET** /metrics | Metrics |



## metricsMetricsGet

> any metricsMetricsGet()

Metrics

Endpoint that serves Prometheus metrics.

### Example

```ts
import {
  Configuration,
  ObservabilityApi,
} from '';
import type { MetricsMetricsGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new ObservabilityApi();

  try {
    const data = await api.metricsMetricsGet();
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

This endpoint does not need any parameter.

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

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

