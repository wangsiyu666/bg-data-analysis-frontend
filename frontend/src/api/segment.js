import request, { createApi } from './request'
import { mockSegment } from './mock/segment'

/**
 * 页面2：客群分析
 * 文档章节 1 + 辅助接口 10
 */

// 1.1 自然语言生成 SQL（不执行）
//   POST /audience/nl2sql   { question, user_id }  ->  { sql }
export const textToSql = createApi(
  async ({ text } = {}) => {
    const data = await request.post('/audience/nl2sql', { question: text })
    return { sql: data.sql }
  },
  (payload) => mockSegment.textToSql(payload)
)

// 1.2 执行 SQL 查询
//   POST /audience/execute  { sql, user_id }
//   ->  { columns: string[], data: any[][], total }
// 前端表格用的是 [{prop,label}] + [{prop:value}] 格式，需要转换
export const queryBySql = createApi(
  async ({ sql } = {}) => {
    const data = await request.post('/audience/execute', { sql })
    const cols = (data.columns || []).map((c) => ({ prop: c, label: c }))
    const rows = (data.data || []).map((r) => {
      const obj = {}
      ;(data.columns || []).forEach((c, idx) => (obj[c] = r[idx]))
      return obj
    })
    return { columns: cols, rows, total: data.total ?? rows.length, sql }
  },
  (payload) => mockSegment.query(payload)
)

// 1.3 保存客群
//   POST /audience/save { name, condition_sql, user_id } -> { status, audience_id }
export const saveSegment = createApi(
  async ({ name, condition } = {}) => {
    const data = await request.post('/audience/save', {
      name,
      condition_sql: condition
    })
    if (data.status === 'error') {
      throw new Error(data.message || '保存失败')
    }
    return { id: data.audience_id, name, condition }
  },
  (payload) => mockSegment.save(payload)
)

// 1.4 多维分析 —— 通过多次 /audience/execute 实现（文档示例里也是前端直接写 SQL）
// 入参 { sql } 为当前客群基础 SQL（含 FROM ... WHERE ...）
function extractFromWhere(sql) {
  const s = (sql || '').replace(/;+\s*$/, '')
  const m = s.match(/(FROM[\s\S]*?)(group\s+by|order\s+by|limit|$)/i)
  return m ? m[1].trim() : 'FROM user_behavior'
}

export const multiAnalysis = createApi(
  async ({ sql } = {}) => {
    const fromWhere = extractFromWhere(sql)

    // 1) 生命周期卡片
    const sqlLifecycle = `SELECT
      countIf(user_online < 6) AS s1,
      countIf(user_online >= 6 AND user_online < 18) AS s2,
      countIf(user_online >= 18 AND user_online < 36) AS s3,
      countIf(user_online >= 36 AND user_online < 60) AS s4,
      countIf(user_online >= 60) AS s5
      ${fromWhere}`

    // 2) 高/低价值按生命周期阶段
    const sqlValue = `SELECT
      CASE
        WHEN user_online < 6 THEN '入网期'
        WHEN user_online >= 6 AND user_online < 18 THEN '成长期'
        WHEN user_online >= 18 AND user_online < 36 THEN '成熟期'
        WHEN user_online >= 36 AND user_online < 60 THEN '异动期'
        ELSE '离网期'
      END AS stage,
      countIf(arpu > 80) AS high,
      countIf(arpu <= 80) AS low
      ${fromWhere}
      GROUP BY stage`

    // 3) 雷达 6 维
    const sqlRadar = `SELECT
      sum(is_rhtc) AS 粘性,
      avg(arpu) AS 价值,
      sum(is_ywsk) AS 竞抢,
      sum(is_ts) AS 感知,
      sum(active_mark) AS 活跃,
      avg(call_opp_counts1) AS 传播
      ${fromWhere}`

    const [lcRes, vRes, rRes] = await Promise.all([
      request.post('/audience/execute', { sql: sqlLifecycle }),
      request.post('/audience/execute', { sql: sqlValue }),
      request.post('/audience/execute', { sql: sqlRadar })
    ])

    // 组装生命周期
    const lcRow = (lcRes.data && lcRes.data[0]) || []
    const toWan = (n) => (typeof n === 'number' ? +(n / 10000).toFixed(2) : 0)
    const lifecycle = [
      { key: 'inflow', label: '入网期', desc: '在网时长<6个月', value: toWan(lcRow[0]) },
      { key: 'growth', label: '成长期', desc: '在网时长<18个月', value: toWan(lcRow[1]) },
      { key: 'mature', label: '成熟期', desc: '在网时长<36个月', value: toWan(lcRow[2]) },
      { key: 'churn', label: '异动期', desc: '在网时长<60个月', value: toWan(lcRow[3]) },
      { key: 'leave', label: '离网期', desc: '在网时长>60个月', value: toWan(lcRow[4]) }
    ]

    // 组装高低价值
    const stageOrder = ['入网期', '成长期', '成熟期', '异动期', '离网期']
    const valueMap = {}
    ;(vRes.data || []).forEach((row) => {
      const stage = row[0]
      valueMap[stage] = { high: row[1] || 0, low: row[2] || 0 }
    })
    const valueBar = {
      categories: stageOrder,
      high: stageOrder.map((s) => valueMap[s]?.high || 0),
      low: stageOrder.map((s) => valueMap[s]?.low || 0)
    }

    // 组装雷达
    const rRow = (rRes.data && rRes.data[0]) || []
    const radar = {
      indicator: [
        { name: '粘性', max: 100 },
        { name: '价值', max: 100 },
        { name: '竞抢', max: 100 },
        { name: '感知', max: 100 },
        { name: '活跃', max: 100 },
        { name: '传播', max: 100 }
      ],
      value: rRow.map((v) => Number(v) || 0)
    }

    // 诊断表格：按阶段 * 6 维，当前后端没有直接接口，沿用雷达总值做示意
    const diagnosisTable = stageOrder.map((stage) => ({
      period: stage,
      sticky: Math.round((rRow[0] || 0) * 0.9),
      value: Math.round((rRow[1] || 0) * 0.9),
      compete: Math.round((rRow[2] || 0) * 0.9),
      sense: Math.round((rRow[3] || 0) * 0.9),
      active: Math.round((rRow[4] || 0) * 0.9),
      spread: Math.round((rRow[5] || 0) * 0.9)
    }))

    return { lifecycle, valueBar, radar, diagnosisTable, sql }
  },
  (payload) => mockSegment.multiAnalysis(payload)
)

// 1.5 已保存客群列表（前端为了方便，走 /strategies 不合适；后端没有直接客群列表接口，
// 由前端在 saveSegment 后维护 Pinia 的 savedSegments 即可；这里保留给 UI 首次加载用）
export const getSegmentList = createApi(
  async () => {
    // 目前后端没有独立的客群列表接口，返回空数组由前端自己维护
    return []
  },
  () => mockSegment.list()
)

// 10.1 获取 ClickHouse 可用字段
//   GET /clickhouse/fields -> { fields: [] }
export const getClickhouseFields = createApi(
  async () => {
    const data = await request.get('/clickhouse/fields')
    return data.fields || []
  },
  () => ['user_id', 'arpu', 'city_id', 'age', 'dou', 'user_online']
)
