# Frontend Architecture

*Parent: [ARCHITECTURE.md](../ARCHITECTURE.md)*

React + Vite frontend architecture with TypeScript.

**Key Concepts**:
- React Query for server state, Zustand for UI state
- shadcn/ui components with Tailwind styling
- Feature-based component organization
- PWA with offline support

---

## State Management

| Type | Tool | Purpose |
|------|------|---------|
| Server state | React Query | API data, caching, sync |
| UI state | Zustand | Sidebar, modals, filters |
| Form state | React Hook Form | Form validation |

### Why This Split?

- **React Query**: Handles all the complexity of server data (caching, background refresh, optimistic updates, retry)
- **Zustand**: Simple, no boilerplate, no context providers, great DevTools
- **React Hook Form**: Performant forms with minimal re-renders

---

## Data Fetching

```typescript
// hooks/useItems.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export function useItems(projectId: string) {
    return useQuery({
        queryKey: ['projects', projectId, 'items'],
        queryFn: () => api.getItems(projectId),
        staleTime: 1000 * 60 * 5, // 5 minutes
    });
}

export function useCreateItem(projectId: string) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: CreateItemRequest) =>
            api.createItem(projectId, data),
        onSuccess: () => {
            // Invalidate items list to refetch
            queryClient.invalidateQueries({
                queryKey: ['projects', projectId, 'items']
            });
        },
    });
}

export function useUpdateItem(projectId: string) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ itemNum, data }: { itemNum: number; data: UpdateItemRequest }) =>
            api.updateItem(projectId, itemNum, data),
        onMutate: async ({ itemNum, data }) => {
            // Optimistic update
            await queryClient.cancelQueries({
                queryKey: ['projects', projectId, 'items']
            });

            const previous = queryClient.getQueryData(['projects', projectId, 'items']);

            queryClient.setQueryData(
                ['projects', projectId, 'items'],
                (old: Item[]) => old.map(item =>
                    item.item_num === itemNum ? { ...item, ...data } : item
                )
            );

            return { previous };
        },
        onError: (err, variables, context) => {
            // Rollback on error
            queryClient.setQueryData(
                ['projects', projectId, 'items'],
                context?.previous
            );
        },
    });
}
```

---

## UI State with Zustand

```typescript
// stores/uiStore.ts
import { create } from 'zustand';

interface UIState {
    sidebarOpen: boolean;
    toggleSidebar: () => void;

    currentFilters: ItemFilters;
    setFilters: (filters: ItemFilters) => void;
    clearFilters: () => void;

    selectedItems: string[];
    toggleItemSelection: (id: string) => void;
    clearSelection: () => void;
}

export const useUIStore = create<UIState>((set) => ({
    sidebarOpen: true,
    toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),

    currentFilters: {},
    setFilters: (filters) => set({ currentFilters: filters }),
    clearFilters: () => set({ currentFilters: {} }),

    selectedItems: [],
    toggleItemSelection: (id) => set((state) => ({
        selectedItems: state.selectedItems.includes(id)
            ? state.selectedItems.filter(i => i !== id)
            : [...state.selectedItems, id]
    })),
    clearSelection: () => set({ selectedItems: [] }),
}));
```

---

## Component Structure

```
components/
├── ui/                    # shadcn/ui primitives
│   ├── button.tsx         # Button variants
│   ├── card.tsx           # Card container
│   ├── dialog.tsx         # Modal dialogs
│   ├── table.tsx          # Data tables
│   └── ...
│
├── layout/                # Layout components
│   ├── Sidebar.tsx        # Navigation sidebar
│   ├── Header.tsx         # Top header bar
│   └── MainLayout.tsx     # Page wrapper
│
└── features/              # Feature components
    ├── items/
    │   ├── ItemTable.tsx       # Item list table
    │   ├── ItemCard.tsx        # Single item card
    │   ├── EditItemDialog.tsx  # Create/edit modal
    │   └── ItemFilters.tsx     # Filter controls
    │
    ├── budget/
    │   ├── BudgetMetrics.tsx   # Key metrics cards
    │   ├── BurnChart.tsx       # Burn rate chart
    │   └── AllocationTable.tsx # Budget breakdown
    │
    └── chat/
        ├── ChatPanel.tsx       # Chat container
        ├── MessageList.tsx     # Message history
        └── ChatInput.tsx       # Message input
```

