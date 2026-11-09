# UserBalanceResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**user_id** | **str** |  | 
**email** | **str** |  | 
**credits** | **int** |  | 
**plan** | **str** |  | 
**cost_per_tutorial_usd** | **float** |  | 
**currency** | **str** |  | 

## Example

```python
from codevideo_client.models.user_balance_response import UserBalanceResponse

# TODO update the JSON string below
json = "{}"
# create an instance of UserBalanceResponse from a JSON string
user_balance_response_instance = UserBalanceResponse.from_json(json)
# print the JSON string representation of the object
print(UserBalanceResponse.to_json())

# convert the object into a dict
user_balance_response_dict = user_balance_response_instance.to_dict()
# create an instance of UserBalanceResponse from a dict
user_balance_response_from_dict = UserBalanceResponse.from_dict(user_balance_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


