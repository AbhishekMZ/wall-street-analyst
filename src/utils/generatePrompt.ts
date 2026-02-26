import type { PromptTemplate } from '../data/prompts';

export function generatePrompt(
  template: PromptTemplate,
  fieldValues: Record<string, string>
): string {
  const lines: string[] = [];

  lines.push(template.role);
  lines.push('');
  lines.push(template.task);
  lines.push('');
  lines.push(template.action);
  lines.push('');

  for (const item of template.items) {
    lines.push(`- ${item}`);
  }

  lines.push('');
  lines.push(template.format);
  lines.push('');

  for (const field of template.fields) {
    const value = fieldValues[field.id]?.trim();
    if (value) {
      lines.push(`${field.label}: ${value}`);
    } else {
      lines.push(`${field.label}: [${field.placeholder.toUpperCase()}]`);
    }
  }

  return lines.join('\n');
}
