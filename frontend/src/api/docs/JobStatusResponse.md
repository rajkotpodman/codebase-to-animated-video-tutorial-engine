
# JobStatusResponse

Job status, progress percentage, and final output artifacts.

## Properties

Name | Type
------------ | -------------
`job_id` | string
`status` | string
`progress` | number
`step` | number
`step_name` | string
`message` | string
`result` | { [key: string]: any; }
`error` | string
`download_url` | string

## Example

```typescript
import type { JobStatusResponse } from ''

// TODO: Update the object below with actual values
const example = {
  "job_id": null,
  "status": null,
  "progress": null,
  "step": null,
  "step_name": null,
  "message": null,
  "result": null,
  "error": null,
  "download_url": null,
} satisfies JobStatusResponse

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as JobStatusResponse
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


