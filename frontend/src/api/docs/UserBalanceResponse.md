
# UserBalanceResponse


## Properties

Name | Type
------------ | -------------
`user_id` | string
`email` | string
`credits` | number
`plan` | string
`cost_per_tutorial_usd` | number
`currency` | string

## Example

```typescript
import type { UserBalanceResponse } from ''

// TODO: Update the object below with actual values
const example = {
  "user_id": null,
  "email": null,
  "credits": null,
  "plan": null,
  "cost_per_tutorial_usd": null,
  "currency": null,
} satisfies UserBalanceResponse

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as UserBalanceResponse
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


