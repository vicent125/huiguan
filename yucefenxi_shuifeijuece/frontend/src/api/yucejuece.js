import request from './qingqiu'

export function shengchengYuce(data) {
  return request.post('/api/yucefenxi/shengcheng', data)
}

export function shengchengJuece(data) {
  return request.post('/api/shuifeijuece/shengcheng', data)
}

export function xiadaZhiling(data) {
  return request.post('/api/shuifeijuece/xiada', data)
}