---

## Component Example

```tsx
// components/features/items/ItemTable.tsx
import { useItems } from '@/hooks/useItems';
import { useUIStore } from '@/stores/uiStore';
import { Table, TableHeader, TableBody, TableRow, TableCell } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';

interface ItemTableProps {
    projectId: string;
}

export function ItemTable({ projectId }: ItemTableProps) {
    const { data: items, isLoading, error } = useItems(projectId);
    const { currentFilters, selectedItems, toggleItemSelection } = useUIStore();

    if (isLoading) return <TableSkeleton />;
    if (error) return <ErrorState error={error} />;

    const filteredItems = applyFilters(items, currentFilters);

    return (
        <Table>
            <TableHeader>
                <TableRow>
                    <TableCell>#</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Title</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Assigned</TableCell>
                </TableRow>
            </TableHeader>
            <TableBody>
                {filteredItems.map(item => (
                    <TableRow
                        key={item.id}
                        selected={selectedItems.includes(item.id)}
                        onClick={() => toggleItemSelection(item.id)}
                    >
                        <TableCell>{item.item_num}</TableCell>
                        <TableCell>
                            <Badge variant={getTypeVariant(item.type)}>
                                {item.type}
                            </Badge>
                        </TableCell>
                        <TableCell>{item.title}</TableCell>
                        <TableCell>
                            <IndicatorBadge indicator={item.indicator} />
                        </TableCell>
                        <TableCell>{item.assigned_to}</TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    );
}
```

---

## API Client

```typescript
// lib/api.ts
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/v1';

class ApiClient {
    private accessToken: string | null = null;

    setAccessToken(token: string) {
        this.accessToken = token;
    }

    private async fetch<T>(
        path: string,
        options: RequestInit = {}
    ): Promise<T> {
        const headers: HeadersInit = {
            'Content-Type': 'application/json',
            ...options.headers,
        };

        if (this.accessToken) {
            headers['Authorization'] = `Bearer ${this.accessToken}`;
        }

        const response = await fetch(`${BASE_URL}${path}`, {
            ...options,
            headers,
            credentials: 'include', // For refresh token cookie
        });

        if (response.status === 401) {
            // Try refresh
            await this.refreshToken();
            return this.fetch(path, options);
        }

        if (!response.ok) {
            const error = await response.json();
            throw new ApiError(error);
        }

        return response.json();
    }

    // API methods
    getProjects = () => this.fetch<Project[]>('/projects');
    getItems = (projectId: string) =>
        this.fetch<Item[]>(`/projects/${projectId}/items`);
    createItem = (projectId: string, data: CreateItemRequest) =>
        this.fetch<Item>(`/projects/${projectId}/items`, {
            method: 'POST',
            body: JSON.stringify(data),
        });
}

export const api = new ApiClient();
```

---

## PWA Configuration

```typescript
// vite.config.ts
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
    plugins: [
        react(),
        VitePWA({
            registerType: 'autoUpdate',
            manifest: {
                name: 'braidMgr',
                short_name: 'braidMgr',
                theme_color: '#1a1a2e',
                icons: [
                    { src: '/icon-192.png', sizes: '192x192', type: 'image/png' },
                    { src: '/icon-512.png', sizes: '512x512', type: 'image/png' },
                ],
            },
            workbox: {
                runtimeCaching: [
                    {
                        urlPattern: /^https:\/\/api\.braidmgr\.com\/v1\/.*/,
                        handler: 'NetworkFirst',
                        options: {
                            cacheName: 'api-cache',
                            expiration: { maxEntries: 100, maxAgeSeconds: 3600 },
                        },
                    },
                ],
            },
        }),
    ],
});
```
