<template>
  <div class="segment-page">
    <div class="seg-grid">
      <!-- 左侧：助手 + SQL + 表格 -->
      <div class="left-pane">
        <!-- 大蓝色助手卡 -->
        <div class="assistant-card">
          <div class="ac-head">
            <div class="ac-avatar">
              <svg viewBox="0 0 20 20" width="20" height="20" fill="#fff">
                <circle cx="10" cy="7" r="3" /><path d="M3 18c0-3 3-5 7-5s7 2 7 5" />
              </svg>
            </div>
            <div class="ac-title">你好！我是客群分析小助手</div>
          </div>

          <div class="ac-body">
            <!-- 输入框 1 -->
            <div class="ac-box">
              <textarea
                v-model="askText"
                rows="2"
                placeholder="向小助手提问客群分析问题，例如分析ARPU>89客群"
              />
              <button class="orange-btn" :disabled="askLoading" @click="handleAskAnalyze">
                {{ askLoading ? '生成中...' : '开始分析' }}
              </button>
            </div>

            <!-- 查询语句 -->
            <div class="ac-label">查询语句</div>
            <div class="ac-box sql-box">
              <textarea v-model="sqlText" rows="3" spellcheck="false" />
              <button class="orange-btn" :disabled="queryLoading" @click="handleQuery">
                {{ queryLoading ? '查询中...' : '统计数据' }}
              </button>
            </div>
          </div>
        </div>

        <!-- 结果表格 -->
        <div class="result-card">
          <el-table
            v-loading="queryLoading"
            :data="pagedRows"
            stripe
            border
            size="small"
            max-height="320"
            @row-click="handleRowClick"
            :row-class-name="rowClassName"
          >
            <el-table-column
              v-for="col in tableColumns"
              :key="col.prop"
              :prop="col.prop"
              :label="col.label"
              sortable
            />
          </el-table>
          <div class="table-footer">
            <span>共 {{ totalRows }}</span>
            <el-pagination
              background
              layout="prev, pager, next"
              :total="totalRows"
              :page-size="pageSize"
              :current-page="currentPage"
              @current-change="(p) => (currentPage = p)"
              small
            />
          </div>

          <div class="result-actions">
            <button class="blue-btn" @click="handleSaveSegment">保存客群</button>
            <button class="orange-btn" :disabled="analysisLoading" @click="handleMultiAnalysis">
              {{ analysisLoading ? '分析中...' : '多维分析' }}
            </button>
          </div>
        </div>
      </div>

      <!-- 右侧：生命周期 + 高低价值 + 诊断 -->
      <div class="right-pane">
        <!-- 5 生命周期卡片 -->
        <div class="lifecycle-row">
          <div v-for="lc in analysis.lifecycle" :key="lc.key" class="lc-card">
            <div class="lc-head">{{ lc.label }}</div>
            <div class="lc-value">
              <CountNumber :end="lc.value" :decimals="2" />
              <span class="lc-unit">W</span>
            </div>
            <div class="lc-desc">口径：{{ lc.desc }}</div>
          </div>
        </div>

        <!-- 高价值 / 低价值 -->
        <div class="value-card">
          <div class="vc-grid">
            <div class="vc-col">
              <div class="vc-title">高价值用户</div>
              <div v-for="(item, i) in highLowData.high" :key="'h' + i" class="vc-row">
                <span class="vc-num">{{ item.value }}</span>
                <div class="vc-bar">
                  <div class="vc-bar-fill hi" :style="{ width: item.percent + '%' }"></div>
                </div>
                <span class="vc-label">{{ item.name }}</span>
              </div>
            </div>
            <div class="vc-col">
              <div class="vc-title">低价值</div>
              <div v-for="(item, i) in highLowData.low" :key="'l' + i" class="vc-row right">
                <span class="vc-label">{{ item.name }}</span>
                <div class="vc-bar">
                  <div class="vc-bar-fill lo" :style="{ width: item.percent + '%' }"></div>
                </div>
                <span class="vc-num">{{ item.value }}</span>
              </div>
            </div>
          </div>
          <div class="vc-footer">
            <div class="vc-footer-title">全生命周期分布</div>
            <div class="vc-footer-sub">全生命周期内使用户价值曲线和差异性运营的直接指标</div>
          </div>
        </div>

        <!-- 客群诊断 -->
        <div class="diag-card">
          <div class="diag-label">客群诊断</div>
          <div class="diag-body">
            <EChart :option="radarOption" height="260px" />
            <el-table :data="analysis.diagnosisTable" size="small" border style="flex:1">
              <el-table-column prop="period" label="" width="72" />
              <el-table-column prop="sticky" label="粘性" />
              <el-table-column prop="value" label="价值" />
              <el-table-column prop="compete" label="竞抢" />
              <el-table-column prop="sense" label="感知" />
              <el-table-column prop="active" label="活跃" />
              <el-table-column prop="spread" label="传播" />
            </el-table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import CountNumber from '@/components/CountNumber.vue'
