# StripeSaaSBillingApi

All URIs are relative to *http://localhost*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**addCreditsMockApiV1BillingAddCreditsPost**](StripeSaaSBillingApi.md#addcreditsmockapiv1billingaddcreditspost) | **POST** /api/v1/billing/add-credits | Mock credit purchase for frontend test modal (for dev/testing) |
| [**createCheckoutSessionApiV1BillingCreateCheckoutSessionPost**](StripeSaaSBillingApi.md#createcheckoutsessionapiv1billingcreatecheckoutsessionpost) | **POST** /api/v1/billing/create-checkout-session | Create a Stripe Checkout session for video generation credits |
| [**getBalanceApiV1BillingBalanceGet**](StripeSaaSBillingApi.md#getbalanceapiv1billingbalanceget) | **GET** /api/v1/billing/balance | Retrieve authenticated user\&#39;s current credit balance |
| [**getBillingHistoryApiV1BillingHistoryGet**](StripeSaaSBillingApi.md#getbillinghistoryapiv1billinghistoryget) | **GET** /api/v1/billing/history | Audit trail of video generation jobs and credit deductions |
| [**stripeWebhookApiV1BillingWebhookPost**](StripeSaaSBillingApi.md#stripewebhookapiv1billingwebhookpost) | **POST** /api/v1/billing/webhook | Stripe Webhook Listener for asynchronous payment fulfillment |



## addCreditsMockApiV1BillingAddCreditsPost

> any addCreditsMockApiV1BillingAddCreditsPost(requestBody)

Mock credit purchase for frontend test modal (for dev/testing)

Direct mock credit addition for frontend test modal.

### Example

```ts
import {
  Configuration,
  StripeSaaSBillingApi,
} from '';
import type { AddCreditsMockApiV1BillingAddCreditsPostRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({ 
    // Configure HTTP bearer authorization: HTTPBearer
    accessToken: "YOUR BEARER TOKEN",
  });
  const api = new StripeSaaSBillingApi(config);

  const body = {
    // { [key: string]: any | null; }
    requestBody: Object,
  } satisfies AddCreditsMockApiV1BillingAddCreditsPostRequest;

  try {
    const data = await api.addCreditsMockApiV1BillingAddCreditsPost(body);
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
| **requestBody** | `{ [key: string]: any | null; }` |  | |

### Return type

**any**

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  -  |
| **422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## createCheckoutSessionApiV1BillingCreateCheckoutSessionPost

> CheckoutSessionResponse createCheckoutSessionApiV1BillingCreateCheckoutSessionPost(createCheckoutSessionRequest)

Create a Stripe Checkout session for video generation credits

Initiates an official Stripe hosted checkout session using standard Stripe SDK patterns.  Parameters ---------- payload : CreateCheckoutSessionRequest     Selected credit package. current_user : AuthenticatedUser     Verified user from JWT middleware.

### Example

```ts
import {
  Configuration,
  StripeSaaSBillingApi,
} from '';
import type { CreateCheckoutSessionApiV1BillingCreateCheckoutSessionPostRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({ 
    // Configure HTTP bearer authorization: HTTPBearer
    accessToken: "YOUR BEARER TOKEN",
  });
  const api = new StripeSaaSBillingApi(config);

  const body = {
    // CreateCheckoutSessionRequest
    createCheckoutSessionRequest: ...,
  } satisfies CreateCheckoutSessionApiV1BillingCreateCheckoutSessionPostRequest;

  try {
    const data = await api.createCheckoutSessionApiV1BillingCreateCheckoutSessionPost(body);
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
| **createCheckoutSessionRequest** | [CreateCheckoutSessionRequest](CreateCheckoutSessionRequest.md) |  | |

### Return type

[**CheckoutSessionResponse**](CheckoutSessionResponse.md)

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  -  |
| **422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## getBalanceApiV1BillingBalanceGet

> UserBalanceResponse getBalanceApiV1BillingBalanceGet()

Retrieve authenticated user\&#39;s current credit balance

Returns the persistent credit balance from PostgreSQL for the authenticated user.

### Example

```ts
import {
  Configuration,
  StripeSaaSBillingApi,
} from '';
import type { GetBalanceApiV1BillingBalanceGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({ 
    // Configure HTTP bearer authorization: HTTPBearer
    accessToken: "YOUR BEARER TOKEN",
  });
  const api = new StripeSaaSBillingApi(config);

  try {
    const data = await api.getBalanceApiV1BillingBalanceGet();
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

[**UserBalanceResponse**](UserBalanceResponse.md)

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## getBillingHistoryApiV1BillingHistoryGet

> Array&lt;BillingHistoryItem&gt; getBillingHistoryApiV1BillingHistoryGet()

Audit trail of video generation jobs and credit deductions

Returns past video generation deductions and timestamps.

### Example

```ts
import {
  Configuration,
  StripeSaaSBillingApi,
} from '';
import type { GetBillingHistoryApiV1BillingHistoryGetRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const config = new Configuration({ 
    // Configure HTTP bearer authorization: HTTPBearer
    accessToken: "YOUR BEARER TOKEN",
  });
  const api = new StripeSaaSBillingApi(config);

  try {
    const data = await api.getBillingHistoryApiV1BillingHistoryGet();
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

[**Array&lt;BillingHistoryItem&gt;**](BillingHistoryItem.md)

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## stripeWebhookApiV1BillingWebhookPost

> any stripeWebhookApiV1BillingWebhookPost(stripeSignature)

Stripe Webhook Listener for asynchronous payment fulfillment

Receives and verifies Stripe webhook events, automatically provisioning credits in PostgreSQL.

### Example

```ts
import {
  Configuration,
  StripeSaaSBillingApi,
} from '';
import type { StripeWebhookApiV1BillingWebhookPostRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new StripeSaaSBillingApi();

  const body = {
    // string (optional)
    stripeSignature: stripeSignature_example,
  } satisfies StripeWebhookApiV1BillingWebhookPostRequest;

  try {
    const data = await api.stripeWebhookApiV1BillingWebhookPost(body);
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
| **stripeSignature** | `string` |  | [Optional] [Defaults to `undefined`] |

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

