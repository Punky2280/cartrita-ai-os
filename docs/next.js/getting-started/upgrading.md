# Upgrading

## Latest version

To update to the latest version of Next.js, you can use the `upgrade` codemod:

```bash
npx @next/codemod@latest upgrade latest
```

If you prefer to upgrade manually, install the latest Next.js and React versions:

```bash
# Using pnpm
pnpm i next@latest react@latest react-dom@latest eslint-config-next@latest

# Using npm
npm i next@latest react@latest react-dom@latest eslint-config-next@latest

# Using yarn
yarn add next@latest react@latest react-dom@latest eslint-config-next@latest

# Using bun
bun add next@latest react@latest react-dom@latest eslint-config-next@latest
```

## Canary version

To update to the latest canary, make sure you're on the latest version of Next.js and everything is working as expected. Then, run the following command:

```bash
npm i next@canary
```

### Features available in canary

The following features are currently available in canary:

**Caching:**

- ["use cache"](https://nextjs.org/docs/app/api-reference/directives/use-cache)
- [cacheLife](https://nextjs.org/docs/app/api-reference/functions/cacheLife)
- [cacheTag](https://nextjs.org/docs/app/api-reference/functions/cacheTag)
- [cacheComponents](https://nextjs.org/docs/app/api-reference/config/next-config-js/cacheComponents)

**Authentication:**

- [forbidden](https://nextjs.org/docs/app/api-reference/functions/forbidden)
- [unauthorized](https://nextjs.org/docs/app/api-reference/functions/unauthorized)
- [forbidden.js](https://nextjs.org/docs/app/api-reference/file-conventions/forbidden)
- [unauthorized.js](https://nextjs.org/docs/app/api-reference/file-conventions/unauthorized)
- [authInterrupts](https://nextjs.org/docs/app/api-reference/config/next-config-js/authInterrupts)

## Version guides

See the version guides for in-depth upgrade instructions.

- [Version 15 - Upgrade your Next.js Application from Version 14 to 15.](https://nextjs.org/docs/app/guides/upgrading/version-15)
- [Version 14 - Upgrade your Next.js Application from Version 13 to 14.](https://nextjs.org/docs/app/guides/upgrading/version-14)
