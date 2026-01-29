/**
 * Simple markdown-to-HTML renderer for LLM output text.
 * Handles headers, bold, inline code, bullet lists, and paragraph breaks.
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

    // Headers: # H1, ## H2, ### H3
    const headerMatch = trimmed.match(/^(#{1,3})\s+(.+)$/)
    if (headerMatch) {
      if (inList) { result.push('</ul>'); inList = false }
      const level = headerMatch[1].length
      result.push(`<h${level + 1}>${applyInline(headerMatch[2])}</h${level + 1}>`)
      continue
    }

    // Bullet lists
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
        // skip consecutive empty lines
      } else {
        result.push(`<p>${applyInline(trimmed)}</p>`)
      }
    }
  }

  if (inList) result.push('</ul>')

  return result.join('')
}

function applyInline(text: string): string {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
}
