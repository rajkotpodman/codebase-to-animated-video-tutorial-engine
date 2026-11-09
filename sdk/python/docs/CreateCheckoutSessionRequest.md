# CreateCheckoutSessionRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**package_id** | **str** | Catalog identifier for desired package (&#39;single_tutorial&#39;, &#39;starter_10&#39;, &#39;pro_50&#39;, &#39;studio_200&#39;) | [optional] [default to 'pro_50']

## Example

```python
from codevideo_client.models.create_checkout_session_request import CreateCheckoutSessionRequest

# TODO update the JSON string below
json = "{}"
# create an instance of CreateCheckoutSessionRequest from a JSON string
create_checkout_session_request_instance = CreateCheckoutSessionRequest.from_json(json)
# print the JSON string representation of the object
print(CreateCheckoutSessionRequest.to_json())

# convert the object into a dict
create_checkout_session_request_dict = create_checkout_session_request_instance.to_dict()
# create an instance of CreateCheckoutSessionRequest from a dict
create_checkout_session_request_from_dict = CreateCheckoutSessionRequest.from_dict(create_checkout_session_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


