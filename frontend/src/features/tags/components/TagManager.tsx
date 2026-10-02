import { useState } from "react";
import { useTags, useCreateTag, useUpdateTag, useDeleteTag } from "../api/tags";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Trash2, Edit2 } from "lucide-react";

export function TagManager({ open, onOpenChange }: { open: boolean; onOpenChange: (open: boolean) => void }) {
  const { data: tags } = useTags();
  const createTag = useCreateTag();
  const updateTag = useUpdateTag();
  const deleteTag = useDeleteTag();

  const [editingId, setEditingId] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [color, setColor] = useState("#000000");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (editingId) {
      updateTag.mutate({ id: editingId, data: { name, color } }, {
        onSuccess: () => resetForm()
      });
    } else {
      createTag.mutate({ name, color }, {
        onSuccess: () => resetForm()
      });
    }
  };

  const resetForm = () => {
    setEditingId(null);
    setName("");
    setColor("#000000");
  };

  return (
    <Dialog open={open} onOpenChange={(val) => {
      onOpenChange(val);
      if (!val) resetForm();
    }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Manage Tags</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <form onSubmit={handleSubmit} className="flex gap-2 items-end">
            <div className="flex-1 space-y-1">
              <Label>Name</Label>
              <Input value={name} onChange={e => setName(e.target.value)} required />
            </div>
            <div className="w-16 space-y-1">
              <Label>Color</Label>
              <Input type="color" value={color} onChange={e => setColor(e.target.value)} className="p-1 h-9" />
            </div>
            <Button type="submit" disabled={createTag.isPending || updateTag.isPending}>
              {editingId ? "Save" : "Add"}
            </Button>
            {editingId && (
              <Button type="button" variant="outline" onClick={resetForm}>Cancel</Button>
            )}
          </form>

          <div className="space-y-2 mt-4 max-h-60 overflow-y-auto">
            {tags?.map(tag => (
              <div key={tag.id} className="flex items-center justify-between p-2 border rounded-md">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded-full" style={{ backgroundColor: tag.color }} />
                  <span className="text-sm font-medium">{tag.name}</span>
                </div>
                <div className="flex gap-1">
                  <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => {
                    setEditingId(tag.id);
                    setName(tag.name);
                    setColor(tag.color);
                  }}>
                    <Edit2 className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive" onClick={() => deleteTag.mutate(tag.id)}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
            {tags?.length === 0 && (
              <div className="text-sm text-muted-foreground text-center py-4">No tags created yet.</div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
