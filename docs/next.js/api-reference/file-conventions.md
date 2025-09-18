# File-system conventions

Next.js uses a file-system based router where folders are used to define routes. Each folder represents a route segment that maps to a URL segment. To create a route, you can create a folder and add the necessary route files.

## Route Files

The following files are used to define routes in the App Router:

### `page.js`

Creates a route that users can visit. Required for each route segment.

### `layout.js`

Creates a shared layout for a segment and its children. Useful for adding UI that is shared across routes.

### `loading.js`

Creates a loading UI for a segment and its children. Automatically wraps pages and layouts in a `<Suspense>` boundary.

### `error.js`

Creates an error UI for a segment and its children. Automatically wraps pages and layouts in an error boundary.

### `not-found.js`

Creates a UI for when the `notFound()` function is thrown within a route segment.

### `template.js`

Similar to `layout.js`, but creates a new instance for each child on navigation. Useful for animations.

### `default.js`

Creates a fallback page for [Parallel Routes](https://nextjs.org/docs/app/api-reference/file-conventions/parallel-routes).

## Route Groups and Organization

### Route Groups

Organize routes without affecting the URL structure using parentheses `()`.

### Dynamic Routes

Create routes that can handle dynamic data using square brackets `[]`.

### Parallel Routes

Render multiple pages simultaneously in the same view.

### Intercepting Routes

Intercept routes to load them within the current layout.

## Data Fetching and API Routes

### `route.js`

Create API endpoints and handle server-side logic.

### Middleware

Run code before a request is completed using `middleware.js`.

## Special Files

### `instrumentation.js`

Add instrumentation for monitoring and observability.

### `instrumentation-client.js`

Add client-side instrumentation.

### `mdx-components.js`

Configure MDX components globally.

## Metadata and Static Assets

### Metadata Files

Configure metadata for routes using special metadata files.

### `public` folder

Serve static assets like images, fonts, and other files.

## Configuration

### Route Segment Config

Configure options for individual route segments.

## Examples

### Basic Route

```bash
app/
  page.js          # /
  layout.js        # Root layout
  dashboard/
    page.js        # /dashboard
    layout.js      # Dashboard layout
```

### Dynamic Route

```bash
app/
  blog/
    [slug]/
      page.js      # /blog/[slug]
```

### Route Group

```bash
app/
  (marketing)/
    about/
      page.js      # /about
    blog/
      page.js      # /blog
```

### Parallel Routes

```bash
app/
  dashboard/
    @sidebar/
      page.js      # Sidebar slot
    @content/
      page.js      # Content slot
    layout.js      # Dashboard layout with slots
```

## File Naming Conventions

- Files must be named exactly as specified (e.g., `page.js`, `layout.js`)
- Files can be `.js`, `.jsx`, `.ts`, or `.tsx`
- Special files like `page.js` are required for routes to be accessible
- Layout files wrap child segments automatically

## Route Priority

Routes are matched in the following order:

1. Static routes
2. Dynamic routes with fixed segments
3. Dynamic routes with catch-all segments
4. Parallel routes
5. Intercepting routes

## Best Practices

- Use `layout.js` for shared UI across routes
- Use `loading.js` for loading states
- Use `error.js` for error boundaries
- Use route groups to organize code without affecting URLs
- Use parallel routes for complex layouts with multiple panels
- Use intercepting routes for modals and advanced navigation patterns

## Related

- [Routing Fundamentals](https://nextjs.org/docs/app/getting-started/project-structure)
- [Layouts and Pages](https://nextjs.org/docs/app/getting-started/layouts-and-pages)
- [Dynamic Routes](https://nextjs.org/docs/app/api-reference/file-conventions/dynamic-routes)
- [Parallel Routes](https://nextjs.org/docs/app/api-reference/file-conventions/parallel-routes)
