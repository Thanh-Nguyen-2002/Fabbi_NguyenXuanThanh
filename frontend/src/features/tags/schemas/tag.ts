import { z } from "zod";

export const tagSchema = z.object({
  name: z.string().min(1, "Name is required").max(50, "Name is too long"),
  color: z.string().regex(/^#[0-9A-F]{6}$/i, "Invalid hex color"),
});

export type TagFormData = z.infer<typeof tagSchema>;
