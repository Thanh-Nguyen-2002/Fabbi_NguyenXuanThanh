import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Checkbox } from "@/components/ui/checkbox";
import { useTags } from "../../tags/api/tags";
import { useAttachTag, useDetachTag } from "../api/todos";
import type { Todo } from "../api/todos";

interface TodoTagsDialogProps {
  todo: Todo | null;
  open: boolean;
  onClose: () => void;
}

export function TodoTagsDialog({ todo, open, onClose }: TodoTagsDialogProps) {
  const { data: allTags } = useTags();
  const attachTag = useAttachTag();
  const detachTag = useDetachTag();

  if (!todo) return null;

  const todoTagIds = new Set(todo.tags?.map(t => t.id) || []);

  const handleToggle = (tagId: string, checked: boolean) => {
    if (checked) {
      attachTag.mutate({ todoId: todo.id, tagId });
    } else {
      detachTag.mutate({ todoId: todo.id, tagId });
    }
  };

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Assign Tags to "{todo.title}"</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-4 max-h-60 overflow-y-auto">
          {allTags?.map(tag => {
            const isAttached = todoTagIds.has(tag.id);
            const isPending = attachTag.isPending || detachTag.isPending;
            return (
              <div key={tag.id} className="flex items-center space-x-3 p-2 border rounded-md hover:bg-accent/50">
                <Checkbox 
                  id={`tag-${tag.id}`} 
                  checked={isAttached} 
                  disabled={isPending}
                  onCheckedChange={(checked) => handleToggle(tag.id, checked as boolean)} 
                />
                <label 
                  htmlFor={`tag-${tag.id}`} 
                  className="flex items-center gap-2 flex-1 cursor-pointer text-sm font-medium"
                >
                  <div className="w-4 h-4 rounded-full" style={{ backgroundColor: tag.color }} />
                  {tag.name}
                </label>
              </div>
            );
          })}
          {allTags?.length === 0 && (
            <p className="text-sm text-muted-foreground text-center">No tags available. Please create some tags first.</p>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
