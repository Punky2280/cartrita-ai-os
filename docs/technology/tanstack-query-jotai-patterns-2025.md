# TanStack Query and Jotai Integration Patterns (2025)

## Overview
This document outlines modern state management patterns combining TanStack Query for server state and Jotai for atomic client state management, representing best practices for React applications in 2025.

## TanStack Query Best Practices

### Core Query Patterns

#### Basic useQuery Pattern
```typescript
import { useQuery } from '@tanstack/react-query';
import { ApiResponse, User } from '@/types';

// Query key factory for consistency
export const userKeys = {
  all: ['users'] as const,
  lists: () => [...userKeys.all, 'list'] as const,
  list: (filters: string) => [...userKeys.lists(), { filters }] as const,
  details: () => [...userKeys.all, 'detail'] as const,
  detail: (id: string) => [...userKeys.details(), id] as const,
};

// Modern query pattern with proper typing
function useUser(id: string) {
  return useQuery({
    queryKey: userKeys.detail(id),
    queryFn: async (): Promise<ApiResponse<User>> => {
      const response = await fetch(`/api/users/${id}`);
      if (!response.ok) {
        throw new Error('Failed to fetch user');
      }
      return response.json();
    },
    enabled: !!id, // Only run when ID is available
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
    retry: (failureCount, error) => {
      if (error instanceof Error && error.message.includes('404')) {
        return false; // Don't retry 404s
      }
      return failureCount < 3;
    },
  });
}
```

#### Advanced Query with Suspense
```typescript
import { useSuspenseQuery } from '@tanstack/react-query';

function UserProfile({ userId }: { userId: string }) {
  const { data: user } = useSuspenseQuery({
    queryKey: userKeys.detail(userId),
    queryFn: () => fetchUser(userId),
  });

  // No need to check loading state or handle undefined data
  return (
    <div>
      <h1>{user.name}</h1>
      <p>{user.email}</p>
    </div>
  );
}

// Wrap with Suspense boundary
function UserProfileWrapper({ userId }: { userId: string }) {
  return (
    <Suspense fallback={<UserProfileSkeleton />}>
      <ErrorBoundary fallback={<ErrorMessage />}>
        <UserProfile userId={userId} />
      </ErrorBoundary>
    </Suspense>
  );
}
```

### Mutation Patterns

