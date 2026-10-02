import { z } from "zod";
import type { Tag } from "../../tags/api/tags";

export const todoSchema = z.object({
  title: z.string().min(1, "Title is required").max(200, "Title is too long"),
  description: z.string().optional(),
  tags: z.array(z.any()).optional(), // Assuming we want it in the schema, but as an interface type below
});

export type TodoFormData = z.infer<typeof todoSchema> & { tags?: Tag[] };
