import request, { createApi } from './request'
import { mockSegment } from './mock/segment'

export const textToSql = createApi(
  (payload) => request.post('/segment/text-to-sql', payload),
  (payload) => mockSegment.textToSql(payload)
)

export const queryBySql = createApi(
  (payload) => request.post('/segment/query', payload),
  (payload) => mockSegment.query(payload)
)

export const saveSegment = createApi(
  (payload) => request.post('/segment/save', payload),
  (payload) => mockSegment.save(payload)
)

export const multiAnalysis = createApi(
  (payload) => request.post('/segment/multi-analysis', payload),
  (payload) => mockSegment.multiAnalysis(payload)
)

export const getSegmentList = createApi(
  () => request.get('/segment/list'),
  () => mockSegment.list()
)
