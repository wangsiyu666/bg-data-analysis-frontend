<template>
  <div class="strategy-area">
    <div class="main-title">
      <svg viewBox="0 0 18 18" width="16" height="16"><path d="M9 2l2 5 5 .5-4 3 1 5-4-3-4 3 1-5-4-3 5-.5z" fill="#1e6ecf"/></svg>
      <span>智能运营策略生成</span>
    </div>

    <!-- 策略内容详细配置 -->
    <div class="block">
      <div class="block-title">策略内容详细配置</div>
      <el-row :gutter="16">
        <el-col :span="12">
          <div class="field-label">策略名称</div>
          <el-input v-model="strategy.name" placeholder="（自动生成后可修改）" />
        </el-col>
        <el-col :span="12">
          <div class="field-label">策略类别</div>
          <el-checkbox-group v-model="strategy.categories">
            <el-checkbox label="挽留" />
            <el-checkbox label="升级" />
            <el-checkbox label="交叉销售" />
            <el-checkbox label="新客拉新" />
          </el-checkbox-group>
        </el-col>
      </el-row>

      <div class="field-label" style="margin-top: 12px">适用条件说明</div>
      <el-input
        v-model="strategy.condition"
        type="textarea"
        :rows="2"
        placeholder="若无圈选客群此处为空"
      />

      <el-row :gutter="16" style="margin-top: 12px">
        <el-col :span="12">
          <div class="field-label">策略描述</div>
          <el-input v-model="strategy.descDetail.desc" type="textarea" :rows="2" />
        </el-col>
        <el-col :span="12">
          <div class="field-label">活动扣费方式</div>
          <el-input v-model="strategy.descDetail.paymentMethod" type="textarea" :rows="2" />
        </el-col>
      </el-row>
      <el-row :gutter="16" style="margin-top: 12px">
        <el-col :span="8">
          <div class="field-label">关联产品</div>
          <el-input v-model="strategy.descDetail.relatedProducts" />
        </el-col>
        <el-col :span="8">
          <div class="field-label">权益内容</div>
          <el-input v-model="strategy.descDetail.benefits" />
        </el-col>
        <el-col :span="8">
          <div class="field-label">有效期</div>
          <el-input v-model="strategy.descDetail.validity" />
        </el-col>
      </el-row>
      <el-row :gutter="16" style="margin-top: 12px">
        <el-col :span="12">
          <div class="field-label">预计 ARPU 提升值</div>
          <div class="metric-box blue-text"> {{ strategy.expectedArpuLift || '--' }} </div>
        </el-col>
        <el-col :span="12">
          <div class="field-label">客群规模确认</div>
          <div class="metric-box dark-bg"> {{ (strategy.segmentSize || 0).toLocaleString() }} 人 </div>
        </el-col>
      </el-row>
    </div>

    <!-- 执行渠道与话术 -->
    <div class="block">
      <div class="block-title">执行渠道与话术</div>
      <div class="sub-title">推荐渠道</div>
      <div class="channel-cards">
        <div
          v-for="ch in execution.channels"
          :key="ch.id"
          class="ch-card"
          :class="{ selected: selectedChannelId === ch.id }"
          @click="selectChannel(ch)"
        >
          <div class="check" v-if="selectedChannelId === ch.id">✓</div>
          <div class="ch-icon">{{ iconFor(ch) }}</div>
          <div class="ch-name">{{ ch.name }}</div>
          <div v-if="selectedChannelId === ch.id" class="tag-main">主推荐渠道</div>
          <div v-else class="tag-rank">TOP{{ ch.rank }}</div>
        </div>
        <div v-if="!execution.channels.length" class="empty">点击"开始生成策略"查看推荐渠道</div>
      </div>

      <div class="sub-title">AI 多版本话术对比</div>
      <div class="script-cards">
        <div
          v-for="s in currentScripts"
          :key="s.id"
          class="s-card"
          :class="{ selected: selectedScriptId === s.id }"
          @click="selectScript(s)"
        >
          <div class="check" v-if="selectedScriptId === s.id">✓</div>
          <div class="s-title">{{ s.title }}</div>
          <div class="s-content">{{ s.content }}</div>
          <div v-if="selectedScriptId === s.id" class="tag-main">主推话术</div>
        </div>
        <div v-if="!currentScripts.length" class="empty">请先选择推荐渠道</div>
      </div>

      <div class="sub-title">营销调度设置</div>
      <el-row :gutter="16">
        <el-col :span="10">
          <div class="field-label">营销频率</div>
          <EChart :option="frequencyOption" height="120px" />
        </el-col>
        <el-col :span="14">
          <div class="field-label">AI 最佳营销时机建议</div>
          <div class="week-bars">
            <div
              v-for="(w, idx) in weekLabels"
              :key="idx"
              class="week-bar"
              :class="{ active: bestWeekdays.includes(idx + 1) }"
            >
              <div class="bar-fill" :style="{ height: bestWeekdays.includes(idx + 1) ? '85%' : '35%' }"></div>
              <div class="bar-label">{{ w }}</div>
            </div>
          </div>
          <el-input
            v-model="execution.bestTime.label"
            placeholder="最佳营销时刻将在生成后展现"
            readonly
            class="best-time-input"
          />
        </el-col>
      </el-row>
    </div>

    <!-- 策略执行效果预测大屏 -->
    <div class="dark-block">
      <div class="dark-title">
        <svg viewBox="0 0 18 18" width="14" height="14"><path d="M2 4h14v10H2z" stroke="#f2a443" stroke-width="1.5" fill="none"/><path d="M5 10l3-3 2 2 3-4" stroke="#f2a443" stroke-width="1.5" fill="none" stroke-linecap="round"/></svg>
        <span>策略执行效果预测大屏</span>
      </div>

      <div class="dark-grid">
        <div class="dark-metrics">
          <div class="pm-card">
            <div class="pm-title">预测转化率 P-CVR</div>
            <div class="pm-main">
              <span class="pm-num">{{ predict.pCvr.to || '0.142' }}</span>
              <span class="pm-up">+2%</span>
            </div>
          </div>
          <div class="pm-card">
            <div class="pm-title">预测投资回报率 P-ROI</div>
            <div class="pm-main">
              <span class="pm-num">{{ predict.pRoi.to || '1:8.4' }}</span>
              <span class="pm-up">1.4倍+6</span>
            </div>
          </div>
          <div class="pm-card">
            <div class="pm-title">预测接通触达率 P-RR</div>
            <div class="pm-main">
              <span class="pm-num">{{ predict.pRr.to || '0.925' }}</span>
            </div>
          </div>
        </div>

        <div class="dark-chart-wrap">
          <div class="chart-head">
            <span class="ch-title">实施策略期限持率趋势走势 (本月P90)</span>
            <div class="dim-switch">
              <el-radio-group v-model="dimension" @change="handleDimChange" size="small">
                <el-radio-button label="region">按地区</el-radio-button>
                <el-radio-button label="arpu">按APRU</el-radio-button>
                <el-radio-button label="age">按年龄区间</el-radio-button>
              </el-radio-group>
            </div>
          </div>
          <EChart :option="predictLineOption" height="220px" />
        </div>
      </div>
    </div>

    <!-- 策略发布 -->
    <div class="publish-row">
      <button class="publish-btn" :disabled="publishLoading || !strategy.id" @click="handlePublish">
        {{ publishLoading ? '发布中...' : (publishLabel || '发布策略') }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import EChart from '@/components/EChart.vue'
import { predictStrategy, publishStrategy } from '@/api/strategy'

const props = defineProps({
  strategyData: { type: Object, default: null },
  executionData: { type: Object, default: null },
  predictData: { type: Object, default: null },
  selectedProducts: { type: Array, default: () => [] },
  segmentCount: { type: Number, default: 0 },
  publishLabel: { type: String, default: '发布策略' }
})

const emit = defineEmits(['publish'])

const weekLabels = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
const dimension = ref('region')
const publishLoading = ref(false)
const selectedChannelId = ref('')
const selectedScriptId = ref('')

const strategy = reactive({
  id: '',
  name: '',
  categories: [],
  condition: '',
  descDetail: {
    desc: '',
    paymentMethod: '',
    relatedProducts: '',
    benefits: '',
    validity: ''
  },
  expectedArpuLift: '',
  segmentSize: 0
})

const execution = reactive({
  channels: [],
  scripts: {},
  frequency: { level: '标准', times: 2, options: [] },
  bestTime: { weekdays: [], label: '' }
})

const predict = reactive({
  pCvr: { from: 0, to: 0 },
  pRoi: { from: 0, to: 0 },
  pRr: { from: 0, to: 0 },
  categories: [],
  series: []
})

watch(
  () => props.strategyData,
  (v) => {
    if (!v) return
    Object.assign(strategy, v)
    if (props.selectedProducts.length) {
      strategy.descDetail.relatedProducts = props.selectedProducts.map((p) => p.name).join(',')
    }
    if (props.segmentCount) {
      strategy.segmentSize = props.segmentCount
    }
  },
  { immediate: true, deep: true }
)

watch(
  () => props.executionData,
  (v) => {
    if (!v) return
    execution.channels = v.channels || []
    execution.scripts = v.scripts || {}
    execution.frequency = v.frequency || execution.frequency
    execution.bestTime = v.bestTime || execution.bestTime
    selectedChannelId.value = execution.channels[0]?.id || ''
    selectedScriptId.value = currentScripts.value[0]?.id || ''
  },
  { immediate: true, deep: true }
)

watch(
  () => props.predictData,
  (v) => {
    if (!v) return
    Object.assign(predict, v)
  },
  { immediate: true, deep: true }
)

const currentScripts = computed(() => {
  if (!selectedChannelId.value) return []
  return execution.scripts?.[selectedChannelId.value] || []
})

const bestWeekdays = computed(() => execution.bestTime?.weekdays || [])

function iconFor(ch) {
  const m = { app: '📱', sms: '✉️', wechat: '🗨️', outcall: '📞', email: '📧' }
  return m[ch.id] || '📌'
}

function selectChannel(ch) {
  selectedChannelId.value = ch.id
  selectedScriptId.value = currentScripts.value[0]?.id || ''
}

function selectScript(s) {
  selectedScriptId.value = s.id
}

const frequencyOption = computed(() => {
  const level = execution.frequency?.level || '标准'
  const opts = execution.frequency?.options?.length
    ? execution.frequency.options
    : [
        { label: '保守', times: 1 },
        { label: '标准', times: 2 },
        { label: '激进', times: 4 }
      ]
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 60, right: 20, top: 10, bottom: 20 },
    xAxis: { type: 'value', max: 5, axisLabel: { show: false }, splitLine: { show: false } },
    yAxis: { type: 'category', data: opts.map((o) => `${o.label}(${o.times}次)`) },
    series: [
      {
        type: 'bar',
        data: opts.map((o) => ({
          value: o.times,
          itemStyle: {
            color: o.label === level ? '#1e6ecf' : '#c9d4e2',
            borderRadius: [0, 4, 4, 0]
          }
        })),
        label: { show: true, position: 'right', formatter: '{c}', color: '#1e6ecf', fontWeight: 700 },
        barWidth: 14
      }
    ]
  }
})

