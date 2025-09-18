
# sitemap.js

The `sitemap.js` file allows you to generate a `sitemap.xml` file for your application.

> **Good to know**
>
> - You can use a `sitemap.js` file to generate a sitemap for your application.
> - The `sitemap.js` file should export a default function that returns an array of objects.
> - Each object in the array should have a `url` and `lastModified` property.
> - The `url` property should be the absolute URL of the page.
> - The `lastModified` property should be a `Date` object.

## Convention

A `sitemap.js` file should export a default function that returns an array of objects.

```javascript
// app/sitemap.js

export default function sitemap() {
  return [
    {
      url: 'https://acme.com',
      lastModified: new Date(),
    },
    {
      url: 'https://acme.com/about',
      lastModified: new Date(),
    },
  ]
}
```

## Examples

### Static Sitemap

You can generate a static sitemap by returning an array of objects.

```javascript
// app/sitemap.js

export default function sitemap() {
  return [
    {
      url: 'https://acme.com',
      lastModified: new Date(),
    },
    {
      url: 'https://acme.com/about',
      lastModified: new Date(),
    },
  ]
}
```

### Dynamic Sitemap

You can generate a dynamic sitemap by fetching data and returning an array of objects.

```javascript
// app/sitemap.js

export default async function sitemap() {
  const res = await fetch('https://.../posts')
  const posts = await res.json()

  const postEntries = posts.map((post) => ({
    url: `https://acme.com/blog/${post.slug}`,
    lastModified: new Date(post.lastModified),
  }))

  return [
    {
      url: 'https://acme.com',
      lastModified: new Date(),
    },
    {
      url: 'https://acme.com/about',
      lastModified: new Date(),
    },
    ...postEntries,
  ]
}
```

### Multiple Sitemaps

You can generate multiple sitemaps by creating a `sitemap.js` file in each route segment.

For example, you can create a `sitemap.js` file in the `app/blog` directory to generate a sitemap for your blog posts.

```javascript
// app/blog/sitemap.js

export default async function sitemap() {
  const res = await fetch('https://.../posts')
  const posts = await res.json()

  return posts.map((post) => ({
    url: `https://acme.com/blog/${post.slug}`,
    lastModified: new Date(post.lastModified),
  }))
}
```

## Version History

| Version | Changes |
| --- | --- |
| `v13.0.0` | `sitemap.js` introduced. |
