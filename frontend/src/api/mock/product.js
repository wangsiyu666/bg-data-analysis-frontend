// 产品接口 Mock 数据

const BASE_PRODUCTS = [
  {
    id: 'P5G01',
    name: '5G畅享套餐 128档',
    category: '5G套餐',
    price: '128元/月',
    scope: '全国通用',
    desc: '100GB流通+1000分钟通话+视频会员，适用于商务人群'
  },
  {
    id: 'P5G02',
    name: '5G青春套餐 68档',
    category: '5G套餐',
    price: '68元/月',
    scope: '校园/年轻用户',
    desc: '30GB定向+500分钟+音乐会员，面向大学生与 Z 世代'
  },
  {
    id: 'PEB01',
    name: '智家宽带 300M',
    category: '宽带业务',
    price: '99元/月',
    scope: '家庭用户',
    desc: '300M光纤+IPTV+WiFi6路由，提升家庭数字体验'
  },
  {
    id: 'PQY01',
    name: '视频权益包',
    category: '权益包',
    price: '19元/月',
    scope: '单独订购',
    desc: '爱奇艺/腾讯/优酷任选其一月度VIP，赠送流量定向包'
  },
  {
    id: 'PQY02',
    name: '出行权益包',
    category: '权益包',
    price: '29元/月',
    scope: '商务出差用户',
    desc: '机场VIP休息+打车券200元+机票返现'
  },
  {
    id: 'P5G03',
    name: '5G尊享套餐 298档',
    category: '5G套餐',
    price: '298元/月',
    scope: '高端商务',
    desc: '不限速300GB+3000分钟+航空里程转积分'
  },
  {
    id: 'PEB02',
    name: '融合宽带+5G 套餐',
    category: '融合套餐',
    price: '199元/月',
    scope: '家庭/融合',
    desc: '千兆宽带+2张5G副卡+IPTV+智能家居终端'
  },
  {
    id: 'PQY03',
    name: '健康权益包',
    category: '权益包',
    price: '39元/月',
    scope: '中老年用户',
    desc: '线上名医问诊+体检折扣+健康档案'
  }
]

function pick4(seed = 0) {
  const arr = [...BASE_PRODUCTS]
  for (let i = arr.length - 1; i > 0; i--) {
    const j = (seed + i * 13) % (i + 1)
    ;[arr[i], arr[j]] = [arr[j], arr[i]]
  }
  return arr.slice(0, 4)
}

export const mockProduct = {
  recommend({ text } = {}) {
    const seed = (text || '').length
    return pick4(seed)
  },
  search({ keyword } = {}) {
    const kw = (keyword || '').trim()
    if (!kw) return pick4(0)
    const matched = BASE_PRODUCTS.filter(
      (p) => p.name.includes(kw) || p.desc.includes(kw) || p.category.includes(kw)
    )
    return (matched.length ? matched : pick4(kw.length)).slice(0, 4)
  },
  recommendBySegment({ segment } = {}) {
    const seed = (segment?.name || '').length + 3
    return pick4(seed)
  }
}
