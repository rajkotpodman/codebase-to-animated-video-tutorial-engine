# CheckoutSessionResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**checkout_url** | **str** |  | 
**session_id** | **str** |  | 
**package_name** | **str** |  | 
**credits** | **int** |  | 
**amount_usd** | **float** |  | 

## Example

```python
from codevideo_client.models.checkout_session_response import CheckoutSessionResponse

# TODO update the JSON string below
json = "{}"
# create an instance of CheckoutSessionResponse from a JSON string
checkout_session_response_instance = CheckoutSessionResponse.from_json(json)
# print the JSON string representation of the object
print(CheckoutSessionResponse.to_json())

# convert the object into a dict
checkout_session_response_dict = checkout_session_response_instance.to_dict()
# create an instance of CheckoutSessionResponse from a dict
checkout_session_response_from_dict = CheckoutSessionResponse.from_dict(checkout_session_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


