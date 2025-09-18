
# template.js

The `template.js` file is a special file that allows you to create a template that is shared across routes.

> **Good to know**
>
> - A `template.js` file is similar to a `layout.js` file, except that a new instance of the template is created for each of its children.
> - Templates are useful for things that need to be re-created on every navigation, such as animations or effects that depend on the route.
> - For example, you can use a template to create a fade-in animation on page transitions.

## Convention

A `template.js` file should export a default function that returns a React component.

```javascript
// app/template.js

export default function Template({ children }) {
  return <div>{children}</div>
}
```

## Props

### `children`

The `children` prop is a React node that represents the content of the route segment.

## Examples

### Fade-in Animation

You can use a `template.js` file to create a fade-in animation on page transitions.

```javascript
// app/template.js

'use client'

import { motion } from 'framer-motion'

export default function Template({ children }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ ease: 'easeInOut', duration: 0.75 }}
    >
      {children}
    </motion.div>
  )
}
```

## Version History

| Version | Changes |
| --- | --- |
| `v13.0.0` | `template.js` introduced. |
