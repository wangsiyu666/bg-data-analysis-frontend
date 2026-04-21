import request, { createApi } from './request'
import { mockProduct } from './mock/product'

/**
 * §3 产品推荐 + §10.2 产品列表
 */

function mapProduct(p) {
  return {
    id: p.id,
    name: p.name,
    category: p.category,
    price: p.price,
    desc: p.description || p.desc || '',
    scope: p.applicable_scope || p.scope || ''
  }
}

// 3.1 基于文本推荐 POST /product/recommend_by_text -> { products: [...] }
export const recommendProducts = createApi(
  async ({ text } = {}) => {
    const data = await request.post('/product/recommend_by_text', {
      user_input: text || ''
    })
    return (data.products || []).map(mapProduct)
  },
  (payload) => mockProduct.recommend(payload)
)

// 3.2 基于客群推荐 POST /product/recommend_by_audience （仅客群运营页）
export const recommendBySegment = createApi(
  async ({ segment = {}, audienceIds = [], text = '' } = {}) => {
    const ids = audienceIds && audienceIds.length ? audienceIds : segment.audienceIds || []
    const data = await request.post('/product/recommend_by_audience', {
      audience_ids: ids,
      user_input: text || segment.goal || '希望提升ARPU'
    })
    return (data.products || []).map(mapProduct)
  },
  (payload) => mockProduct.recommendBySegment(payload)
)

// 10.2 产品列表 GET /products -> { products: [] }
//   前端"搜索"在列表上做本地 keyword 过滤
let _productCache = null
async function loadProducts() {
  if (_productCache) return _productCache
  const data = await request.get('/products')
  _productCache = (data.products || []).map(mapProduct)
  return _productCache
}

export const searchProducts = createApi(
  async ({ keyword } = {}) => {
    const all = await loadProducts()
    const kw = (keyword || '').trim().toLowerCase()
    if (!kw) return all
    return all.filter((p) =>
      [p.name, p.category, p.desc, p.scope].filter(Boolean).some((v) => String(v).toLowerCase().includes(kw))
    )
  },
  (payload) => mockProduct.search(payload)
)
