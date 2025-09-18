# layout.js

The `layout` file is used to define a layout in your Next.js application.

```tsx
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return <section>{children}</section>
}
```

A root layout is the top-most layout in the root `app` directory. It is used to define the `<html>` and `<body>` tags
and other globally shared UI.

```tsx
export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
```

## Reference

### Props

#### children (required)

Layout components should accept and use a `children` prop. During rendering, `children` will be populated with the route segments
the layout is wrapping. These will primarily be the component of a child Layout (if it exists) or Page, but could also be other special files
like Loading or Error when applicable.

#### params (optional)

A promise that resolves to an object containing the [dynamic route parameters](https://nextjs.org/docs/app/api-reference/file-conventions/dynamic-routes)
object from the root segment down to that layout.

```tsx
export default async function Layout({
  children,
  params,
}: {
  children: React.ReactNode
  params: Promise<{ team: string }>
}) {
  const { team } = await params
}
```

| Route | URL | params |
|-------|-----|--------|
| app/dashboard/[team]/layout.js | /dashboard/1 | Promise<{ team: '1' }> |
| app/shop/[tag]/[item]/layout.js | /shop/1/2 | Promise<{ tag: '1', item: '2' }> |
| app/blog/[...slug]/layout.js | /blog/1/2 | Promise<{ slug: ['1', '2'] }> |

- Since the `params` prop is a promise. You must use `async/await` or React's [use](https://react.dev/reference/react/use) function to access the values.
- In version 14 and earlier, `params` was a synchronous prop. To help with backwards compatibility,
  you can still access it synchronously in Next.js 15, but this behavior will be deprecated in the future.

### Layout Props Helper

You can type layouts with `LayoutProps` to get a strongly typed `params` and named slots inferred from your directory structure.
`LayoutProps` is a globally available helper.

```tsx
export default function Layout(props: LayoutProps<'/dashboard'>) {
  return (
    <section>
      {props.children}
      {/* If you have app/dashboard/@analytics, it appears as a typed slot: */}
      {/* {props.analytics} */}
    </section>
  )
}
```

Good to know:

- Types are generated during `next dev`, `next build`, or `next typegen`.

### Root Layout

The `app` directory must include a root layout, which is the top-most layout in the root `app` directory. Typically, the root layout is `app/layout.js`.

```tsx
export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html>
      <body>{children}</body>
    </html>
  )
}
```

- The root layout must define `<html>` and `<body>` tags.
- You should not manually add `<head>` tags such as `<title>` and `<meta>` to root layouts. Instead, you should use the
  [Metadata API](https://nextjs.org/docs/app/getting-started/metadata-and-og-images) which automatically handles advanced requirements
  such as streaming and de-duplicating `<head>` elements.
- You can use [route groups](https://nextjs.org/docs/app/api-reference/file-conventions/route-groups) to create multiple root layouts.
- Navigating across multiple root layouts will cause a full page load (as opposed to a client-side navigation). For example,
  navigating from `/cart` that uses `app/(shop)/layout.js` to `/blog` that uses `app/(marketing)/layout.js` will cause a full page load.
  This only applies to multiple root layouts.
- The root layout can be under a dynamic segment, for example when implementing
  [internationalization](https://nextjs.org/docs/app/guides/internationalization) with `app/[lang]/layout.js`.

## Caveats

### Request Object

Layouts are cached in the client during navigation to avoid unnecessary server requests.

Layouts do not rerender. They can be cached and reused to avoid unnecessary computation when navigating between pages.
By restricting layouts from accessing the raw request, Next.js can prevent the execution of potentially slow or expensive user code within the layout,
which could negatively impact performance.

To access the request object, you can use [headers](https://nextjs.org/docs/app/api-reference/functions/headers) and
[cookies](https://nextjs.org/docs/app/api-reference/functions/cookies) APIs in Server Components and Functions.

```tsx
import { cookies } from 'next/headers'

export default async function Layout({ children }) {
  const cookieStore = await cookies()
  const theme = cookieStore.get('theme')
  return '...'
}
```

### Query params

Layouts do not rerender on navigation, so they cannot access search params which would otherwise become stale.

To access updated query parameters, you can use the Page [searchParams](https://nextjs.org/docs/app/api-reference/file-conventions/page#searchparams-optional) prop,
or read them inside a Client Component using the [useSearchParams](https://nextjs.org/docs/app/api-reference/functions/use-search-params) hook.
Since Client Components re-render on navigation, they have access to the latest query parameters.

```tsx
'use client'
import { useSearchParams } from 'next/navigation'

export default function Search() {
  const searchParams = useSearchParams()
  const search = searchParams.get('search')
  return '...'
}
```

```tsx
import Search from '@/app/ui/search'

export default function Layout({ children }) {
  return (
    <>
      <Search />
      {children}
    </>
  )
}
```

### Pathname

Layouts do not re-render on navigation, so they do not access pathname which would otherwise become stale.

To access the current pathname, you can read it inside a Client Component using the [usePathname](https://nextjs.org/docs/app/api-reference/functions/use-pathname) hook.
Since Client Components re-render during navigation, they have access to the latest pathname.

```tsx
'use client'
import { usePathname } from 'next/navigation'

// Simplified breadcrumbs logic
export default function Breadcrumbs() {
  const pathname = usePathname()
  const segments = pathname.split('/')
  return (
    <nav>
      {segments.map((segment, index) => (
        <span key={index}>
          {' > '}
          {segment}
        </span>
      ))}
    </nav>
  )
}
```

```tsx
import { Breadcrumbs } from '@/app/ui/Breadcrumbs'

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <Breadcrumbs />
      <main>{children}</main>
    </>
  )
}
```

### Fetching Data

Layouts cannot pass data to their `children`. However, you can fetch the same data in a route more than once, and use React [cache](https://react.dev/reference/react/cache)
to dedupe the requests without affecting performance.

Alternatively, when using [fetch](https://nextjs.org/docs/app/api-reference/functions/fetch) in Next.js, requests are automatically deduped.

```tsx
export async function getUser(id: string) {
  const res = await fetch(`https://.../users/${id}`)
  return res.json()
}
```

```tsx
import { getUser } from '@/app/lib/data'
import { UserName } from '@/app/ui/user-name'

export default async function Layout({ children }) {
  const user = await getUser('1')
  return (
    <>
      <nav>
        {/* ... */}
        <UserName user={user.name} />
      </nav>
      {children}
    </>
  )
}
```

```tsx
import { getUser } from '@/app/lib/data'
import { UserName } from '@/app/ui/user-name'

export default async function Page() {
  const user = await getUser('1')
  return (
    <div>
      <h1>Welcome {user.name}</h1>
    </div>
  )
}
```

### Accessing child segments

Layouts do not have access to the route segments below itself. To access all route segments, you can use [useSelectedLayoutSegment](https://nextjs.org/docs/app/api-reference/functions/use-selected-layout-segment)
or [useSelectedLayoutSegments](https://nextjs.org/docs/app/api-reference/functions/use-selected-layout-segments) in a Client Component.

```tsx
'use client'
import Link from 'next/link'
import { useSelectedLayoutSegment } from 'next/navigation'

export default function NavLink({
  slug,
  children,
}: {
  slug: string
  children: React.ReactNode
}) {
  const segment = useSelectedLayoutSegment()
  const isActive = slug === segment
  return (
    <Link
      href={`/blog/${slug}`}
      style={{
        fontWeight: isActive ? 'bold' : 'normal'
      }}
    >
      {children}
    </Link>
  )
}
```

```tsx
import { NavLink } from './nav-link'
import getPosts from './get-posts'

export default async function Layout({
  children,
}: {
  children: React.ReactNode
}) {
  const featuredPosts = await getPosts()
  return (
    <div>
      {featuredPosts.map((post) => (
        <div key={post.id}>
          <NavLink slug={post.slug}>{post.title}</NavLink>
        </div>
      ))}
      <div>{children}</div>
    </div>
  )
}
```

## Examples

### Metadata

You can modify the `<head>` HTML elements such as `title` and `meta` using the [metadata object](https://nextjs.org/docs/app/api-reference/functions/generate-metadata#the-metadata-object)
or [generateMetadata function](https://nextjs.org/docs/app/api-reference/functions/generate-metadata#generatemetadata-function).

```tsx
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Next.js',
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return '...'
}
```

Good to know: You should not manually add `<head>` tags such as `<title>` and `<meta>` to root layouts. Instead, use the [Metadata APIs](https://nextjs.org/docs/app/api-reference/functions/generate-metadata)
which automatically handles advanced requirements such as streaming and de-duplicating `<head>` elements.

### Active Nav Links

You can use the [usePathname](https://nextjs.org/docs/app/api-reference/functions/use-pathname) hook to determine if a nav link is active.

Since `usePathname` is a client hook, you need to extract the nav links into a Client Component, which can be imported into your layout:

```tsx
'use client'
import { usePathname } from 'next/navigation'
import Link from 'next/link'

export function NavLinks() {
  const pathname = usePathname()
  return (
    <nav>
      <Link className={`link ${pathname === '/' ? 'active' : ''}`} href="/">
        Home
      </Link>
      <Link
        className={`link ${pathname === '/about' ? 'active' : ''}`}
        href="/about"
      >
        About
      </Link>
    </nav>
  )
}
```

```tsx
import { NavLinks } from '@/app/ui/nav-links'

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <NavLinks />
        <main>{children}</main>
      </body>
    </html>
  )
}
```

### Displaying content based on params

Using [dynamic route segments](https://nextjs.org/docs/app/api-reference/file-conventions/dynamic-routes),
you can display or fetch specific content based on the `params` prop.

```tsx
export default async function DashboardLayout({
  children,
  params,
}: {
  children: React.ReactNode
  params: Promise<{ team: string }>
}) {
  const { team } = await params
  return (
    <section>
      <header>
        <h1>Welcome to {team}'s Dashboard</h1>
      </header>
      <main>{children}</main>
    </section>
  )
}
```

### Reading params in Client Components

To use `params` in a Client Component (which cannot be `async`), you can use React's
[use](https://react.dev/reference/react/use) function to read the promise:

```tsx
'use client'
import { use } from 'react'

export default function Page({
  params,
}: {
  params: Promise<{ slug: string }>
}) {
  const { slug } = use(params)
}
```

## Version History

| Version | Changes |
|---------|---------|
| v15.0.0-RC | params is now a promise. A codemod is available. |
| v13.0.0 | layout introduced. |
