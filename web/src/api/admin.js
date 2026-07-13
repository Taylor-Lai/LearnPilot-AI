import request from './request'

export const getAdminUsers = (params) => {
  return request({
    url: '/admin/users/page',
    method: 'GET',
    params,
  })
}

export const getAdminUserDetail = (id) => {
  return request({
    url: `/admin/users/${id}`,
    method: 'GET',
  })
}

export const updateAdminUserRole = (id, isAdmin) => {
  return request({
    url: `/admin/users/${id}/role`,
    method: 'PUT',
    data: { isAdmin },
  })
}

export const deleteAdminUser = (id) => {
  return request({
    url: `/admin/users/${id}`,
    method: 'DELETE',
  })
}

export const getAdminStatistics = () => {
  return request({
    url: '/admin/statistics',
    method: 'GET',
    headers: {
      Accept: 'application/json',
    },
  })
}

export const getAdminProducerTasks = (params) => {
  return request({
    url: '/admin/producer/tasks',
    method: 'GET',
    params,
  })
}

export const getAdminProducerTaskDetail = (taskId) => {
  return request({
    url: `/admin/producer/tasks/${taskId}`,
    method: 'GET',
  })
}

export const getAdminFeedback = (params) => request({ url: '/admin/feedback', method: 'GET', params })
export const resolveAdminFeedback = (id) =>
  request({ url: `/admin/feedback/${id}/status`, method: 'PUT', data: { status: '已解决' } })
export const deleteAdminFeedback = (id) =>
  request({ url: `/admin/feedback/${id}`, method: 'DELETE' })
export const getAdminSettings = () => request({ url: '/admin/settings', method: 'GET' })
export const updateAdminSettings = (data) => request({ url: '/admin/settings', method: 'PUT', data })

// Backward-compatible aliases
export const getUserPageApi = getAdminUsers
export const getUserDetailApi = getAdminUserDetail
export const updateUserAdminRoleApi = updateAdminUserRole
export const deleteUserApi = deleteAdminUser
export const getAdminStatisticsApi = getAdminStatistics