#### Optimistic Updates Pattern
```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query';

function useUpdateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (userData: Partial<User> & { id: string }) => {
      const response = await fetch(`/api/users/${userData.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(userData),
      });
      
      if (!response.ok) {
        throw new Error('Update failed');
      }
      
      return response.json();
    },
    
    // Optimistic update
    onMutate: async (updatedUser) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ 
        queryKey: userKeys.detail(updatedUser.id) 
      });

      // Snapshot previous value
      const previousUser = queryClient.getQueryData(
        userKeys.detail(updatedUser.id)
      );

      // Optimistically update
      queryClient.setQueryData(
        userKeys.detail(updatedUser.id),
        (old: ApiResponse<User> | undefined) => ({
          ...old!,
          data: { ...old!.data, ...updatedUser }
        })
      );

      return { previousUser, updatedUser };
    },

    // Rollback on error
    onError: (err, updatedUser, context) => {
      if (context?.previousUser) {
        queryClient.setQueryData(
          userKeys.detail(updatedUser.id),
          context.previousUser
        );
      }
    },

    // Always refetch after success or error
    onSettled: (data, error, updatedUser) => {
      queryClient.invalidateQueries({ 
        queryKey: userKeys.detail(updatedUser.id) 
      });
    },
  });
}
```

#### Batch Mutations Pattern
```typescript
function useBatchUpdateUsers() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (updates: Array<Partial<User> & { id: string }>) => {
      const promises = updates.map(user =>
        fetch(`/api/users/${user.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(user),
        })
      );

      const responses = await Promise.allSettled(promises);
      
      const results = await Promise.all(
        responses.map(async (response, index) => {
          if (response.status === 'fulfilled' && response.value.ok) {
            return {
              success: true,
              data: await response.value.json(),
              id: updates[index].id
            };
          }
          return {
            success: false,
            error: response.status === 'fulfilled' 
              ? await response.value.text() 
              : response.reason,
            id: updates[index].id
          };
        })
      );

      return results;
    },

    onSuccess: (results) => {
      results.forEach(result => {
        if (result.success) {
          // Update individual user cache
          queryClient.setQueryData(
            userKeys.detail(result.id),
            result.data
          );
        }
      });

      // Invalidate lists to ensure consistency
      queryClient.invalidateQueries({ queryKey: userKeys.lists() });
    },
  });
}
```

### Infinite Queries Pattern
```typescript
interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    hasNext: boolean;
  };
}

function useInfiniteUsers(filters?: Record<string, any>) {
  return useInfiniteQuery({
    queryKey: userKeys.list(JSON.stringify(filters)),
    queryFn: async ({ pageParam = 1 }): Promise<PaginatedResponse<User>> => {
      const params = new URLSearchParams({
        page: pageParam.toString(),
        limit: '20',
        ...filters,
      });

      const response = await fetch(`/api/users?${params}`);
      if (!response.ok) {
        throw new Error('Failed to fetch users');
      }
      return response.json();
    },
    initialPageParam: 1,
    getNextPageParam: (lastPage) => 
      lastPage.pagination.hasNext ? lastPage.pagination.page + 1 : undefined,
    select: (data) => ({
      pages: data.pages,
      pageParams: data.pageParams,
      // Flatten all users into a single array
      allUsers: data.pages.flatMap(page => page.data),
    }),
    staleTime: 30 * 1000, // 30 seconds
  });
}

// Usage in component
function InfiniteUserList() {
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    status,
  } = useInfiniteUsers();

  if (status === 'pending') return <LoadingSpinner />;
  if (status === 'error') return <ErrorMessage />;

  return (
    <div>
      {data.allUsers.map(user => (
        <UserCard key={user.id} user={user} />
      ))}
      
      {hasNextPage && (
        <button
          onClick={() => fetchNextPage()}
          disabled={isFetchingNextPage}
        >
          {isFetchingNextPage ? 'Loading...' : 'Load More'}
        </button>
      )}
    </div>
  );
}
```

## Jotai Atomic State Management

### Basic Atom Patterns

```typescript
import { atom, useAtom, useAtomValue, useSetAtom } from 'jotai';

// Primitive atoms
export const countAtom = atom(0);
export const nameAtom = atom('');
export const isLoadingAtom = atom(false);

// Read-only derived atom
export const doubleCountAtom = atom((get) => get(countAtom) * 2);

// Read-write derived atom
export const uppercaseNameAtom = atom(
  (get) => get(nameAtom).toUpperCase(),
  (get, set, newValue: string) => {
    set(nameAtom, newValue.toLowerCase());
  }
);

// Complex state atom
interface UserPreferences {
  theme: 'light' | 'dark';
  language: string;
  notifications: boolean;
}

export const userPreferencesAtom = atom<UserPreferences>({
  theme: 'light',
  language: 'en',
  notifications: true,
});

// Derived atom for theme-specific styles
export const themeStylesAtom = atom((get) => {
  const preferences = get(userPreferencesAtom);
  return preferences.theme === 'dark' ? darkStyles : lightStyles;
});
```

### Custom Atom Hooks Pattern

```typescript
// Custom hook combining multiple related atoms
export function useCounter() {
  const [count, setCount] = useAtom(countAtom);
  const doubleCount = useAtomValue(doubleCountAtom);

  const increment = useCallback(() => setCount(c => c + 1), [setCount]);
  const decrement = useCallback(() => setCount(c => c - 1), [setCount]);
  const reset = useCallback(() => setCount(0), [setCount]);

  return {
    count,
    doubleCount,
    increment,
    decrement,
    reset,
  };
}

// Custom hook for complex state management
export function useUserPreferences() {
  const [preferences, setPreferences] = useAtom(userPreferencesAtom);
  const themeStyles = useAtomValue(themeStylesAtom);

  const updateTheme = useCallback((theme: 'light' | 'dark') => {
    setPreferences(prev => ({ ...prev, theme }));
  }, [setPreferences]);

  const updateLanguage = useCallback((language: string) => {
    setPreferences(prev => ({ ...prev, language }));
  }, [setPreferences]);

  const toggleNotifications = useCallback(() => {
    setPreferences(prev => ({ ...prev, notifications: !prev.notifications }));
  }, [setPreferences]);

  return {
    preferences,
    themeStyles,
    updateTheme,
    updateLanguage,
    toggleNotifications,
  };
}
```

### Async Atoms Pattern

```typescript
// Async atom for API calls
export const userProfileAtom = atom(async (get) => {
  const userId = get(currentUserIdAtom);
  if (!userId) return null;

  const response = await fetch(`/api/users/${userId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch user profile');
  }
  return response.json();
});

// Atom with async write operation
export const updateUserAtom = atom(
  null, // No read function
  async (get, set, update: Partial<User>) => {
    const currentProfile = get(userProfileAtom);
    if (!currentProfile) return;

    set(isLoadingAtom, true);
    
    try {
      const response = await fetch(`/api/users/${currentProfile.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(update),
      });

      if (!response.ok) {
        throw new Error('Update failed');
      }

      const updatedUser = await response.json();
      
      // Trigger refresh of user profile atom
      set(userProfileAtom, updatedUser);
      
      return updatedUser;
    } finally {
      set(isLoadingAtom, false);
    }
  }
);

// Usage in component
function UserProfileEditor() {
  const userProfile = useAtomValue(userProfileAtom);
  const updateUser = useSetAtom(updateUserAtom);
  const isLoading = useAtomValue(isLoadingAtom);

  const handleSave = async (updates: Partial<User>) => {
    try {
      await updateUser(updates);
      toast.success('Profile updated!');
    } catch (error) {
      toast.error('Update failed');
    }
  };

  if (!userProfile) return <div>Loading...</div>;

  return (
    <form onSubmit={(e) => {
      e.preventDefault();
      const formData = new FormData(e.target as HTMLFormElement);
      handleSave(Object.fromEntries(formData));
    }}>
      <input 
        name="name" 
        defaultValue={userProfile.name} 
        disabled={isLoading}
      />
      <button type="submit" disabled={isLoading}>
        {isLoading ? 'Saving...' : 'Save'}
      </button>
    </form>
  );
}
```

## Combined TanStack Query + Jotai Patterns

### Server State Synchronization Pattern

```typescript
// Jotai atom that syncs with TanStack Query
export const userQueryAtom = atom(
  (get) => {
    const userId = get(currentUserIdAtom);
    if (!userId) return null;

    // This creates a query that will be managed by TanStack Query
    return {
      queryKey: userKeys.detail(userId),
      queryFn: () => fetchUser(userId),
      staleTime: 5 * 60 * 1000,
    };
  }
);

// Custom hook combining both libraries
export function useSyncedUser() {
  const queryConfig = useAtomValue(userQueryAtom);
  const [currentUserId, setCurrentUserId] = useAtom(currentUserIdAtom);

  const queryResult = useQuery({
    ...queryConfig,
    enabled: !!queryConfig,
  });

  // Synchronize successful queries with local atom
  useEffect(() => {
    if (queryResult.data && queryResult.isSuccess) {
      // You could sync specific fields to local atoms if needed
    }
  }, [queryResult.data, queryResult.isSuccess]);

  return {
    ...queryResult,
    currentUserId,
    setCurrentUserId,
  };
}
```

### Local Storage Persistence Pattern

```typescript
import { atomWithStorage } from 'jotai/utils';

// Persistent atoms using localStorage
export const persistentUserPreferencesAtom = atomWithStorage<UserPreferences>(
  'userPreferences',
  {
    theme: 'light',
    language: 'en',
    notifications: true,
  }
);

// Combine persistent local state with server state
export function usePersistedUserData() {
  const [preferences, setPreferences] = useAtom(persistentUserPreferencesAtom);
  
  const { data: serverUserData, isLoading } = useQuery({
    queryKey: ['user', 'server-data'],
    queryFn: fetchUserFromServer,
    staleTime: 10 * 60 * 1000,
  });

  // Merge server data with local preferences
  const combinedUserData = useMemo(() => ({
    ...serverUserData,
    preferences,
  }), [serverUserData, preferences]);

  const updatePreferences = useCallback((updates: Partial<UserPreferences>) => {
    setPreferences(prev => ({ ...prev, ...updates }));
  }, [setPreferences]);

  return {
    userData: combinedUserData,
    isLoading,
    updatePreferences,
  };
}
```

### Optimistic Updates with Atomic State

```typescript
// Local optimistic state
export const optimisticUpdatesAtom = atom<Record<string, any>>({});

// Mutation hook with optimistic updates
export function useOptimisticMutation<TData, TVariables>(
  mutationFn: (variables: TVariables) => Promise<TData>,
  options?: {
    onSuccess?: (data: TData, variables: TVariables) => void;
    onError?: (error: Error, variables: TVariables) => void;
  }
) {
  const [optimisticData, setOptimisticData] = useAtom(optimisticUpdatesAtom);
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn,
    onMutate: async (variables) => {
      // Set optimistic state
      const optimisticId = Math.random().toString(36);
      setOptimisticData(prev => ({
        ...prev,
        [optimisticId]: { status: 'pending', variables }
      }));

      return { optimisticId };
    },
    onSuccess: (data, variables, context) => {
      // Clear optimistic state
      setOptimisticData(prev => {
        const newState = { ...prev };
        delete newState[context!.optimisticId];
        return newState;
      });

      options?.onSuccess?.(data, variables);
    },
    onError: (error, variables, context) => {
      // Update optimistic state with error
      setOptimisticData(prev => ({
        ...prev,
        [context!.optimisticId]: { 
          status: 'error', 
          variables, 
          error: error.message 
        }
      }));

      options?.onError?.(error, variables);
    },
  });
}
```

### Form State Management Pattern

```typescript
// Form atom with validation
interface FormState<T> {
  values: T;
  errors: Record<keyof T, string>;
  touched: Record<keyof T, boolean>;
  isSubmitting: boolean;
}

export function atomWithForm<T extends Record<string, any>>(
  initialValues: T,
  validator?: (values: T) => Record<keyof T, string>
) {
  const formAtom = atom<FormState<T>>({
    values: initialValues,
    errors: {} as Record<keyof T, string>,
    touched: {} as Record<keyof T, boolean>,
    isSubmitting: false,
  });

  const updateFieldAtom = atom(
    null,
    (get, set, update: { field: keyof T; value: any }) => {
      const currentState = get(formAtom);
      const newValues = {
        ...currentState.values,
        [update.field]: update.value,
      };

      const errors = validator ? validator(newValues) : {};

      set(formAtom, {
        ...currentState,
        values: newValues,
        errors,
        touched: {
          ...currentState.touched,
          [update.field]: true,
        },
      });
    }
  );

  return {
    formAtom,
    updateFieldAtom,
  };
}

// Usage in form component
export function UserForm() {
  const { formAtom, updateFieldAtom } = useMemo(
    () => atomWithForm(
      { name: '', email: '', age: 0 },
      (values) => {
        const errors: any = {};
        if (!values.name) errors.name = 'Name is required';
        if (!values.email) errors.email = 'Email is required';
        if (values.age < 0) errors.age = 'Age must be positive';
        return errors;
      }
    ),
    []
  );

  const [formState] = useAtom(formAtom);
  const updateField = useSetAtom(updateFieldAtom);

  const createUserMutation = useMutation({
    mutationFn: (userData: typeof formState.values) => 
      createUser(userData),
    onSuccess: () => {
      toast.success('User created!');
    },
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (Object.keys(formState.errors).length === 0) {
      await createUserMutation.mutateAsync(formState.values);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        value={formState.values.name}
        onChange={(e) => updateField({ field: 'name', value: e.target.value })}
      />
      {formState.touched.name && formState.errors.name && (
        <span className="error">{formState.errors.name}</span>
      )}
      
      <button 
        type="submit" 
        disabled={createUserMutation.isPending || Object.keys(formState.errors).length > 0}
      >
        {createUserMutation.isPending ? 'Creating...' : 'Create User'}
      </button>
    </form>
  );
}
```

## Performance Optimization Patterns

### Selective Re-renders with Jotai

```typescript
// Split atoms to minimize re-renders
export const userDataAtom = atom({
  name: 'John',
  email: 'john@example.com',
  profile: {
    avatar: 'avatar.jpg',
    bio: 'Developer',
  },
  settings: {
    theme: 'dark',
    notifications: true,
  },
});

// Focused atoms for specific UI components
export const userNameAtom = atom(
  (get) => get(userDataAtom).name,
  (get, set, newName: string) => {
    const current = get(userDataAtom);
    set(userDataAtom, { ...current, name: newName });
  }
);

export const userThemeAtom = atom(
  (get) => get(userDataAtom).settings.theme,
  (get, set, newTheme: 'light' | 'dark') => {
    const current = get(userDataAtom);
    set(userDataAtom, {
      ...current,
      settings: { ...current.settings, theme: newTheme },
    });
  }
);

// Components only re-render when their specific atom changes
function UserName() {
  const [name, setName] = useAtom(userNameAtom);
  return (
    <input 
      value={name} 
      onChange={(e) => setName(e.target.value)} 
    />
  );
}

function ThemeToggle() {
  const [theme, setTheme] = useAtom(userThemeAtom);
  return (
    <button onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}>
      Current theme: {theme}
    </button>
  );
}
```

### Query Invalidation Patterns

```typescript
// Centralized invalidation patterns
export const invalidationPatterns = {
  user: (userId: string) => [
    userKeys.detail(userId),
    userKeys.lists(),
  ],
  
  conversation: (conversationId: string) => [
    ['conversations', conversationId],
    ['conversations', 'list'],
    ['messages', conversationId],
  ],
  
  global: () => [
    ['user'],
    ['conversations'],
    ['agents'],
  ],
};

// Mutation hook with smart invalidation
export function useSmartInvalidation() {
  const queryClient = useQueryClient();

  const invalidateQueries = useCallback((pattern: keyof typeof invalidationPatterns, id?: string) => {
    const queryKeys = invalidationPatterns[pattern](id as any);
    
    return Promise.all(
      queryKeys.map(queryKey => 
        queryClient.invalidateQueries({ queryKey })
      )
    );
  }, [queryClient]);

  return { invalidateQueries };
}
```

## Key Takeaways for 2025

### TanStack Query Best Practices
1. **Query Key Factories**: Use consistent, hierarchical query keys
2. **Error Boundaries**: Implement proper error handling with Suspense
3. **Optimistic Updates**: Use for better UX in mutations
4. **Selective Invalidation**: Minimize unnecessary refetches
5. **Infinite Queries**: For paginated data with scroll interactions

### Jotai Best Practices
1. **Atomic Design**: Keep atoms small and focused
2. **Custom Hooks**: Encapsulate complex atom interactions
3. **Storage Integration**: Use `atomWithStorage` for persistence
4. **Performance**: Split atoms to minimize re-renders
5. **Async Patterns**: Handle async operations gracefully

### Combined Patterns
1. **Clear Boundaries**: Server state in TanStack Query, client state in Jotai
2. **Sync Carefully**: Only sync when necessary, avoid over-synchronization
3. **Optimistic Updates**: Combine local atoms with server mutations
4. **Form Handling**: Use atoms for complex form state with validation
5. **Testing Strategy**: Test atoms and queries independently

This integration provides a powerful, performant, and maintainable approach to state management in modern React applications.