const predictLineOption = computed(() => {
  const s = predict.series || []
  return {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' },
    legend: { show: false },
    grid: { left: 40, right: 20, top: 16, bottom: 28 },
    xAxis: {
      type: 'category',
      data: predict.categories || [],
      axisLine: { lineStyle: { color: '#5a6a7a' } },
      axisLabel: { color: '#ccd4dc', fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#2d3c4e' } },
      axisLabel: { color: '#ccd4dc', fontSize: 11 }
    },
    series: s.length
      ? s.map((item, idx) => ({
          name: item.name,
          type: 'line',
          smooth: true,
          data: item.data,
          lineStyle: { width: 2.5, color: ['#f2a443', '#4a90e2', '#67c23a'][idx % 3] },
          itemStyle: { color: ['#f2a443', '#4a90e2', '#67c23a'][idx % 3] },
          areaStyle: idx === 0
            ? { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(242,164,67,0.3)' }, { offset: 1, color: 'rgba(242,164,67,0.02)' }] } }
            : undefined,
          symbolSize: 6
        }))
      : [
          {
            type: 'line',
            smooth: true,
            data: [5, 5.2, 5.5, 6, 6.8, 7.4, 7.9, 8.2],
            lineStyle: { width: 2.5, color: '#f2a443' },
            itemStyle: { color: '#f2a443' },
            areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(242,164,67,0.3)' }, { offset: 1, color: 'rgba(242,164,67,0.02)' }] } },
            symbolSize: 5
          }
        ]
  }
})

async function handleDimChange(d) {
  if (!strategy.id) return
  try {
    const res = await predictStrategy({ strategyId: strategy.id, dimension: d })
    Object.assign(predict, res)
  } catch (e) {}
}

async function handlePublish() {
  if (!strategy.id) {
    ElMessage.warning('请先生成策略')
    return
  }
  publishLoading.value = true
  try {
    const channel = execution.channels.find((c) => c.id === selectedChannelId.value)
    const script = currentScripts.value.find((s) => s.id === selectedScriptId.value)
    await publishStrategy({
      strategy,
      channel,
      script,
      products: props.selectedProducts,
      frequency: execution.frequency,
      bestTime: execution.bestTime,
      segmentSize: strategy.segmentSize
    })
    ElMessage.success('策略发布成功！已更新到产品/策略/话术/执行计划/客群表')
    emit('publish')
  } finally {
    publishLoading.value = false
  }
}
</script>

<style lang="scss" scoped>
.strategy-area {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}
.main-title {
  font-size: 16px;
  font-weight: 700;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
  padding-bottom: 10px;
  border-bottom: 1px solid #f0f2f5;
}
.block {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px dashed #ebeef5;
  &:last-of-type {
    border-bottom: none;
  }
}
.block-title {
  font-size: 15px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 12px;
}
.sub-title {
  font-size: 13px;
  font-weight: 700;
  color: #606266;
  margin: 12px 0 6px;
}
.field-label {
  font-size: 13px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 4px;
}
.metric-box {
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 20px;
  font-weight: 700;
  &.blue-text {
    background: #f5f7fa;
    color: #1e6ecf;
  }
  &.dark-bg {
    background: linear-gradient(90deg, #1e6ecf, #4a90e2);
    color: #fff;
  }
}
.channel-cards,
.script-cards {
  display: grid;
  gap: 12px;
}
.channel-cards {
  grid-template-columns: 1fr 1fr;
}
.script-cards {
  grid-template-columns: 1fr 1fr;
}
.ch-card,
.s-card {
  position: relative;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  padding: 14px;
  cursor: pointer;
  background: #fff;
  transition: all 0.2s;
  &:hover {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  }
  &.selected {
    border-color: #1e6ecf;
    background: #f0f6ff;
    box-shadow: 0 0 0 1px #1e6ecf inset;
  }
  .check {
    position: absolute;
    right: 8px;
    top: 6px;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background: #1e6ecf;
    color: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 13px;
  }
  .tag-main {
    display: inline-block;
    margin-top: 6px;
    font-size: 12px;
    padding: 2px 8px;
    border-radius: 10px;
    background: #1e6ecf;
    color: #fff;
  }
  .tag-rank {
    display: inline-block;
    margin-top: 6px;
    font-size: 12px;
    padding: 2px 8px;
    border-radius: 10px;
    background: #f0f2f5;
    color: #606266;
  }
}
.ch-card {
  display: flex;
  align-items: center;
  gap: 12px;
  .ch-icon {
    font-size: 28px;
  }
  .ch-name {
    font-size: 15px;
    font-weight: 700;
    color: #303133;
  }
}
.s-card {
  .s-title {
    font-size: 13px;
    font-weight: 700;
    color: #1e6ecf;
  }
  .s-content {
    margin-top: 6px;
    font-size: 13px;
    color: #606266;
    line-height: 1.6;
  }
}
.empty {
  grid-column: 1 / -1;
  text-align: center;
  color: #909399;
  background: #f5f7fa;
  padding: 20px;
  border-radius: 8px;
}
.week-bars {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 6px;
  height: 100px;
  align-items: end;
  background: #f0f6ff;
  padding: 8px;
  border-radius: 6px;
}
.week-bar {
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
  justify-content: end;
  gap: 4px;
  .bar-fill {
    width: 70%;
    background: #c9d4e2;
    border-radius: 4px 4px 0 0;
    transition: all 0.4s;
  }
  .bar-label {
    font-size: 10px;
    color: #606266;
  }
  &.active .bar-fill {
    background: linear-gradient(180deg, #1e6ecf, #4a90e2);
  }
  &.active .bar-label {
    color: #1e6ecf;
    font-weight: 700;
  }
}
.best-time-input {
  margin-top: 10px;
  :deep(.el-input__inner) {
    background: #f5f7fa;
    font-weight: 700;
    color: #1e6ecf;
  }
}
.dark-block {
  background: linear-gradient(135deg, #0a1f3d, #1a3358);
  border-radius: 8px;
  padding: 16px 20px 20px;
  margin-top: 20px;
  color: #fff;
}
.dark-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 14px;
}
.dark-grid {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 18px;
}
.dark-metrics {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.pm-card {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(74, 144, 226, 0.2);
  border-radius: 6px;
  padding: 12px 14px;
}
.pm-title {
  font-size: 12px;
  color: #aab8c8;
  margin-bottom: 6px;
}
.pm-main {
  display: flex;
  align-items: baseline;
  gap: 8px;
}
.pm-num {
  font-size: 22px;
  font-weight: 700;
  color: #fff;
}
.pm-up {
  color: #f2a443;
  font-size: 12px;
  font-weight: 600;
}
.dark-chart-wrap {
  background: rgba(0, 0, 0, 0.15);
  border-radius: 6px;
  padding: 12px 14px;
}
.chart-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}
.ch-title {
  font-size: 12px;
  color: #ccd4dc;
}
.dim-switch :deep(.el-radio-button__inner) {
  background: transparent;
  color: #aab8c8;
  border-color: #3b5a7f;
  padding: 4px 10px;
  font-size: 11px;
}
.dim-switch :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: #f2a443;
  border-color: #f2a443;
  color: #fff;
  box-shadow: none;
}
.publish-row {
  text-align: center;
  margin-top: 20px;
}
.publish-btn {
  background: #f2a443;
  border: none;
  color: #fff;
  font-size: 15px;
  font-weight: 700;
  padding: 12px 64px;
  border-radius: 6px;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(242, 164, 67, 0.4);
  transition: all 0.2s;
  &:hover:not(:disabled) {
    background: #e2923a;
  }
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
}
</style>