import EChart from '@/components/EChart.vue'
import { textToSql, queryBySql, saveSegment, multiAnalysis, getSegmentList } from '@/api/segment'
import { useSegmentStore } from '@/stores/segment'

const store = useSegmentStore()

const askText = ref('分析 ARPU>89 的客群')
const sqlText = ref('select city_id,user_online,sex_id,count(*) from *** where arpu>80;')
const askLoading = ref(false)
const queryLoading = ref(false)
const analysisLoading = ref(false)

const tableColumns = ref([])
const allRows = ref([])
const totalRows = ref(0)
const currentPage = ref(1)
const pageSize = 10
const selectedRowIdx = ref(new Set())

const analysis = reactive({
  lifecycle: [
    { key: 'inflow', label: '入网期', desc: '在网时长<6个月', value: 0 },
    { key: 'growth', label: '成长期', desc: '在网时长<18个月', value: 0 },
    { key: 'mature', label: '成熟期', desc: '在网时长<36个月', value: 0 },
    { key: 'churn', label: '异动期', desc: '在网时长<60个月', value: 0 },
    { key: 'leave', label: '离网期', desc: '沉默、状态非100等', value: 0 }
  ],
  valueBar: { categories: [], high: [], low: [] },
  radar: { indicator: [], value: [] },
  diagnosisTable: []
})

// 将 valueBar 数据转成左右两列横条图
const highLowData = computed(() => {
  const cats = analysis.valueBar.categories || []
  const highArr = analysis.valueBar.high || []
  const lowArr = analysis.valueBar.low || []
  const maxH = Math.max(1, ...highArr)
  const maxL = Math.max(1, ...lowArr)
  return {
    high: cats.map((c, i) => ({
      name: c,
      value: highArr[i] ?? 0,
      percent: ((highArr[i] ?? 0) / maxH) * 100
    })),
    low: cats.map((c, i) => ({
      name: c,
      value: lowArr[i] ?? 0,
      percent: ((lowArr[i] ?? 0) / maxL) * 100
    }))
  }
})

const pagedRows = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return allRows.value.slice(start, start + pageSize)
})

const radarOption = computed(() => ({
  tooltip: {},
  radar: {
    indicator: analysis.radar.indicator || [],
    splitNumber: 4,
    radius: '65%',
    axisName: { color: '#303133', fontSize: 12, fontWeight: 600 },
    splitLine: { lineStyle: { color: '#dce3ef' } },
    splitArea: { show: false }
  },
  series: [
    {
      type: 'radar',
      areaStyle: { color: 'rgba(30,110,207,0.18)' },
      lineStyle: { color: '#1e6ecf', width: 2 },
      itemStyle: { color: '#1e6ecf' },
      symbolSize: 5,
      data: analysis.radar.value && analysis.radar.value.length ? [{ value: analysis.radar.value, name: '客群诊断' }] : []
    }
  ]
}))

function rowClassName({ rowIndex }) {
  return selectedRowIdx.value.has(rowIndex) ? 'row-selected' : ''
}

