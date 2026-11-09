
# GenerateVideoRequest

Payload for initiating tutorial video generation.

## Properties

Name | Type
------------ | -------------
`repo_url` | string
`voice` | string
`resolution` | string
`theme` | string
`burn_subtitles` | boolean
`custom_instructions` | string
`run_sync` | boolean

## Example

```typescript
import type { GenerateVideoRequest } from ''

// TODO: Update the object below with actual values
const example = {
  "repo_url": null,
  "voice": null,
  "resolution": null,
  "theme": null,
  "burn_subtitles": null,
  "custom_instructions": null,
  "run_sync": null,
} satisfies GenerateVideoRequest

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as GenerateVideoRequest
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


