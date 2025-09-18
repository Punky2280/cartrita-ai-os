# Optimizing

This guide covers performance optimization techniques for Next.js applications, including bundle analysis, package optimization, and production best practices.

## Analyzing JavaScript Bundles

[@next/bundle-analyzer](https://www.npmjs.com/package/@next/bundle-analyzer) is a plugin for Next.js that helps you manage the size of your application bundles. It generates a visual report of the size of each package and their dependencies.

### Installation

Install the plugin by running the following command:

```bash
npm i @next/bundle-analyzer
# or
yarn add @next/bundle-analyzer
# or
pnpm add @next/bundle-analyzer
```

Then, add the bundle analyzer's settings to your `next.config.js`.

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {}

const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
})

module.exports = withBundleAnalyzer(nextConfig)
```

### Generating a Report

Run the following command to analyze your bundles:

```bash
ANALYZE=true npm run build
# or
ANALYZE=true yarn build
# or
ANALYZE=true pnpm build
```

The report will open three new tabs in your browser, which you can inspect. Periodically evaluating your application's bundles can help you maintain application performance over time.

## Optimizing Package Imports

Some packages, such as icon libraries, can export hundreds of modules, which can cause performance issues in development and production.

You can optimize how these packages are imported by adding the [optimizePackageImports](https://nextjs.org/docs/app/api-reference/config/next-config-js/optimizePackageImports) option to your `next.config.js`. This option will only load the modules you actually use, while still giving you the convenience of writing import statements with many named exports.

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    optimizePackageImports: ['icon-library'],
  },
}

module.exports = nextConfig
```

