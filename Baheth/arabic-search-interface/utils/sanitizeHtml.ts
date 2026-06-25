import DOMPurify from "isomorphic-dompurify";

export function sanitizeHtml(rawHtml: string): string {
  return DOMPurify.sanitize(rawHtml, {
    ALLOWED_TAGS: ["p", "span", "strong", "em", "matn", "br", "div", "b", "i"],
    ALLOWED_ATTR: ["class", "id", "dir"],
  });
}
