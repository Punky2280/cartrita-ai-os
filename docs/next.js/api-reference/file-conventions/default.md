# default.js

The `default.js` file is used to render a fallback within
[Parallel Routes](https://nextjs.org/docs/app/api-reference/file-conventions/parallel-routes) when Next.js cannot
recover a [slot's](https://nextjs.org/docs/app/api-reference/file-conventions/parallel-routes#slots) active state
after a full-page load.

During [soft navigation](https://nextjs.org/docs/app/getting-started/linking-and-navigating#client-side-transitions),
Next.js keeps track of the active state (subpage) for each slot. However, for hard
navigations (e.g. reloading the page), Next.js can't recover the active state. In
this case, it will render the `default.js` file for the unmatched slots.

Consider the following folder structure. The `@team` slot has a `settings` page, but `@analytics` does not.

![Parallel Routes unmatched routes](https://nextjs.org/_next/image?url=https%3A%2F%2Fh8DxKfmAPhn8O0p3.public.blob.vercel-storage.com%2Fdocs%2Fdark%2Fparallel-routes-unmatched-routes.png&w=1920&q=75)

When navigating to `/settings`, the `@team` slot will render the `settings` page
while maintaining the currently active page for the `@analytics` slot.

On refresh, Next.js will render a `default.js` for `@analytics`. If `default.js` doesn't exist, a `404` is rendered instead.

Additionally, since `children` is an implicit slot, you also need to create a
`default.js` file to render a fallback for `children` when Next.js cannot
recover the active state of the parent page.

## Reference

### params (optional)

A promise that resolves to an object containing the
[dynamic route parameters](https://nextjs.org/docs/app/api-reference/file-conventions/dynamic-routes)
from the root segment down to the slot's subpages. For example:

```js
export default async function Default({
  params,
}: {
  params: Promise<{ artist: string }>
}) {
  const { artist } = await params
}
```

| Route | URL | `params` |
| --- | --- | --- |
| `app/[artist]/@sidebar/default.js` | `/zack` | `Promise<{ artist: 'zack' }>` |
| `app/[artist]/[album]/@sidebar/default.js` | `/zack/next` | `Promise<{ artist: 'zack', album: 'next' }>` |

- Since the `params` prop is a promise. You must use `async/await` or React's
  [use](https://react.dev/reference/react/use) function to access the values.
- In version 14 and earlier, `params` was a synchronous prop. To help with
  backwards compatibility, you can still access it synchronously in Next.js 15,
  but this behavior will be deprecated in the future.

## Learn more about Parallel Routes

[Parallel Routes Simultaneously render one or more pages in the same view that can be navigated independently. A pattern for highly dynamic applications.](https://nextjs.org/docs/app/api-reference/file-conventions/parallel-routes)
