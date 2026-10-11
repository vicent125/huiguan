import request from './qingqiu'

export function shengchengYuce(data) {
  return request.post('/api/olive/predict', data)
}

export function shengchengJuece(data) {
  return request.post('/api/shuifeijuece/shengcheng', data)
}

export function xiadaZhiling(data) {
  return request.post('/api/shuifeijuece/xiada', data)
}
