# codevideo_client.StripeSaaSBillingApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**add_credits_mock_api_v1_billing_add_credits_post**](StripeSaaSBillingApi.md#add_credits_mock_api_v1_billing_add_credits_post) | **POST** /api/v1/billing/add-credits | Mock credit purchase for frontend test modal (for dev/testing)
[**create_checkout_session_api_v1_billing_create_checkout_session_post**](StripeSaaSBillingApi.md#create_checkout_session_api_v1_billing_create_checkout_session_post) | **POST** /api/v1/billing/create-checkout-session | Create a Stripe Checkout session for video generation credits
[**get_balance_api_v1_billing_balance_get**](StripeSaaSBillingApi.md#get_balance_api_v1_billing_balance_get) | **GET** /api/v1/billing/balance | Retrieve authenticated user&#39;s current credit balance
[**get_billing_history_api_v1_billing_history_get**](StripeSaaSBillingApi.md#get_billing_history_api_v1_billing_history_get) | **GET** /api/v1/billing/history | Audit trail of video generation jobs and credit deductions
[**stripe_webhook_api_v1_billing_webhook_post**](StripeSaaSBillingApi.md#stripe_webhook_api_v1_billing_webhook_post) | **POST** /api/v1/billing/webhook | Stripe Webhook Listener for asynchronous payment fulfillment


# **add_credits_mock_api_v1_billing_add_credits_post**
> object add_credits_mock_api_v1_billing_add_credits_post(request_body)

Mock credit purchase for frontend test modal (for dev/testing)

Direct mock credit addition for frontend test modal.

### Example

* Bearer Authentication (HTTPBearer):

```python
import codevideo_client
from codevideo_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = codevideo_client.Configuration(
    host = "http://localhost"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization: HTTPBearer
configuration = codevideo_client.Configuration(
    access_token = os.environ["BEARER_TOKEN"]
)

# Enter a context with an instance of the API client
with codevideo_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = codevideo_client.StripeSaaSBillingApi(api_client)
    request_body = None # Dict[str, Optional[object]] | 

    try:
        # Mock credit purchase for frontend test modal (for dev/testing)
        api_response = api_instance.add_credits_mock_api_v1_billing_add_credits_post(request_body)
        print("The response of StripeSaaSBillingApi->add_credits_mock_api_v1_billing_add_credits_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling StripeSaaSBillingApi->add_credits_mock_api_v1_billing_add_credits_post: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **request_body** | [**Dict[str, Optional[object]]**](object.md)|  | 

### Return type

**object**

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_checkout_session_api_v1_billing_create_checkout_session_post**
> CheckoutSessionResponse create_checkout_session_api_v1_billing_create_checkout_session_post(create_checkout_session_request)

Create a Stripe Checkout session for video generation credits

Initiates an official Stripe hosted checkout session using standard Stripe SDK patterns.

Parameters
----------
payload : CreateCheckoutSessionRequest
    Selected credit package.
current_user : AuthenticatedUser
    Verified user from JWT middleware.

### Example

* Bearer Authentication (HTTPBearer):

```python
import codevideo_client
from codevideo_client.models.checkout_session_response import CheckoutSessionResponse
from codevideo_client.models.create_checkout_session_request import CreateCheckoutSessionRequest
from codevideo_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = codevideo_client.Configuration(
    host = "http://localhost"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization: HTTPBearer
configuration = codevideo_client.Configuration(
    access_token = os.environ["BEARER_TOKEN"]
)

# Enter a context with an instance of the API client
with codevideo_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = codevideo_client.StripeSaaSBillingApi(api_client)
    create_checkout_session_request = codevideo_client.CreateCheckoutSessionRequest() # CreateCheckoutSessionRequest | 

    try:
        # Create a Stripe Checkout session for video generation credits
        api_response = api_instance.create_checkout_session_api_v1_billing_create_checkout_session_post(create_checkout_session_request)
        print("The response of StripeSaaSBillingApi->create_checkout_session_api_v1_billing_create_checkout_session_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling StripeSaaSBillingApi->create_checkout_session_api_v1_billing_create_checkout_session_post: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **create_checkout_session_request** | [**CreateCheckoutSessionRequest**](CreateCheckoutSessionRequest.md)|  | 

### Return type

[**CheckoutSessionResponse**](CheckoutSessionResponse.md)

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |
**422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_balance_api_v1_billing_balance_get**
> UserBalanceResponse get_balance_api_v1_billing_balance_get()

Retrieve authenticated user's current credit balance

Returns the persistent credit balance from PostgreSQL for the authenticated user.

### Example

* Bearer Authentication (HTTPBearer):

```python
import codevideo_client
from codevideo_client.models.user_balance_response import UserBalanceResponse
from codevideo_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = codevideo_client.Configuration(
    host = "http://localhost"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization: HTTPBearer
configuration = codevideo_client.Configuration(
    access_token = os.environ["BEARER_TOKEN"]
)

# Enter a context with an instance of the API client
with codevideo_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = codevideo_client.StripeSaaSBillingApi(api_client)

    try:
        # Retrieve authenticated user's current credit balance
        api_response = api_instance.get_balance_api_v1_billing_balance_get()
        print("The response of StripeSaaSBillingApi->get_balance_api_v1_billing_balance_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling StripeSaaSBillingApi->get_balance_api_v1_billing_balance_get: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**UserBalanceResponse**](UserBalanceResponse.md)

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_billing_history_api_v1_billing_history_get**
> List[BillingHistoryItem] get_billing_history_api_v1_billing_history_get()

Audit trail of video generation jobs and credit deductions

Returns past video generation deductions and timestamps.

### Example

* Bearer Authentication (HTTPBearer):

```python
import codevideo_client
from codevideo_client.models.billing_history_item import BillingHistoryItem
from codevideo_client.rest import ApiException
from pprint import pprint

# Defining the host is optional and defaults to http://localhost
# See configuration.py for a list of all supported configuration parameters.
configuration = codevideo_client.Configuration(
    host = "http://localhost"
)

# The client must configure the authentication and authorization parameters
# in accordance with the API server security policy.
# Examples for each auth method are provided below, use the example that
# satisfies your auth use case.

# Configure Bearer authorization: HTTPBearer
configuration = codevideo_client.Configuration(
    access_token = os.environ["BEARER_TOKEN"]
)

# Enter a context with an instance of the API client
with codevideo_client.ApiClient(configuration) as api_client:
    # Create an instance of the API class
    api_instance = codevideo_client.StripeSaaSBillingApi(api_client)

    try:
        # Audit trail of video generation jobs and credit deductions
        api_response = api_instance.get_billing_history_api_v1_billing_history_get()
        print("The response of StripeSaaSBillingApi->get_billing_history_api_v1_billing_history_get:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling StripeSaaSBillingApi->get_billing_history_api_v1_billing_history_get: %s\n" % e)
```



### Parameters

This endpoint does not need any parameter.

### Return type

[**List[BillingHistoryItem]**](BillingHistoryItem.md)

### Authorization

[HTTPBearer](../README.md#HTTPBearer)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

### HTTP response details

| Status code | Description | Response headers |
|-------------|-------------|------------------|
**200** | Successful Response |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **stripe_webhook_api_v1_billing_webhook_post**
> object stripe_webhook_api_v1_billing_webhook_post(stripe_signature=stripe_signature)

Stripe Webhook Listener for asynchronous payment fulfillment

Receives and verifies Stripe webhook events, automatically provisioning credits in PostgreSQL.

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
    api_instance = codevideo_client.StripeSaaSBillingApi(api_client)
    stripe_signature = 'stripe_signature_example' # str |  (optional)

    try:
        # Stripe Webhook Listener for asynchronous payment fulfillment
        api_response = api_instance.stripe_webhook_api_v1_billing_webhook_post(stripe_signature=stripe_signature)
        print("The response of StripeSaaSBillingApi->stripe_webhook_api_v1_billing_webhook_post:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling StripeSaaSBillingApi->stripe_webhook_api_v1_billing_webhook_post: %s\n" % e)
```



### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **stripe_signature** | **str**|  | [optional] 

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

