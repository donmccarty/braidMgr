# React Component Patterns

*Parent: [PATTERNS.md](../PATTERNS.md)*

React patterns for frontend development.

**Key Concepts**:
- React Query for server state
- shadcn/ui components with Tailwind
- Feature-based component organization
- TypeScript for type safety

---

## Data Fetching Hook

```typescript
// hooks/useItems.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Item, ItemCreate } from '@/types/item';

export function useItems(projectId: string) {
    return useQuery({
        queryKey: ['projects', projectId, 'items'],
        queryFn: () => api.getItems(projectId),
        staleTime: 1000 * 60 * 5, // 5 minutes
    });
}

export function useItem(projectId: string, itemNum: number) {
    return useQuery({
        queryKey: ['projects', projectId, 'items', itemNum],
        queryFn: () => api.getItem(projectId, itemNum),
    });
}

export function useCreateItem(projectId: string) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (data: ItemCreate) => api.createItem(projectId, data),
        onSuccess: () => {
            queryClient.invalidateQueries({
                queryKey: ['projects', projectId, 'items']
            });
        },
    });
}

export function useUpdateItem(projectId: string) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ itemNum, data }: { itemNum: number; data: Partial<ItemCreate> }) =>
            api.updateItem(projectId, itemNum, data),
        onSuccess: (_, { itemNum }) => {
            queryClient.invalidateQueries({
                queryKey: ['projects', projectId, 'items']
            });
            queryClient.invalidateQueries({
                queryKey: ['projects', projectId, 'items', itemNum]
            });
        },
    });
}
```

---

## Component Structure

```typescript
// components/features/items/ItemCard.tsx
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { Item } from '@/types/item';

interface ItemCardProps {
    item: Item;
    onEdit: (item: Item) => void;
}

export function ItemCard({ item, onEdit }: ItemCardProps) {
    return (
        <Card
            className="cursor-pointer hover:shadow-md transition-shadow"
            onClick={() => onEdit(item)}
        >
            <CardHeader className="flex flex-row items-center justify-between">
                <span className="font-medium">#{item.item_num}</span>
                <Badge variant={getVariantForIndicator(item.indicator)}>
                    {item.indicator}
                </Badge>
            </CardHeader>
            <CardContent>
                <h3 className="font-semibold">{item.title}</h3>
                {item.assigned_to && (
                    <p className="text-sm text-muted-foreground">
                        {item.assigned_to}
                    </p>
                )}
            </CardContent>
        </Card>
    );
}

function getVariantForIndicator(indicator: string | null): string {
    if (!indicator) return 'secondary';
    if (indicator.includes('Late') || indicator.includes('Deadline')) return 'destructive';
    if (indicator.includes('Soon')) return 'warning';
    if (indicator === 'Completed') return 'success';
    return 'secondary';
}
```

---

## Loading and Error States

```typescript
// components/features/items/ItemList.tsx
import { useItems } from '@/hooks/useItems';
import { ItemCard } from './ItemCard';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface ItemListProps {
    projectId: string;
    onEditItem: (item: Item) => void;
}

export function ItemList({ projectId, onEditItem }: ItemListProps) {
    const { data: items, isLoading, error } = useItems(projectId);

    if (isLoading) {
        return (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {[...Array(6)].map((_, i) => (
                    <Skeleton key={i} className="h-32" />
                ))}
            </div>
        );
    }

    if (error) {
        return (
            <Alert variant="destructive">
                <AlertDescription>
                    Failed to load items: {error.message}
                </AlertDescription>
            </Alert>
        );
    }

    if (!items?.length) {
        return (
            <div className="text-center py-8 text-muted-foreground">
                No items found. Create your first item to get started.
            </div>
        );
    }

    return (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {items.map(item => (
                <ItemCard
                    key={item.id}
                    item={item}
                    onEdit={onEditItem}
                />
            ))}
        </div>
    );
}
```

---

## Form with React Hook Form

```typescript
// components/features/items/EditItemDialog.tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { useCreateItem, useUpdateItem } from '@/hooks/useItems';

const itemSchema = z.object({
    type: z.enum(['Budget', 'Risk', 'Action Item', 'Issue', 'Decision', 'Deliverable', 'Plan Item']),
    title: z.string().min(1).max(500),
    description: z.string().max(10000).optional(),
    assigned_to: z.string().max(255).optional(),
});

type ItemFormData = z.infer<typeof itemSchema>;

interface EditItemDialogProps {
    projectId: string;
    item?: Item;
    open: boolean;
    onClose: () => void;
}

export function EditItemDialog({ projectId, item, open, onClose }: EditItemDialogProps) {
    const createItem = useCreateItem(projectId);
    const updateItem = useUpdateItem(projectId);

    const form = useForm<ItemFormData>({
        resolver: zodResolver(itemSchema),
        defaultValues: item ?? { type: 'Action Item', title: '' },
    });

    const onSubmit = async (data: ItemFormData) => {
        if (item) {
            await updateItem.mutateAsync({ itemNum: item.item_num, data });
        } else {
            await createItem.mutateAsync(data);
        }
        onClose();
    };

    return (
        <Dialog open={open} onOpenChange={onClose}>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>{item ? 'Edit Item' : 'Create Item'}</DialogTitle>
                </DialogHeader>
                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                    <Input
                        {...form.register('title')}
                        placeholder="Title"
                        error={form.formState.errors.title?.message}
                    />
                    <Textarea
                        {...form.register('description')}
                        placeholder="Description"
                        rows={4}
                    />
                    <Input
                        {...form.register('assigned_to')}
                        placeholder="Assigned to"
                    />
                    <div className="flex justify-end gap-2">
                        <Button type="button" variant="outline" onClick={onClose}>
                            Cancel
                        </Button>
                        <Button type="submit" loading={form.formState.isSubmitting}>
                            {item ? 'Update' : 'Create'}
                        </Button>
                    </div>
                </form>
            </DialogContent>
        </Dialog>
    );
}
```

---

## UI State with Zustand

```typescript
// stores/uiStore.ts
import { create } from 'zustand';

interface ItemFilters {
    type?: string;
    indicator?: string;
    assignee?: string;
}

interface UIState {
    sidebarOpen: boolean;
    toggleSidebar: () => void;

    itemFilters: ItemFilters;
    setItemFilters: (filters: ItemFilters) => void;
    clearItemFilters: () => void;

    editingItem: Item | null;
    setEditingItem: (item: Item | null) => void;
}

export const useUIStore = create<UIState>((set) => ({
    sidebarOpen: true,
    toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),

    itemFilters: {},
    setItemFilters: (filters) => set({ itemFilters: filters }),
    clearItemFilters: () => set({ itemFilters: {} }),

    editingItem: null,
    setEditingItem: (item) => set({ editingItem: item }),
}));
```
