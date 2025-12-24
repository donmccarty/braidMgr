import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Utility for merging Tailwind classes with proper precedence.
 *
 * Combines clsx for conditional classes with tailwind-merge for
 * deduplication and proper class precedence.
 *
 * Usage:
 *   cn("px-4 py-2", condition && "bg-blue-500", "px-6")
 *   // Returns "py-2 px-6" (px-6 wins over px-4)
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
