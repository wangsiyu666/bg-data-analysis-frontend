import request, { createApi } from './request'
import { mockStrategy } from './mock/strategy'

export const segmentByCondition = createApi(
  (payload) => request.post('/segment/by-condition', payload),
  (payload) => mockStrategy.segmentByCondition(payload)
)

export const seedExpand = createApi(
  (payload) => request.post('/segment/seed-expand', payload),
  (payload) => mockStrategy.seedExpand(payload)
)

export const segmentByProduct = createApi(
  (payload) => request.post('/segment/by-product', payload),
  (payload) => mockStrategy.segmentByProduct(payload)
)

export const uploadUsers = createApi(
  (formData) =>
    request.post('/segment/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),
  () => mockStrategy.uploadUsers()
)

export const generateStrategy = createApi(
  (payload) => request.post('/strategy/generate', payload),
  (payload) => mockStrategy.generate(payload)
)

export const executeStrategy = createApi(
  (payload) => request.post('/strategy/execute', payload),
  (payload) => mockStrategy.execute(payload)
)

export const predictStrategy = createApi(
  (payload) => request.post('/strategy/predict', payload),
  (payload) => mockStrategy.predict(payload)
)

export const publishStrategy = createApi(
  (payload) => request.post('/strategy/publish', payload),
  (payload) => mockStrategy.publish(payload)
)