Next.js also optimizes some libraries automatically, thus they do not need to be included in the optimizePackageImports list. See the [full list](https://nextjs.org/docs/app/api-reference/config/next-config-js/optimizePackageImports).

## Opting Specific Packages Out of Bundling

Since packages imported inside Server Components and Route Handlers are automatically bundled by Next.js, you can opt specific packages out of bundling using the [serverExternalPackages](https://nextjs.org/docs/app/api-reference/config/next-config-js/serverExternalPackages) option in your `next.config.js`.

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  serverExternalPackages: ['package-name'],
}

module.exports = nextConfig
```

Next.js includes a list of popular packages that currently are working on compatibility and automatically opt-ed out. See the [full list](https://nextjs.org/docs/app/api-reference/config/next-config-js/serverExternalPackages).

## Production Optimization Checklist

### Automatic Optimizations

These Next.js optimizations are enabled by default and require no configuration:

- **Server Components**: Next.js uses Server Components by default. Server Components run on the server, and don't require JavaScript to render on the client. As such, they have no impact on the size of your client-side JavaScript bundles.
- **Code-splitting**: Server Components enable automatic code-splitting by route segments. You may also consider [lazy loading](https://nextjs.org/docs/app/guides/lazy-loading) Client Components and third-party libraries, where appropriate.
- **Prefetching**: When a link to a new route enters the user's viewport, Next.js prefetches the route in background. This makes navigation to new routes almost instant. You can opt out of prefetching, where appropriate.
- **Static Rendering**: Next.js statically renders Server and Client Components on the server at build time and caches the rendered result to improve your application's performance. You can opt into [Dynamic Rendering](https://nextjs.org/docs/app/getting-started/partial-prerendering#dynamic-rendering) for specific routes, where appropriate.
- **Caching**: Next.js caches data requests, the rendered result of Server and Client Components, static assets, and more, to reduce the number of network requests to your server, database, and backend services. You may opt out of caching, where appropriate.

These defaults aim to improve your application's performance, and reduce the cost and amount of data transferred on each network request.

### Development Best Practices

#### Routing and Rendering

- **Layouts**: Use layouts to share UI across pages and enable [partial rendering](https://nextjs.org/docs/app/getting-started/linking-and-navigating#client-side-transitions) on navigation.
- **Link Component**: Use the `<Link>` component for [client-side navigation and prefetching](https://nextjs.org/docs/app/getting-started/linking-and-navigating#how-navigation-works).
- **Error Handling**: Gracefully handle [catch-all errors](https://nextjs.org/docs/app/getting-started/error-handling) and [404 errors](https://nextjs.org/docs/app/api-reference/file-conventions/not-found) in production by creating custom error pages.
- **Client and Server Components**: Follow the recommended composition patterns for Server and Client Components, and check the placement of your ["use client" boundaries](https://nextjs.org/docs/app/getting-started/server-and-client-components#examples#moving-client-components-down-the-tree) to avoid unnecessarily increasing your client-side JavaScript bundle.
- **Dynamic APIs**: Be aware that Dynamic APIs like [cookies](https://nextjs.org/docs/app/api-reference/functions/cookies) and the [searchParams](https://nextjs.org/docs/app/api-reference/file-conventions/page#searchparams-optional) prop will opt the entire route into [Dynamic Rendering](https://nextjs.org/docs/app/getting-started/partial-prerendering#dynamic-rendering) (or your whole application if used in the [Root Layout](https://nextjs.org/docs/app/api-reference/file-conventions/layout#root-layout)). Ensure Dynamic API usage is intentional and wrap them in `<Suspense>` boundaries where appropriate.

> Good to know: [Partial Prerendering (experimental)](https://nextjs.org/blog/next-14#partial-prerendering-preview) will allow parts of a route to be dynamic without opting the whole route into dynamic rendering.

#### Data Fetching and Caching

- **Server Components**: Leverage the benefits of fetching data on the server using Server Components.
- **Route Handlers**: Use Route Handlers to access your backend resources from Client Components. But do not call Route Handlers from Server Components to avoid an additional server request.
- **Streaming**: Use Loading UI and React Suspense to progressively send UI from the server to the client, and prevent the whole route from blocking while data is being fetched.
- **Parallel Data Fetching**: Reduce network waterfalls by fetching data in parallel, where appropriate. Also, consider [preloading data](https://nextjs.org/docs/app/getting-started/fetching-data#preloading-data) where appropriate.
- **Data Caching**: Verify whether your data requests are being cached or not, and opt into caching, where appropriate. Ensure requests that don't use `fetch` are [cached](https://nextjs.org/docs/app/api-reference/functions/unstable_cache).
- **Static Images**: Use the `public` directory to automatically cache your application's static assets, e.g. images.

#### UI and Accessibility

- **Forms and Validation**: Use Server Actions to handle form submissions, server-side validation, and handle errors.
- **Global Error UI**: Add `app/global-error.tsx` to provide consistent, accessible fallback UI and recovery for uncaught errors across your app.
- **Global 404**: Add `app/global-not-found.tsx` to serve an accessible 404 for unmatched routes across your app.
- **Font Module**: Optimize fonts by using the Font Module, which automatically hosts your font files with other static assets, removes external network requests, and reduces [layout shift](https://web.dev/articles/cls).
- **Image Component**: Optimize images by using the Image Component, which automatically optimizes images, prevents layout shift, and serves them in modern formats like WebP.
- **Script Component**: Optimize third-party scripts by using the Script Component, which automatically defers scripts and prevents them from blocking the main thread.
- **ESLint**: Use the built-in `eslint-plugin-jsx-a11y` plugin to catch accessibility issues early.

#### Security

- **Tainting**: Prevent sensitive data from being exposed to the client by tainting data objects and/or specific values.
- **Server Actions**: Ensure users are authorized to call Server Actions. Review the recommended [security practices](https://nextjs.org/blog/security-nextjs-server-components-actions).
- **Environment Variables**: Ensure your `.env.*` files are added to `.gitignore` and only public variables are prefixed with `NEXT_PUBLIC_`.
- **Content Security Policy**: Consider adding a Content Security Policy to protect your application against various security threats such as cross-site scripting, clickjacking, and other code injection attacks.

#### Metadata and SEO

- **Metadata API**: Use the Metadata API to improve your application's Search Engine Optimization (SEO) by adding page titles, descriptions, and more.
- **Open Graph (OG) images**: Create OG images to prepare your application for social sharing.
- **Sitemaps** and **Robots**: Help Search Engines crawl and index your pages by generating sitemaps and robots files.

#### Type Safety

- **TypeScript and TS Plugin**: Use TypeScript and the TypeScript plugin for better type-safety, and to help you catch errors early.

### Pre-Production Checks

#### Core Web Vitals

- **Lighthouse**: Run lighthouse in incognito to gain a better understanding of how your users will experience your site, and to identify areas for improvement. This is a simulated test and should be paired with looking at field data (such as Core Web Vitals).
- **useReportWebVitals hook**: Use this hook to send [Core Web Vitals](https://web.dev/articles/vitals) data to analytics tools.

#### Bundle Analysis

Use the [@next/bundle-analyzer plugin](https://nextjs.org/docs/app/guides/package-bundling#analyzing-javascript-bundles) to analyze the size of your JavaScript bundles and identify large modules and dependencies that might be impacting your application's performance.

Additionally, the following tools can help you understand the impact of adding new dependencies to your application:

- [Import Cost](https://marketplace.visualstudio.com/items?itemName=wix.vscode-import-cost)
- [Package Phobia](https://packagephobia.com/)
- [Bundle Phobia](https://bundlephobia.com/)
- [bundlejs](https://bundlejs.com/)

## Additional Optimization Tools

### Bundle Analysis Tools

- **@next/bundle-analyzer**: Visual bundle size analysis
- **Import Cost**: VS Code extension showing import size
- **Package Phobia**: Package size analysis
- **Bundle Phobia**: Bundle size impact analysis
- **bundlejs**: Online bundle analysis tool

### Performance Monitoring

- **Lighthouse**: Comprehensive performance auditing
- **useReportWebVitals**: Core Web Vitals tracking
- **Web Vitals Library**: Detailed performance metrics

### Caching Strategies

- **Data Cache**: Automatic request deduplication
- **Full Route Cache**: Static rendering optimization
- **Router Cache**: Client-side navigation caching
- **unstable_cache**: Manual caching control

### Image Optimization

- **Next.js Image Component**: Automatic optimization and WebP conversion
- **Static Asset Caching**: Public directory automatic caching
- **Font Optimization**: Font Module for reduced layout shift

### Script Optimization

- **Script Component**: Third-party script deferral
- **Lazy Loading**: Dynamic imports for Client Components
- **Code Splitting**: Automatic route-based splitting

## Next Steps

Learn more about optimizing your application for production in the [Production Recommendations](https://nextjs.org/docs/app/guides/production-checklist) guide.
