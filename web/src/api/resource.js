import request from '../api/request'

export function getResourceList(params = {}) {
  return request({
    url: '/resources',
    method: 'GET',
    params
  })
}

export function getResourceDetail(id) {
  return request({
    url: `/resources/${id}`,
    method: 'GET'
  })
}

export function viewResource(id) {
  return request({
    url: `/resources/${id}/view`,
    method: 'POST'
  })
}

export function likeResource(id) {
  return request({
    url: `/resources/${id}/like`,
    method: 'POST'
  })
}

export default {
  getResourceList,
  getResourceDetail,
  viewResource,
  likeResource
}