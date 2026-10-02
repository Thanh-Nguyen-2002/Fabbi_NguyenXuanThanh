import { useState } from "react";
import { TodoItem } from "./TodoItem";
import { TodoForm } from "./TodoForm";
import { TodoTagsDialog } from "./TodoTagsDialog";
import type { Todo, TodoFilters } from "../api/todos";
import { useDeleteTodo, useToggleTodo, useTodos, useBulkUpdateTodos } from "../api/todos";
import { useTags } from "@/features/tags/api/tags";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export function TodoList() {
  const [filters, setFilters] = useState<TodoFilters>({});
  const { data, isLoading, error } = useTodos(filters);
  const { data: tags } = useTags();

  const [editingTodo, setEditingTodo] = useState<Todo | null>(null);
  const [taggingTodoId, setTaggingTodoId] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const deleteTodo = useDeleteTodo();
  const toggleTodo = useToggleTodo();
  const bulkUpdateTodos = useBulkUpdateTodos();

  const handleToggle = (todo: Todo) => toggleTodo.mutate(todo);
  const handleEdit = (todo: Todo) => setEditingTodo(todo);
  const handleDelete = (id: string) => deleteTodo.mutate(id);

  const handleSelect = (id: string, checked: boolean) => {
    setSelectedIds(prev => 
      checked ? [...prev, id] : prev.filter(x => x !== id)
    );
  };

  const handleBulkUpdate = (completed: boolean) => {
    if (selectedIds.length === 0) return;
    bulkUpdateTodos.mutate({ ids: selectedIds, completed }, {
      onSuccess: () => setSelectedIds([])
    });
  };

  const updateFilter = (key: keyof TodoFilters, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value || undefined }));
  };

  if (error) {
    return (
      <div className="text-center py-12 text-destructive">
        Failed to load todos. Please try again.
      </div>
    );
  }

  return (
    <>
      <div className="flex flex-col gap-4 mb-4">
        {/* Filter Bar */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold text-muted-foreground">Search</label>
            <Input 
              placeholder="Keywords..." 
              value={filters.keyword || ""} 
              onChange={e => updateFilter("keyword", e.target.value)} 
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold text-muted-foreground">Status</label>
            <select 
              className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm"
              value={filters.status || ""}
              onChange={e => updateFilter("status", e.target.value)}
            >
              <option value="">All Statuses</option>
              <option value="completed">Completed</option>
              <option value="active">Active</option>
            </select>
          </div>
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold text-muted-foreground">Tag</label>
            <select 
              className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm"
              value={filters.tag_id || ""}
              onChange={e => updateFilter("tag_id", e.target.value)}
            >
              <option value="">All Tags</option>
              {tags?.map(tag => (
                <option key={tag.id} value={tag.id}>{tag.name}</option>
              ))}
            </select>
          </div>
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold text-muted-foreground">From Date</label>
            <Input 
              type="date" 
              value={filters.date_from || ""}
              onChange={e => updateFilter("date_from", e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold text-muted-foreground">To Date</label>
            <Input 
              type="date" 
              value={filters.date_to || ""}
              onChange={e => updateFilter("date_to", e.target.value)}
            />
          </div>
        </div>

        {/* Bulk Actions */}
        {selectedIds.length > 0 && (
          <div className="flex items-center gap-2 p-2 bg-muted/50 rounded-md border">
            <span className="text-sm font-medium mr-auto">{selectedIds.length} selected</span>
            <Button size="sm" variant="outline" onClick={() => handleBulkUpdate(true)} disabled={bulkUpdateTodos.isPending}>
              Mark Completed
            </Button>
            <Button size="sm" variant="outline" onClick={() => handleBulkUpdate(false)} disabled={bulkUpdateTodos.isPending}>
              Mark Active
            </Button>
          </div>
        )}
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-muted-foreground">Loading todos...</div>
      ) : !data || data.items.length === 0 ? (
        <div className="text-center py-12 text-muted-foreground">
          <p className="text-lg">No todos found</p>
          <p className="text-sm mt-1">Try adjusting your filters or create a new todo</p>
        </div>
      ) : (
        <div className="space-y-2">
          {data.items.map((todo, index) => (
            <TodoItem
              key={todo.id}
              todo={todo}
              index={index}
              isSelected={selectedIds.includes(todo.id)}
              onSelect={handleSelect}
              onToggle={handleToggle}
              onEdit={handleEdit}
              onDelete={handleDelete}
              onManageTags={(todo) => setTaggingTodoId(todo.id)}
            />
          ))}
          <div className="mt-4 text-center text-sm text-muted-foreground">
            Showing {data.items.length} of {data.total} todos
          </div>
        </div>
      )}

      {editingTodo && (
        <TodoForm
          mode="edit"
          todo={editingTodo}
          open={!!editingTodo}
          onClose={() => setEditingTodo(null)}
        />
      )}

      {taggingTodoId && (
        <TodoTagsDialog
          todo={data?.items.find(t => t.id === taggingTodoId) || null}
          open={!!taggingTodoId}
          onClose={() => setTaggingTodoId(null)}
        />
      )}
    </>
  );
}
