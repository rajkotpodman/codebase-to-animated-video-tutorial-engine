# GenerateVideoRequest

Payload for initiating tutorial video generation.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**repo_url** | **str** | Public GitHub repository URL (e.g. &#39;https://github.com/octocat/Hello-World&#39;) | 
**voice** | **str** | Neural TTS voice model (e.g. &#39;en-US-ChristopherNeural&#39;, &#39;en-US-GuyNeural&#39;, &#39;en-US-JennyNeural&#39;) | [optional] [default to 'en-US-ChristopherNeural']
**resolution** | **str** | Target output video resolution | [optional] [default to '1080p']
**theme** | **str** | Manim architecture diagram styling theme | [optional] [default to 'midnight']
**burn_subtitles** | **bool** | Whether to burn synchronized subtitles directly into the video stream | [optional] [default to True]
**custom_instructions** | **str** | Optional custom focus prompt for Gemini script generation (e.g. &#39;Focus on auth &amp; caching&#39;) | [optional] 
**run_sync** | **bool** | If True, runs synchronously in-process (useful for local debugging or non-Celery environments) | [optional] [default to False]

## Example

```python
from codevideo_client.models.generate_video_request import GenerateVideoRequest

# TODO update the JSON string below
json = "{}"
# create an instance of GenerateVideoRequest from a JSON string
generate_video_request_instance = GenerateVideoRequest.from_json(json)
# print the JSON string representation of the object
print(GenerateVideoRequest.to_json())

# convert the object into a dict
generate_video_request_dict = generate_video_request_instance.to_dict()
# create an instance of GenerateVideoRequest from a dict
generate_video_request_from_dict = GenerateVideoRequest.from_dict(generate_video_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


