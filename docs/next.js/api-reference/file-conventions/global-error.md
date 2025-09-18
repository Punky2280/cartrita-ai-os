# global-error.js

The `global-error.js` file is used to catch errors that occur in the root layout and in nested route segments.

> **Good to know**
>
> - A `global-error.js` file is used to handle errors that occur in the root layout.
> - It is only triggered when the app is running in production.
> - It replaces the root `layout.js` when active, so it must define its own `<html>` and `<body>` tags.
> - It is less granular than `error.js` boundaries and should only be used for handling truly global errors.

## Convention

A `global-error.js` file should export a default function that returns a React component.

```javascript
// app/global-error.js

'use client'

export default function GlobalError({
  error,
  reset,
}) {
  return (
    <html>
      <body>
        <h2>Something went wrong!</h2>
        <button onClick={() => reset()}>Try again</button>
      </body>
    </html>
  )
}
```

## Props

### `error`

An instance of an `Error` object forwarded to the `global-error.js` Client Component.

#### `error.message`

The error message. For errors forwarded from Client Components this will be the original Error's message.
For errors forwarded from Server Components, this will be a generic error message to avoid leaking sensitive details.

#### `error.digest`

An automatically generated hash of the error thrown in a Server Component. It can be used to match the corresponding error in server-side logs.

### `reset`

A function to reset the error boundary. When executed, the function will try to re-render the Error boundary's contents.

## Examples

### Basic Usage

You can use a `global-error.js` file to handle errors that occur in the root layout.

```javascript
// app/global-error.js

'use client'

export default function GlobalError({
  error,
  reset,
}) {
  return (
    <html>
      <body>
        <h2>Something went wrong!</h2>
        <button onClick={() => reset()}>Try again</button>
      </body>
    </html>
  )
}
```

## Version History

| Version | Changes |
| --- | --- |
| `v13.0.0` | `global-error.js` introduced. |