function handleRowClick(_row, _col, event) {
  const rowIdx = (currentPage.value - 1) * pageSize + pagedRows.value.indexOf(_row)
  if (event?.ctrlKey || event?.metaKey) {
    if (selectedRowIdx.value.has(rowIdx)) selectedRowIdx.value.delete(rowIdx)
    else selectedRowIdx.value.add(rowIdx)
  } else {
    selectedRowIdx.value = new Set([rowIdx])
  }
}

async function handleAskAnalyze() {
  if (!askText.value.trim()) {
    ElMessage.warning('请输入分析需求')
    return
  }
  askLoading.value = true
  try {
    const res = await textToSql({ text: askText.value })
    sqlText.value = res.sql
    ElMessage.success('SQL 已生成')
  } finally {
    askLoading.value = false
  }
}

async function handleQuery() {
  if (!sqlText.value.trim()) {
    ElMessage.warning('请输入 SQL')
    return
  }
  queryLoading.value = true
  try {
    const res = await queryBySql({ sql: sqlText.value })
    tableColumns.value = res.columns
    allRows.value = res.rows
    totalRows.value = res.total || res.rows.length
    currentPage.value = 1
    selectedRowIdx.value = new Set()
  } finally {
    queryLoading.value = false
  }
}

async function handleSaveSegment() {
  try {
    const { value: name } = await ElMessageBox.prompt('请输入客群名称', '保存客群', {
      confirmButtonText: '保存',
      cancelButtonText: '取消',
      inputPattern: /.+/,
      inputErrorMessage: '客群名称不能为空'
    })
    const fromMatch = sqlText.value.match(/(FROM[\s\S]*?)(?:group by|order by|limit|;|$)/i)
    const condition = fromMatch ? fromMatch[1].trim() : sqlText.value
    const res = await saveSegment({ name, condition })
    store.addSegment({ name, condition, id: res.id })
    ElMessage.success('客群已保存')
  } catch (e) {
    if (e !== 'cancel') console.warn(e)
  }
}

async function handleMultiAnalysis() {
  analysisLoading.value = true
  try {
    const res = await multiAnalysis({ sql: sqlText.value })
    analysis.lifecycle = res.lifecycle
    analysis.valueBar = res.valueBar
    analysis.radar = res.radar
    analysis.diagnosisTable = res.diagnosisTable
    ElMessage.success('多维分析已更新右侧数据')
  } finally {
    analysisLoading.value = false
  }
}

onMounted(async () => {
  try {
    const list = await getSegmentList()
    store.setList(list)
  } catch (e) {}
  handleQuery()
  handleMultiAnalysis()
})
</script>

<style lang="scss" scoped>
.segment-page {
  padding-bottom: 30px;
}
.seg-grid {
  display: grid;
  grid-template-columns: minmax(520px, 1.1fr) minmax(540px, 1fr);
  gap: 14px;
}
.left-pane,
.right-pane {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* 助手卡 */
.assistant-card {
  background: #e9f1fb;
  border-radius: 10px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}
.ac-head {
  background: #1e6ecf;
  color: #fff;
  padding: 10px 16px;
  display: flex;
  align-items: center;
  gap: 10px;
}
.ac-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.22);
  display: flex;
  align-items: center;
  justify-content: center;
}
.ac-title {
  font-weight: 700;
  font-size: 15px;
}
.ac-body {
  padding: 14px 16px 18px;
}
.ac-box {
  position: relative;
  background: #b6d2ef;
  border-radius: 8px;
  padding: 10px 12px 44px;
  margin-bottom: 12px;
  textarea {
    width: 100%;
    background: transparent;
    border: none;
    outline: none;
    resize: none;
    font-size: 13px;
    color: #103a70;
    font-family: Consolas, Menlo, monospace;
    &::placeholder {
      color: #5a7ea8;
    }
  }
  &.sql-box textarea {
    color: #0a2e60;
    font-family: Consolas, Menlo, monospace;
  }
}
.ac-label {
  font-size: 13px;
  color: #606266;
  margin: 4px 0 6px;
}
.orange-btn {
  position: absolute;
  right: 10px;
  bottom: 10px;
  background: #1e6ecf;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 6px 18px;
  font-size: 13px;
  cursor: pointer;
  font-weight: 600;
  box-shadow: 0 2px 6px rgba(30, 110, 207, 0.3);
  transition: all 0.2s;
  &:hover:not(:disabled) {
    background: #1857a8;
  }
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
}

