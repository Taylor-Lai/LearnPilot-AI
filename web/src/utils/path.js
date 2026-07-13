function normalizeResourceItem(item, index, groupIndex) {
  return {
    id: item.id || item.resource_id || `resource-${groupIndex + 1}-${index + 1}`,
    title: item.title || item.name || '未命名资源',
    meta: item.meta || item.subtitle || item.type || item.resource_type || '',
    description: item.description || item.summary || '',
    source: item.source || '',
    url: item.url || item.link || item.detail_url || '',
  }
}

const PATH_STATUS_LABELS = {
  not_started: '未开始',
  in_progress: '进行中',
  completed: '已完成',
  active: '学习中',
  deleted: '已删除',
}

export function normalizePathStatus(status) {
  const normalized = status === 'pending' || !status ? 'not_started' : String(status)
  return {
    value: normalized,
    label: PATH_STATUS_LABELS[normalized] || normalized,
  }
}

export function adaptPathListResponse(raw = {}) {
  const data = raw?.data || raw || {}
  const items = Array.isArray(data.items) ? data.items : []

  return {
    total: Number(data.total) || items.length,
    items: items.map((item) => ({
      pathId: String(item.pathId ?? item.path_id ?? ''),
      title: item.title || '未命名路径',
      goal: item.goal || '',
      course: item.course || '',
      progress: Number(item.progress) || 0,
      status: item.status || 'active',
      statusLabel: normalizePathStatus(item.status || 'active').label,
      createdAt: item.created_at || item.createdAt || '',
    })),
  }
}

export function adaptPathProgressResponse(raw = {}) {
  const data = raw?.data || raw || {}
  const current = data.current_node || data.currentNode || null

  return {
    pathId: String(data.pathId ?? data.path_id ?? ''),
    totalNodes: Number(data.total_nodes ?? data.totalNodes) || 0,
    completedNodes: Number(data.completed_nodes ?? data.completedNodes) || 0,
    progress: Number(data.progress) || 0,
    currentNode: current
      ? {
          id: String(current.id ?? current.nodeId ?? current.node_id ?? ''),
          nodeId: String(current.nodeId ?? current.id ?? current.node_id ?? ''),
          title: current.title || '',
        }
      : null,
  }
}

/**
 * 将后端 path 响应（nodes/edges）适配为学习路径页面展示结构。
 */
export function adaptPathResponse(raw = {}) {
  const data = raw?.data || raw || {}
  const nodes = Array.isArray(data.nodes) ? data.nodes : []

  const steps = nodes.map((node, index) => {
    const stepOrder = node.step_order ?? index + 1
    const minutes = Number(node.estimated_minutes) || 0

    return {
      id: node.id || node.nodeId || node.node_id || `step-${index + 1}`,
      period: node.level ? `第${stepOrder}步 · ${node.level}` : `第${stepOrder}步`,
      duration: minutes > 0 ? `${minutes}分钟` : '',
      title: node.title || node.name || `步骤${stepOrder}`,
      short: node.objective || node.description || '',
      description: node.description || node.objective || node.content || '',
      tags: [node.level, node.status].filter(Boolean),
      status: normalizePathStatus(node.status || 'not_started').value,
      statusLabel: normalizePathStatus(node.status || 'not_started').label,
      stepResources: Array.isArray(node.resources) ? node.resources : [],
    }
  })

  const totalMinutes = nodes.reduce(
    (sum, node) => sum + (Number(node.estimated_minutes) || 0),
    0,
  )

  let duration = ''
  if (totalMinutes > 0) {
    duration =
      totalMinutes >= 60
        ? `约${Math.round((totalMinutes / 60) * 10) / 10}小时`
        : `约${totalMinutes}分钟`
  }

  const title = data.title || ''
  const goal = data.goal || ''
  const summary = goal ? `${title ? `${title}：` : ''}${goal}` : title

  const resources = []
  steps.forEach((step, index) => {
    if (!step.stepResources.length) return
    resources.push({
      type: step.title || `阶段${index + 1}`,
      desc: step.short || step.description || '',
      items: step.stepResources.map((item, itemIndex) =>
        normalizeResourceItem(item, itemIndex, index),
      ),
    })
  })

  return {
    pathId: data.pathId || data.path_id || '',
    title,
    summary,
    duration,
    steps,
    resources,
  }
}
