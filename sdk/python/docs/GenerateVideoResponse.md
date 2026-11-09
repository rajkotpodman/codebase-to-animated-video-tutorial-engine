# GenerateVideoResponse

Immediate response confirming task enqueue.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**job_id** | **str** |  | 
**status** | **str** |  | 
**status_url** | **str** |  | 
**message** | **str** |  | 

## Example

```python
from codevideo_client.models.generate_video_response import GenerateVideoResponse

# TODO update the JSON string below
json = "{}"
# create an instance of GenerateVideoResponse from a JSON string
generate_video_response_instance = GenerateVideoResponse.from_json(json)
# print the JSON string representation of the object
print(GenerateVideoResponse.to_json())

# convert the object into a dict
generate_video_response_dict = generate_video_response_instance.to_dict()
# create an instance of GenerateVideoResponse from a dict
generate_video_response_from_dict = GenerateVideoResponse.from_dict(generate_video_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


