/**
 * Simple markdown-to-HTML renderer for LLM output text.
 * Handles bold, bullet lists, and paragraph breaks.
 */
export function renderMarkdown(text: string): string {
  if (!text) return ''

  const escaped = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  const lines = escaped.split('\n')
  const result: string[] = []
  let inList = false

  for (const line of lines) {
    const trimmed = line.trim()

    if (/^[-*]\s+/.test(trimmed)) {
      if (!inList) {
        result.push('<ul>')
        inList = true
      }
      const content = trimmed.replace(/^[-*]\s+/, '')
      result.push(`<li>${applyInline(content)}</li>`)
    } else {
      if (inList) {
        result.push('</ul>')
        inList = false
      }
      if (trimmed === '') {
        result.push('<br>')
      } else {
        result.push(`<p>${applyInline(trimmed)}</p>`)
      }
    }
  }

  if (inList) result.push('</ul>')

  return result.join('')
}

function applyInline(text: string): string {
  return text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
}
