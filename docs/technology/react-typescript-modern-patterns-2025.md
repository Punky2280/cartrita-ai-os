# React TypeScript Modern Patterns and Best Practices (2025)

## Overview
This document outlines the modern patterns and best practices for React TypeScript development as of 2025, based on community consensus and industry standards.

## Component Architecture

### Direct Function Typing Over React.FC
**Recommended approach:**
```typescript
type Props = { 
  title: string; 
  children?: React.ReactNode;
};

const MyComponent = ({ title, children }: Props) => (
  <div>
    <h1>{title}</h1>
    {children}
  </div>
);
```

**Why this is preferred:**
- Simpler and more predictable typing
- Avoids implicit children prop issues
- Better TypeScript inference
- Community consensus has moved away from React.FC

### Performance Optimization Patterns

#### Essential Hooks Usage
- `useState`, `useEffect`, and `useContext` for core functionality
- `React.memo` to prevent unnecessary re-renders
- `useMemo` and `useCallback` for expensive operations
- `React.lazy` for code-splitting

#### Custom Hooks for Reusability
Custom hooks represent the most powerful pattern for extracting stateful logic:
```typescript
// Example custom hook pattern
function useLocalStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      return initialValue;
    }
  });

  const setValue = (value: T | ((val: T) => T)) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      window.localStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.log(error);
    }
  };

  return [storedValue, setValue] as const;
}
```

### Advanced TypeScript Patterns

#### Component Props Inheritance
```typescript
import { ComponentProps } from 'react';

type ButtonProps = ComponentProps<'button'> & {
  variant?: 'primary' | 'secondary';
};

function CustomButton({ variant = 'primary', ...props }: ButtonProps) {
  return <button className={`btn btn-${variant}`} {...props} />;
}
```

#### Generic Components
```typescript
interface ListProps<T> {
  items: T[];
  renderItem: (item: T) => React.ReactNode;
}

function List<T>({ items, renderItem }: ListProps<T>) {
  return (
    <ul>
      {items.map((item, index) => (
        <li key={index}>{renderItem(item)}</li>
      ))}
    </ul>
  );
}
```

## 2025 Essential Practices

### 1. Default to TypeScript
- Every new project should use TypeScript
- Gradual migration strategies for existing projects
- Strict TypeScript configuration

### 2. Accessibility First
- Keyboard navigation support
- Screen reader compatibility
- WCAG compliance from the start
- Use semantic HTML elements

### 3. Server-First Thinking
- Consider server-side rendering capabilities
- Optimize for Core Web Vitals
- Use React Server Components where appropriate

### 4. Component-First Testing
- Use tools like Storybook for component development
- Write tests alongside components
- Focus on user behavior over implementation details

## State Management Patterns

### Local State Priority
```typescript
// Use local state for component-specific data
const [isOpen, setIsOpen] = useState(false);
const [inputValue, setInputValue] = useState('');
```

### Context for Shared State
```typescript
// Context for shared but not global state
const ThemeContext = createContext<{
  theme: 'light' | 'dark';
  toggleTheme: () => void;
}>({
  theme: 'light',
  toggleTheme: () => {},
});
```

### External Libraries for Complex State
- **Zustand**: Simple and performant
- **Jotai**: Atomic state management
- **TanStack Query**: Server state management
- **Redux Toolkit**: Complex application state

## Error Boundaries and Error Handling

```typescript
interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundary extends Component<
  PropsWithChildren<{}>,
  ErrorBoundaryState
> {
  constructor(props: PropsWithChildren<{}>) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error boundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-fallback">
          <h2>Something went wrong.</h2>
          <p>{this.state.error?.message}</p>
        </div>
      );
    }

    return this.props.children;
  }
}
```

## Modern Bundle Optimization

### Code Splitting Patterns
```typescript
// Route-based code splitting
const Home = lazy(() => import('./pages/Home'));
const About = lazy(() => import('./pages/About'));

// Component-based code splitting
const HeavyComponent = lazy(() => import('./components/HeavyComponent'));
```

### Tree Shaking Optimization
- Use ES6 modules
- Import only what you need
- Configure bundler properly

## Development Workflow

### ESLint and Prettier Configuration
```json
{
  "extends": [
    "@typescript-eslint/recommended",
    "plugin:react/recommended",
    "plugin:react-hooks/recommended"
  ],
  "rules": {
    "@typescript-eslint/no-unused-vars": "error",
    "react/react-in-jsx-scope": "off",
    "react-hooks/exhaustive-deps": "warn"
  }
}
```

### Husky Pre-commit Hooks
- Type checking before commit
- Lint and format code
- Run unit tests
- Build verification

## Key Takeaways for 2025

1. **Abandon React.FC** - Use direct prop typing
2. **TypeScript by default** - No exceptions for new projects
3. **Accessibility first** - Built-in, not added later
4. **Performance-oriented** - Use React.memo, useMemo, useCallback wisely
5. **Custom hooks** - Extract and reuse stateful logic
6. **Component composition** - Prefer composition over inheritance
7. **Error boundaries** - Handle errors gracefully
8. **Testing strategy** - Component-first testing approach

## Implementation Priority

1. Set up TypeScript with strict configuration
2. Implement accessibility features from the start
3. Create reusable custom hooks
4. Set up error boundaries
5. Optimize performance with proper memoization
6. Implement comprehensive testing strategy

This guide represents the current best practices for React TypeScript development in 2025, emphasizing performance, maintainability, and developer experience.