# Loading UI and Streaming

The special file `loading.js` helps you create meaningful Loading UI with [React Suspense](https://react.dev/reference/react/Suspense). With this convention, you can show an [instant loading state](#instant-loading-states) from the server while the content of a route segment streams in. The new content is automatically swapped in once complete.

![Loading UI](https://nextjs.org/_next/image?url=https%3A%2F%2Fh8DxKfmAPhn8O0p3.public.blob.vercel-storage.com%2Fdocs%2Fdark%2Floading-ui.png&w=1920&q=75)

```tsx
// app/feed/loading.tsx
export default function Loading() {
  // Or a custom loading skeleton component
  return <p>Loading...</p>
}
```

Inside the `loading.js` file, you can add any light-weight loading UI. You may find it helpful to use the [React Developer Tools](https://react.dev/learn/react-developer-tools) to manually toggle Suspense boundaries.

By default, this file is a [Server Component](https://nextjs.org/docs/app/getting-started/server-and-client-components) - but can also be used as a Client Component through the `"use client"` directive.

## Reference

### Parameters

Loading UI components do not accept any parameters.

## Behavior

### Navigation

- The Fallback UI is [prefetched](https://nextjs.org/docs/app/getting-started/linking-and-navigating#prefetching), making navigation is immediate unless prefetching hasn't completed.
- Navigation is interruptible, meaning changing routes does not need to wait for the content of the route to fully load before navigating to another route.
- Shared layouts remain interactive while new route segments load.

### Instant Loading States

An instant loading state is fallback UI that is shown immediately upon navigation. You can pre-render loading indicators such as skeletons and spinners, or a small but meaningful part of future screens such as a cover photo, title, etc. This helps users understand the app is responding and provides a better user experience.

Create a loading state by adding a `loading.js` file inside a folder.

![loading.js special file](https://nextjs.org/_next/image?url=https%3A%2F%2Fh8DxKfmAPhn8O0p3.public.blob.vercel-storage.com%2Fdocs%2Fdark%2Floading-special-file.png&w=1920&q=75)

```tsx
// app/dashboard/loading.tsx
export default function Loading() {
  // You can add any UI inside Loading, including a Skeleton.
  return <LoadingSkeleton />
}
```

In the same folder, `loading.js` will be nested inside `layout.js`. It will automatically wrap the `page.js` file and any children below in a `<Suspense>` boundary.

![loading.js overview](https://nextjs.org/_next/image?url=https%3A%2F%2Fh8DxKfmAPhn8O0p3.public.blob.vercel-storage.com%2Fdocs%2Fdark%2Floading-overview.png&w=1920&q=75)

### SEO

- Next.js will wait for data fetching inside [generateMetadata](https://nextjs.org/docs/app/api-reference/functions/generate-metadata) to complete before streaming UI to the client. This guarantees the first part of a streamed response includes `<head>` tags.
- Since streaming is server-rendered, it does not impact SEO. You can use the [Rich Results Test](https://search.google.com/test/rich-results) tool from Google to see how your page appears to Google's web crawlers and view the serialized HTML ([source](https://web.dev/rendering-on-the-web/#seo-considerations)).

### Status Codes

When streaming, a `200` status code will be returned to signal that the request was successful.

The server can still communicate errors or issues to the client within the streamed content itself, for example, when using [redirect](https://nextjs.org/docs/app/api-reference/functions/redirect) or [notFound](https://nextjs.org/docs/app/api-reference/functions/not-found). Since the response headers have already been sent to the client, the status code of the response cannot be updated. This does not affect SEO.

### Browser limits

[Some browsers](https://bugs.webkit.org/show_bug.cgi?id=252413) buffer a streaming response. You may not see the streamed response until the response exceeds 1024 bytes. This typically only affects "hello world" applications, but not real applications.

## Platform Support

| | |
|---|---|
| Node.js server | Yes |
| Docker container | Yes |
| Static export | No |
| Adapters | Platform-specific |

Learn how to [configure streaming](https://nextjs.org/docs/app/guides/self-hosting#streaming-and-suspense) when self-hosting Next.js.

## Examples

### Streaming with Suspense

In addition to `loading.js`, you can also manually create Suspense Boundaries for your own UI components. The App Router supports streaming with [Suspense](https://react.dev/reference/react/Suspense).

`<Suspense>` works by wrapping a component that performs an asynchronous action (e.g. fetch data), showing fallback UI (e.g. skeleton, spinner) while it's happening, and then swapping in your component once the action completes.

```tsx
// app/dashboard/page.tsx
import { Suspense } from 'react'
import { PostFeed, Weather } from './Components'

export default function Posts() {
  return (
    <section>
      <Suspense fallback={<p>Loading feed...</p>}>
        <PostFeed />
      </Suspense>
      <Suspense fallback={<p>Loading weather...</p>}>
        <Weather />
      </Suspense>
    </section>
  )
}
```

By using Suspense, you get the benefits of:

1. Streaming Server Rendering - Progressively rendering HTML from the server to the client.
2. Selective Hydration - React prioritizes what components to make interactive first based on user interaction.

For more Suspense examples and use cases, please see the [React Documentation](https://react.dev/reference/react/Suspense).

## Version History

| | |
|---|---|
| v13.0.0 | loading introduced. |
