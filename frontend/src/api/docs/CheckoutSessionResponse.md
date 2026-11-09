
# CheckoutSessionResponse


## Properties

Name | Type
------------ | -------------
`checkout_url` | string
`session_id` | string
`package_name` | string
`credits` | number
`amount_usd` | number

## Example

```typescript
import type { CheckoutSessionResponse } from ''

// TODO: Update the object below with actual values
const example = {
  "checkout_url": null,
  "session_id": null,
  "package_name": null,
  "credits": null,
  "amount_usd": null,
} satisfies CheckoutSessionResponse

console.log(example)

// Convert the instance to a JSON string
const exampleJSON: string = JSON.stringify(example)
console.log(exampleJSON)

// Parse the JSON string back to an object
const exampleParsed = JSON.parse(exampleJSON) as CheckoutSessionResponse
console.log(exampleParsed)
```

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


