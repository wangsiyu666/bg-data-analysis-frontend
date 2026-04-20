const fs = require('fs')

// 解析墨刀自定义文本格式: 每行 `id type  \t {json}` 或 `@@R *\t{}`
// 提取含文字 (属性 +b/#...) 的节点，按 y 坐标分组输出
const raw = fs.readFileSync('decoded/0_7574062.json', 'utf8')

// 每个节点的"N"字段是名称，文字内容常在 '+b/#000000' 这样的键里存储为第二项
const lines = raw.split('\n')

// 墨刀将 xy/wh 做了自定义 base54 类编码，先不尝试解码精确坐标
// 先把所有文字串按出现顺序打印，按节点名分组

const results = []
for (const line of lines) {
  const tabIdx = line.indexOf('\t')
  if (tabIdx < 0) continue
  const head = line.slice(0, tabIdx).trim()
  const body = line.slice(tabIdx + 1).trim()
  if (!body.startsWith('{')) continue
  let obj
  try { obj = JSON.parse(body) } catch { continue }

  // 提取名称
  const name = obj.N || ''

  // 提取所有嵌套文本 - 墨刀格式中文字往往是数组第二个元素
  const texts = []
  function walk(v) {
    if (Array.isArray(v)) {
      if (v.length >= 2 && typeof v[1] === 'string' && v[1].length > 0 && v[1].length < 120) {
        // 典型文字数组: ["( ( ","文字内容",["style..."],[]]
        if (typeof v[0] === 'string' && v[0].includes('(')) {
          texts.push(v[1])
        }
      }
      v.forEach(walk)
    } else if (v && typeof v === 'object') {
      Object.values(v).forEach(walk)
    }
  }
  walk(obj)

  if (name || texts.length) {
    results.push({ head, name, texts, xy: obj.xy, wh: obj.wh, fill: obj.fill })
  }
}

// 输出所有非空文字
const unique = new Set()
for (const r of results) {
  const candidates = [r.name, ...r.texts].filter(Boolean)
  for (const t of candidates) {
    if (t && /[\u4e00-\u9fa5A-Za-z0-9]/.test(t) && t.length >= 2) unique.add(t)
  }
}
const sorted = Array.from(unique)
fs.writeFileSync('decoded/all_texts.txt', sorted.join('\n'), 'utf8')
console.log('节点总数:', results.length)
console.log('文字条目:', unique.size, '→ decoded/all_texts.txt')
