
# GenerateVideoResponse

Immediate response confirming task enqueue.

## Properties

Name | Type
------------ | -------------
`job_id` | string
`status` | string
`status_url` | string
`message` | string

## Example

```typescript
import type { GenerateVideoResponse } from ''

// TODO: Update the object below with actual values
const example = {
  "job_id": null,
  "status": null,
  "status_url": null,
  "message": null,
} satisfies GenerateVideoResponse

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as GenerateVideoResponse
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


