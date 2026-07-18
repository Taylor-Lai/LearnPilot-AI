import { marked } from 'marked'

marked.setOptions({ breaks: true, gfm: true })

export function sanitizeHtml(html) {
  if (!html) return ''
  return String(html)
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    .replace(/<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>/gi, '')
    .replace(/<object\b[^<]*(?:(?!<\/object>)<[^<]*)*<\/object>/gi, '')
    .replace(/\son\w+\s*=\s*["'][^"']*["']/gi, '')
    .replace(/\son\w+\s*=\s*[^\s>]+/gi, '')
    .replace(/javascript:/gi, '')
}

export function renderMarkdown(value) {
  const content = normalizeDisplayContent(value)
  if (!content) return ''
  try {
    return sanitizeHtml(marked.parse(content))
  } catch {
    return sanitizeHtml(`<p>${escapeHtml(content)}</p>`)
  }
}

export function normalizeDisplayContent(value) {
  if (value == null) return ''
  if (Array.isArray(value)) return formatStructuredItems(value)
  if (typeof value === 'object') return formatStructuredItems(value.questions || value.items || [value])

  const text = String(value).trim()
  if (!text) return ''
  if (text.startsWith('[') || text.startsWith('{')) {
    try {
      const parsed = JSON.parse(text)
      return normalizeDisplayContent(parsed)
    } catch {
      // Old tasks may contain Python-repr strings produced before the typed contract.
      const prompts = [...text.matchAll(/['"]question['"]\s*:\s*['"]([^'"]{4,})['"]/g)]
        .map(match => match[1].replace(/\\n/g, '\n'))
      if (prompts.length) return prompts.map((item, index) => `${index + 1}. ${item}`).join('\n')
      return '这部分内容来自旧版任务，结构无法安全解析。请重新生成资源以获得完整内容。'
    }
  }
  return text
}

function formatStructuredItems(items) {
  if (!Array.isArray(items)) return String(items || '')
  return items
    .map((item, index) => {
      if (typeof item === 'string') return `${index + 1}. ${item}`
      const prompt = item?.question || item?.prompt || item?.title || item?.content
      return prompt ? `${index + 1}. ${prompt}` : ''
    })
    .filter(Boolean)
    .join('\n')
}

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;')
}
