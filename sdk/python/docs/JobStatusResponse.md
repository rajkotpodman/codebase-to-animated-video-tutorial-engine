# JobStatusResponse

Job status, progress percentage, and final output artifacts.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**job_id** | **str** |  | 
**status** | **str** |  | 
**progress** | **int** |  | 
**step** | **int** |  | [optional] 
**step_name** | **str** |  | [optional] 
**message** | **str** |  | [optional] 
**result** | **Dict[str, object]** |  | [optional] 
**error** | **str** |  | [optional] 
**download_url** | **str** |  | [optional] 

## Example

```python
from codevideo_client.models.job_status_response import JobStatusResponse

# TODO update the JSON string below
json = "{}"
# create an instance of JobStatusResponse from a JSON string
job_status_response_instance = JobStatusResponse.from_json(json)
# print the JSON string representation of the object
print(JobStatusResponse.to_json())

# convert the object into a dict
job_status_response_dict = job_status_response_instance.to_dict()
# create an instance of JobStatusResponse from a dict
job_status_response_from_dict = JobStatusResponse.from_dict(job_status_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


