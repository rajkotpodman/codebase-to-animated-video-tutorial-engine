
# BillingHistoryItem


## Properties

Name | Type
------------ | -------------
`id` | string
`job_id` | string
`repo_name` | string
`timestamp` | string
`duration_seconds` | number
`resolution` | string
`cost_credits` | number
`cost_usd` | number
`status` | string

## Example

```typescript
import type { BillingHistoryItem } from ''

// TODO: Update the object below with actual values
const example = {
  "id": null,
  "job_id": null,
  "repo_name": null,
  "timestamp": null,
  "duration_seconds": null,
  "resolution": null,
  "cost_credits": null,
  "cost_usd": null,
  "status": null,
} satisfies BillingHistoryItem

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as BillingHistoryItem
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


