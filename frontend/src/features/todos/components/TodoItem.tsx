import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Pencil, Trash2, CheckCircle2, Circle, Tag, Clock } from "lucide-react";
import type { Todo } from "../api/todos";

interface TodoItemProps {
  todo: Todo;
  index: number;
  isSelected: boolean;
  onSelect: (id: string, checked: boolean) => void;
  onToggle: (todo: Todo) => void;
  onEdit: (todo: Todo) => void;
  onDelete: (id: string) => void;
  onManageTags: (todo: Todo) => void;
}

export function TodoItem({ todo, isSelected, onSelect, onToggle, onEdit, onDelete, onManageTags }: TodoItemProps) {
  return (
    <div className="flex items-center gap-3 p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors group">
      <div className="flex items-center justify-center w-6" title="Select for bulk actions">
        <Checkbox
          checked={isSelected}
          onCheckedChange={(checked) => onSelect(todo.id, checked as boolean)}
        />
      </div>
      
      <button 
        onClick={() => onToggle(todo)}
        title={todo.completed ? "Mark active" : "Mark completed"}
        className={`focus:outline-none transition-colors ${todo.completed ? "text-green-500 hover:text-green-600" : "text-muted-foreground hover:text-foreground"}`}
      >
        {todo.completed ? <CheckCircle2 className="w-5 h-5" /> : <Circle className="w-5 h-5" />}
      </button>

      <div className="flex-1 min-w-0 flex flex-col gap-1 ml-2">
        <label
          htmlFor={`todo-${todo.id}`}
          className={`text-sm font-medium cursor-pointer ${
            todo.completed ? "line-through text-muted-foreground" : ""
          }`}
        >
          {todo.title}
        </label>
        {todo.description && (
          <p className="text-xs text-muted-foreground truncate">
            {todo.description}
          </p>
        )}
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 mt-1.5">
          {todo.tags && todo.tags.length > 0 && (
            <div className="flex gap-1.5 flex-wrap">
              {todo.tags.map(tag => (
                <span
                  key={tag.id}
                  className="text-[10px] font-medium px-2 py-0.5 rounded-full text-white shadow-sm"
                  style={{ backgroundColor: tag.color }}
                >
                  {tag.name}
                </span>
              ))}
            </div>
          )}
          {todo.created_at && (
            <div className="flex items-center gap-1 text-[11px] text-muted-foreground/60 font-medium">
              <Clock className="w-3 h-3" />
              <span>
                {new Date(todo.created_at).toLocaleDateString(undefined, {
                  year: 'numeric',
                  month: 'short',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </span>
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          title="Manage Tags"
          onClick={() => onManageTags(todo)}
        >
          <Tag className="h-3.5 w-3.5" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          title="Edit Todo"
          onClick={() => onEdit(todo)}
        >
          <Pencil className="h-3.5 w-3.5" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 text-destructive hover:text-destructive"
          title="Delete Todo"
          onClick={() => onDelete(todo.id)}
        >
          <Trash2 className="h-3.5 w-3.5" />
        </Button>
      </div>
    </div>
  );
}
