# BillingHistoryItem


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **str** |  | 
**job_id** | **str** |  | 
**repo_name** | **str** |  | 
**timestamp** | **str** |  | 
**duration_seconds** | **int** |  | 
**resolution** | **str** |  | 
**cost_credits** | **int** |  | 
**cost_usd** | **float** |  | 
**status** | **str** |  | 

## Example

```python
from codevideo_client.models.billing_history_item import BillingHistoryItem

# TODO update the JSON string below
json = "{}"
# create an instance of BillingHistoryItem from a JSON string
billing_history_item_instance = BillingHistoryItem.from_json(json)
# print the JSON string representation of the object
print(BillingHistoryItem.to_json())

# convert the object into a dict
billing_history_item_dict = billing_history_item_instance.to_dict()
# create an instance of BillingHistoryItem from a dict
billing_history_item_from_dict = BillingHistoryItem.from_dict(billing_history_item_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