/* 结果卡 */
.result-card {
  background: #fff;
  border-radius: 8px;
  padding: 14px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}
.table-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
  color: #666;
  font-size: 13px;
}
:deep(.row-selected) {
  background: #e8f2ff !important;
}
.result-actions {
  margin-top: 14px;
  display: flex;
  gap: 12px;
}
.blue-btn {
  background: #1e6ecf;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 8px 28px;
  font-size: 13px;
  cursor: pointer;
  font-weight: 600;
  &:hover {
    background: #1857a8;
  }
}
.result-actions .orange-btn {
  position: static;
  background: #f2a443;
  padding: 8px 28px;
  box-shadow: 0 2px 6px rgba(242, 164, 67, 0.3);
  &:hover:not(:disabled) {
    background: #e2923a;
  }
}

/* 生命周期卡片 */
.lifecycle-row {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 10px;
}
.lc-card {
  background: #fff;
  border-radius: 6px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  .lc-head {
    background: #eaf1fb;
    color: #1e6ecf;
    font-weight: 700;
    font-size: 13px;
    text-align: center;
    padding: 6px 0;
  }
  .lc-value {
    text-align: center;
    padding: 10px 6px 4px;
    font-size: 18px;
    font-weight: 700;
    color: #1e6ecf;
    background: linear-gradient(180deg, #c8dcf5 0%, #e5eef9 100%);
    .lc-unit {
      font-size: 12px;
      margin-left: 2px;
    }
  }
  .lc-desc {
    padding: 6px 8px 10px;
    font-size: 10px;
    color: #606266;
    background: linear-gradient(180deg, #e5eef9 0%, #fff 100%);
    text-align: center;
    min-height: 42px;
  }
}

/* 高/低价值卡 */
.value-card {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}
.vc-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 28px;
}
.vc-title {
  text-align: center;
  font-size: 15px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 12px;
}
.vc-row {
  display: grid;
  grid-template-columns: 42px 1fr 50px;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
  &.right {
    grid-template-columns: 50px 1fr 42px;
  }
  .vc-num {
    font-size: 12px;
    color: #606266;
    text-align: right;
  }
  .vc-label {
    font-size: 12px;
    color: #606266;
    text-align: left;
  }
  &.right .vc-num {
    text-align: left;
  }
  &.right .vc-label {
    text-align: right;
  }
}
.vc-bar {
  height: 16px;
  background: #eef3fb;
  border-radius: 2px;
  overflow: hidden;
}
.vc-row:not(.right) .vc-bar {
  display: flex;
  justify-content: flex-start;
}
.vc-row.right .vc-bar {
  display: flex;
  justify-content: flex-end;
}
.vc-bar-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.8s;
  &.hi {
    background: linear-gradient(90deg, #a6c8eb, #4a90e2);
  }
  &.lo {
    background: linear-gradient(90deg, #103a70, #1e6ecf);
  }
}
.vc-footer {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px dashed #e4e7ed;
  .vc-footer-title {
    font-size: 15px;
    font-weight: 700;
    color: #303133;
  }
  .vc-footer-sub {
    font-size: 11px;
    color: #909399;
    margin-top: 4px;
  }
}

/* 诊断卡 */
.diag-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  display: flex;
  overflow: hidden;
  min-height: 260px;
}
.diag-label {
  writing-mode: vertical-rl;
  text-orientation: upright;
  background: linear-gradient(180deg, #1e6ecf, #4a90e2);
  color: #fff;
  padding: 16px 10px;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.diag-body {
  flex: 1;
  padding: 12px;
  display: flex;
  gap: 10px;
  align-items: center;
  :deep(.el-table) {
    font-size: 12px;
  }
}
.diag-body > :deep(.echart-container) {
  flex: 1;
}
</style>
