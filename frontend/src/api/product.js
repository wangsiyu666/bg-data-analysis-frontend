import request, { createApi } from './request'
import { mockProduct } from './mock/product'

export const recommendProducts = createApi(
  (payload) => request.post('/product/recommend', payload),
  (payload) => mockProduct.recommend(payload)
)

export const searchProducts = createApi(
  (payload) => request.post('/product/search', payload),
  (payload) => mockProduct.search(payload)
)

export const recommendBySegment = createApi(
  (payload) => request.post('/product/recommend-by-segment', payload),
  (payload) => mockProduct.recommendBySegment(payload)
)
