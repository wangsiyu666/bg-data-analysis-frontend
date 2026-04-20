<template>
  <div class="evaluation">
    <!-- 顶部面包屑/进度条 -->
    <div class="top-bar-strip">
      <div class="strip-left">
        <span class="strip-active">● 主要预测客群 计算进度</span>
        <div class="strip-progress">
          <div class="sp-fill" :style="{ width: progress + '%' }"></div>
          <span class="sp-text">{{ progress }}%</span>
        </div>
      </div>
      <div class="strip-right">
        <span class="dot red"></span>
        <span>实时关键指标推介计算</span>
        <el-button size="small" plain>导出全部数据</el-button>
      </div>
    </div>

    <!-- 预测效果总览 -->
    <div class="section">
      <div class="sec-title">
        <svg viewBox="0 0 16 16" width="14" height="14"><path d="M2 12h12M4 10V7M7 10V5M10 10V3M13 10V8" stroke="#1e6ecf" stroke-width="1.5" fill="none" stroke-linecap="round"/></svg>
        <span>预测效果总览</span>
        <span class="sub-note">策略运营期整体预测汇总（当月P90数据）</span>
      </div>
      <div class="metric-grid">
        <div v-for="m in metrics" :key="m.key" class="m-card">
          <div class="m-top">
            <div class="m-icon" :style="{ background: lighten(m.color), color: m.color }">
              <svg v-if="m.icon === 'chart'" viewBox="0 0 18 18" width="18" height="18"><path d="M3 15V7l3 5 3-9 3 7 3-3v8H3z" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/></svg>
              <svg v-else-if="m.icon === 'warning'" viewBox="0 0 18 18" width="18" height="18"><path d="M9 2l7 13H2L9 2z" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M9 7v4M9 13v1" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
              <svg v-else-if="m.icon === 'user'" viewBox="0 0 18 18" width="18" height="18"><circle cx="9" cy="6" r="3" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M2 16c0-3 3-5 7-5s7 2 7 5" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>
              <svg v-else viewBox="0 0 18 18" width="18" height="18"><path d="M9 2a5 5 0 00-5 5v3l-2 3h14l-2-3V7a5 5 0 00-5-5zM7 15a2 2 0 004 0" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>
            </div>
            <div class="m-title">{{ m.title }}</div>
            <div class="m-yoy" :class="m.yoy >= 0 ? 'up' : 'down'">
              {{ m.yoy >= 0 ? '+' : '' }}{{ m.yoy }}%
              <span class="arrow">{{ m.yoy >= 0 ? '↑' : '↓' }}</span>
            </div>
          </div>
          <div class="m-value">
            <CountNumber :end="m.value" :decimals="m.decimals" :suffix="m.unit" :duration="1.8" />
          </div>
          <div class="m-foot">较上周同期{{ m.yoy >= 0 ? '上升' : '下降' }}</div>
        </div>
      </div>
    </div>

    <!-- 流失预警表格 -->
    <div class="section">
      <div class="sec-title">
        <svg viewBox="0 0 16 16" width="14" height="14"><rect x="2" y="3" width="12" height="10" rx="1.5" stroke="#1e6ecf" stroke-width="1.5" fill="none"/><path d="M2 7h12M6 3v10" stroke="#1e6ecf" stroke-width="1.5"/></svg>
        <span>流失预警</span>
        <div style="margin-left:auto; display:flex; gap:8px">
          <el-input size="small" placeholder="搜索策略名称" style="width: 200px" clearable v-model="tableFilter">
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
      </div>
      <el-table :data="filteredAlerts" size="small" stripe style="width: 100%" border>
        <el-table-column prop="strategy" label="策略名称" min-width="180" />
        <el-table-column prop="time" label="触发时间" width="160" />
        <el-table-column label="预警状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small" effect="light">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="completion" label="完成率" width="90">
          <template #default="{ row }">{{ row.completion }}%</template>
        </el-table-column>
        <el-table-column prop="risk" label="风险值" width="90" />
        <el-table-column prop="scope" label="影响范围" width="100" />
        <el-table-column label="操作" width="100">
          <template #default>
            <el-button link type="primary" size="small">查看</el-button>
            <el-button link type="info" size="small">修正</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pager">
        <span>共 {{ alertTable.length }} 条数据, 当前页 1/1</span>
        <el-pagination background layout="prev, pager, next" :total="alertTable.length" :page-size="10" small />
      </div>
    </div>

    <!-- 趋势多维分析 -->
    <div class="section">
      <div class="sec-title">
        <svg viewBox="0 0 16 16" width="14" height="14"><path d="M2 14l4-6 4 3 4-8" stroke="#1e6ecf" stroke-width="1.5" fill="none"/></svg>
        <span>趋势多维分析</span>
      </div>
      <div class="two-col">
        <div class="chart-card">
          <div class="cc-title">
            <span>客户流失率(CVR)趋势分析</span>
            <span class="cc-sub">按周粒度</span>
          </div>
          <EChart :option="trendOption" height="220px" />
          <div class="chart-legend">
            <span class="lg-item"><i style="background:#f2a443"></i>本周</span>
            <span class="lg-item"><i style="background:#1e6ecf"></i>上周</span>
            <span class="lg-item"><i style="background:#67c23a"></i>同期</span>
          </div>
        </div>
        <div class="chart-card">
          <div class="cc-title">
            <span>可用能源位与属性对比</span>
            <span class="cc-sub">多指标</span>
          </div>
          <EChart :option="energyOption" height="240px" />
        </div>
      </div>
    </div>

    <!-- 图谱深度对比 -->
    <div class="section">
      <div class="sec-title">
        <svg viewBox="0 0 16 16" width="14" height="14"><polygon points="8,1 14,5 14,11 8,15 2,11 2,5" stroke="#1e6ecf" stroke-width="1.5" fill="none"/></svg>
        <span>图谱深度对比</span>
      </div>
      <div class="two-col">
        <div class="chart-card legend-list">
          <div class="ll-title">分析内容：已执行</div>
          <div v-for="(r, idx) in radarLabels" :key="idx" class="ll-item">
            <i class="dot" :style="{ background: r.color }"></i>
            <div>
              <strong>{{ r.text }}</strong>
              <div class="ll-sub">{{ r.sub }}</div>
            </div>
          </div>
          <div class="ll-note">
            <div class="note-title">分析解读建议</div>
            <div>● <b>全渠道覆盖</b>：综合APP行为、客户数据及策略效果相关指标以形成评估框架</div>
            <div>● <b>反馈闭环</b>：基于实际执行结果持续优化策略参数与阈值</div>
          </div>
        </div>
        <div class="chart-card">
          <EChart :option="radarOption" height="340px" />
        </div>
      </div>
    </div>

    <!-- 客群深度调整 -->
    <div class="section">
      <div class="sec-title">
        <svg viewBox="0 0 16 16" width="14" height="14"><circle cx="8" cy="8" r="6" stroke="#1e6ecf" stroke-width="1.5" fill="none"/><path d="M8 2v12M2 8h12" stroke="#1e6ecf" stroke-width="1" fill="none"/></svg>
        <span>客群深度调整</span>
      </div>
      <div class="three-col">
        <div class="chart-card">
          <div class="cc-title"><span>▓ 地域流失变化</span></div>
          <EChart :option="regionBarOption" height="220px" />
        </div>
        <div class="chart-card">
          <div class="cc-title"><span>▓ 用户行为预测</span></div>
          <EChart :option="behaviorBarOption" height="220px" />
        </div>
        <div class="chart-card">
          <div class="cc-title"><span>▓ 触达通道占比</span></div>
          <EChart :option="pieOption" height="220px" />
        </div>
      </div>
      <div class="kpi-strip">
        <div class="kpi-head">
          <div class="kh-title">流动性走减后 APRU 关联影响</div>
          <div class="kh-sub">流动性下降后，对ARPU相关指标的影响</div>
        </div>
        <div class="kpi-items">
          <div v-for="(k, idx) in seg.kpis" :key="idx" class="kpi-item">
            <div class="kv">{{ k.value }}</div>
            <div class="kl">{{ k.label }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 话术效果分析 -->
    <div class="section">
      <div class="sec-title">
        <svg viewBox="0 0 16 16" width="14" height="14"><path d="M2 3h12v9H6l-4 3z" stroke="#1e6ecf" stroke-width="1.5" fill="none"/></svg>
        <span>话术效果分析</span>
      </div>
      <div class="two-col">
        <div class="chart-card">
          <div class="cc-title">热点话术方案 (TOP3)</div>
          <div class="script-list">
            <div v-for="(s, idx) in scriptEffects" :key="idx" class="script-item">
              <div class="si-left">
                <div class="si-title">{{ s.title }}</div>
                <div class="si-desc">{{ s.desc }}</div>
              </div>
              <div class="si-right">
                <div class="si-num">{{ s.percent }}%</div>
                <div class="si-sub">{{ s.sub }}</div>
                <div class="si-bar">
                  <div class="si-fill" :style="{ width: Math.min(100, s.percent * 4) + '%' }"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="chart-card dark-card">
          <div class="ai-box">
            <div class="ai-head">
              <div class="ai-avatar">
                <svg viewBox="0 0 32 32" width="28" height="28"><circle cx="16" cy="16" r="14" stroke="#4a90e2" stroke-width="2" fill="none"/><circle cx="11" cy="14" r="1.5" fill="#4a90e2"/><circle cx="21" cy="14" r="1.5" fill="#4a90e2"/><path d="M11 20c2 2 8 2 10 0" stroke="#4a90e2" stroke-width="1.5" fill="none"/></svg>
              </div>
              <div class="ai-title">{{ aiScriptGen.title }}</div>
            </div>
            <div class="ai-body">{{ aiScriptGen.content }}</div>
            <div class="ai-chips">
              <span class="chip">情绪感知</span>
              <span class="chip">场景识别</span>
              <span class="chip">意图理解</span>
            </div>
            <button class="ai-btn">
              <svg viewBox="0 0 16 16" width="14" height="14"><path d="M8 2v12M2 8h12" stroke="#fff" stroke-width="1.5"/></svg>
              立即生成新话术
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 执行计划全链路分析 -->
    <div class="section">
      <div class="sec-title">
        <svg viewBox="0 0 16 16" width="14" height="14"><path d="M2 4l3 3-3 3M8 4h6M8 10h6M2 13l3-3" stroke="#1e6ecf" stroke-width="1.5" fill="none"/></svg>
        <span>执行计划全链路分析</span>
      </div>
      <div class="three-col">
        <div class="chart-card">
          <div class="cc-title">{{ execution.c1.title }}</div>
          <EChart :option="execLineOption(execution.c1, '#1e6ecf')" height="200px" />
        </div>
        <div class="chart-card">
          <div class="cc-title">{{ execution.c2.title }}</div>
          <EChart :option="execBarOption(execution.c2, '#67c23a')" height="200px" />
        </div>
        <div class="chart-card">
          <div class="cc-title">{{ execution.c3.title }}</div>
          <EChart :option="execLineDoubleOption(execution.c3)" height="200px" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Search } from '@element-plus/icons-vue'
import EChart from '@/components/EChart.vue'
import CountNumber from '@/components/CountNumber.vue'
import { evaluationData } from '@/mock/dashboard'

const {
  metrics,
  alertTable,
  trend,
  energyCompare,
  radar,
  radarLabels,
  segmentAdjust: seg,
  scriptEffects,
  aiScriptGen,
  executionCharts: execution
} = evaluationData

const progress = ref(60.3)
const tableFilter = ref('')

const filteredAlerts = computed(() => {
  if (!tableFilter.value) return alertTable
  return alertTable.filter((r) => r.strategy.includes(tableFilter.value))
})

function lighten(color) {
  const map = {
    '#1e6ecf': '#e7f0fb',
    '#409eff': '#eaf4ff',
    '#f2c037': '#fdf5e0',
    '#67c23a': '#eaf6e1'
  }
  return map[color] || '#eef3fb'
}

function statusType(status) {
  if (status === '已完成') return 'success'
  if (status === '待审核') return 'warning'
  if (status === '进行中') return 'primary'
  return 'info'
}

const trendOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 34, right: 20, top: 16, bottom: 30 },
  xAxis: { type: 'category', data: trend.x, boundaryGap: false, axisLabel: { fontSize: 11 } },
  yAxis: { type: 'value', axisLabel: { formatter: '{value}%', fontSize: 11 }, splitLine: { lineStyle: { color: '#f0f2f5' } } },
  series: [
    { name: '本周', type: 'line', data: trend.cvr, smooth: true, lineStyle: { color: '#f2a443', width: 2.5 }, itemStyle: { color: '#f2a443' }, symbolSize: 6 },
    { name: '上周', type: 'line', data: trend.cvr2, smooth: true, lineStyle: { color: '#1e6ecf', width: 2 }, itemStyle: { color: '#1e6ecf' } },
    { name: '同期', type: 'line', data: trend.cvr3, smooth: true, lineStyle: { color: '#67c23a', width: 2 }, itemStyle: { color: '#67c23a' } }
  ]
}))

const energyOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 40, right: 20, top: 20, bottom: 30 },
  xAxis: { type: 'category', data: energyCompare.map((e) => e.name), axisLabel: { fontSize: 11 } },
  yAxis: { type: 'value', axisLabel: { fontSize: 11 }, splitLine: { lineStyle: { color: '#f0f2f5' } } },
  series: [
    {
      type: 'bar',
      data: energyCompare.map((e) => ({ value: e.value, itemStyle: { color: e.color, borderRadius: [4, 4, 0, 0] } })),
      barWidth: 30
    }
  ]
}))

const radarOption = computed(() => ({
  tooltip: {},
  legend: { show: false },
  radar: {
    indicator: radar.indicator,
    radius: '65%',
    splitNumber: 4,
    axisName: { color: '#606266', fontSize: 12 },
    splitLine: { lineStyle: { color: '#e4e7ed' } },
    splitArea: { show: false }
  },
  series: [
    {
      type: 'radar',
      symbolSize: 4,
      data: radar.series.map((s, idx) => ({
        name: s.name,
        value: s.data,
        lineStyle: { color: ['#1e6ecf', '#67c23a', '#f2c037'][idx], width: 2 },
        itemStyle: { color: ['#1e6ecf', '#67c23a', '#f2c037'][idx] },
        areaStyle: { color: ['rgba(30,110,207,0.15)', 'rgba(103,194,58,0.15)', 'rgba(242,192,55,0.15)'][idx] }
      }))
    }
  ]
}))

const regionBarOption = computed(() => ({
  tooltip: {},
  grid: { left: 60, right: 20, top: 10, bottom: 20 },
  xAxis: { type: 'value', axisLabel: { fontSize: 10 } },
  yAxis: { type: 'category', data: seg.regionBar.x, axisLabel: { fontSize: 11 } },
  series: [
    {
      type: 'bar',
      data: seg.regionBar.value,
      itemStyle: { color: '#4a90e2', borderRadius: [0, 4, 4, 0] },
      barWidth: 14
    }
  ]
}))

const behaviorBarOption = computed(() => ({
  tooltip: {},
  grid: { left: 40, right: 20, top: 10, bottom: 40 },
  xAxis: { type: 'category', data: seg.behaviorBar.x, axisLabel: { fontSize: 10, rotate: 20 } },
  yAxis: { type: 'value', axisLabel: { fontSize: 10 } },
  series: [
    {
      type: 'bar',
      data: seg.behaviorBar.value,
      itemStyle: { color: '#a855f7', borderRadius: [4, 4, 0, 0] },
      barWidth: 30
    }
  ]
}))

const pieOption = computed(() => ({
  tooltip: { trigger: 'item', formatter: '{b}: {d}%' },
  legend: { orient: 'vertical', right: 10, top: 'middle', textStyle: { fontSize: 11 } },
  series: [
    {
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['35%', '50%'],
      label: { show: false },
      data: seg.pie,
      color: ['#1e6ecf', '#67c23a', '#f2c037', '#a855f7']
    }
  ]
}))

function execLineOption(c, color) {
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 30, right: 14, top: 10, bottom: 22 },
    xAxis: { type: 'category', data: c.x, axisLabel: { fontSize: 10 } },
    yAxis: { type: 'value', axisLabel: { fontSize: 10 } },
    series: [
      {
        type: 'line',
        data: c.value,
        smooth: true,
        lineStyle: { color, width: 2 },
        itemStyle: { color },
        areaStyle: { color: color + '30' }
      }
    ]
  }
}

function execBarOption(c, color) {
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 30, right: 14, top: 10, bottom: 22 },
    xAxis: { type: 'category', data: c.x, axisLabel: { fontSize: 10 } },
    yAxis: { type: 'value', axisLabel: { fontSize: 10 } },
    series: [{ type: 'bar', data: c.value, itemStyle: { color, borderRadius: [3, 3, 0, 0] }, barWidth: 14 }]
  }
}

function execLineDoubleOption(c) {
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 30, right: 14, top: 20, bottom: 22 },
    legend: { show: false },
    xAxis: { type: 'category', data: c.x, axisLabel: { fontSize: 10 } },
    yAxis: { type: 'value', axisLabel: { fontSize: 10 } },
    series: [
      { type: 'line', data: c.value, smooth: true, lineStyle: { color: '#f56c6c', width: 2 }, itemStyle: { color: '#f56c6c' } },
      { type: 'line', data: c.compare, smooth: true, lineStyle: { color: '#1e6ecf', width: 2 }, itemStyle: { color: '#1e6ecf' } }
    ]
  }
}
</script>

<style lang="scss" scoped>
.evaluation {
  padding-bottom: 30px;
  min-width: 1280px;
}

/* 顶部条 */
.top-bar-strip {
  background: #0a1f3d;
  color: #fff;
  border-radius: 6px;
  padding: 10px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
  font-size: 12px;
}
.strip-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.strip-active {
  color: #fff;
}
.strip-progress {
  position: relative;
  width: 220px;
  height: 6px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 3px;
  overflow: hidden;
  .sp-fill {
    height: 100%;
    background: linear-gradient(90deg, #f2a443, #f5b768);
    border-radius: 3px;
  }
  .sp-text {
    position: absolute;
    right: -40px;
    top: -5px;
    color: #f2a443;
    font-weight: 700;
  }
}
.strip-right {
  display: flex;
  align-items: center;
  gap: 10px;
  .dot.red {
    display: inline-block;
    width: 8px;
    height: 8px;
    background: #f56c6c;
    border-radius: 50%;
  }
}

/* 区块 */
.section {
  background: #fff;
  border-radius: 8px;
  padding: 14px 16px 18px;
  margin-bottom: 14px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}
.sec-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 15px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 14px;
  padding-bottom: 10px;
  border-bottom: 1px solid #f0f2f5;
  .sub-note {
    font-size: 11px;
    color: #909399;
    font-weight: 400;
    margin-left: 6px;
  }
}

/* 指标卡 */
.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}
.m-card {
  background: #fafbfd;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 12px 16px;
  transition: all 0.2s;
  &:hover {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
    transform: translateY(-1px);
  }
}
.m-top {
  display: flex;
  align-items: center;
  gap: 8px;
}
.m-icon {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.m-title {
  flex: 1;
  font-size: 12px;
  color: #606266;
}
.m-yoy {
  font-size: 11px;
  font-weight: 700;
  &.up { color: #67c23a; }
  &.down { color: #f56c6c; }
  .arrow { font-size: 12px; }
}
.m-value {
  margin-top: 10px;
  font-size: 26px;
  font-weight: 800;
  color: #303133;
}
.m-foot {
  margin-top: 4px;
  font-size: 11px;
  color: #909399;
}

.pager {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
  color: #606266;
  font-size: 12px;
}

/* 两列/三列 */
.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.three-col {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}
.chart-card {
  background: #fafbfd;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 12px 14px;
}
.cc-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 8px;
  .cc-sub {
    font-size: 11px;
    color: #909399;
    font-weight: 400;
  }
}
.chart-legend {
  display: flex;
  gap: 14px;
  justify-content: center;
  font-size: 11px;
  color: #606266;
  margin-top: 4px;
  .lg-item {
    display: flex;
    align-items: center;
    gap: 4px;
    i {
      display: inline-block;
      width: 14px;
      height: 3px;
      border-radius: 2px;
    }
  }
}

/* 图谱对比左侧列表 */
.legend-list {
  font-size: 12px;
  color: #606266;
  padding: 14px;
}
.ll-title {
  font-size: 13px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 10px;
}
.ll-item {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  margin-bottom: 10px;
  .dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    margin-top: 4px;
    flex-shrink: 0;
  }
  strong {
    color: #303133;
  }
  .ll-sub {
    color: #909399;
    font-size: 11px;
    margin-top: 2px;
    line-height: 1.5;
  }
}
.ll-note {
  margin-top: 14px;
  padding-top: 10px;
  border-top: 1px dashed #ebeef5;
  font-size: 11px;
  line-height: 1.8;
  color: #606266;
  .note-title {
    font-weight: 700;
    color: #303133;
    margin-bottom: 4px;
    font-size: 12px;
  }
  b { color: #1e6ecf; }
}

/* 客群深度 KPI 横条 */
.kpi-strip {
  margin-top: 14px;
  background: linear-gradient(90deg, #1e6ecf, #4a90e2);
  border-radius: 8px;
  padding: 16px 20px;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 20px;
}
.kpi-head {
  flex-shrink: 0;
  .kh-title {
    font-size: 14px;
    font-weight: 700;
  }
  .kh-sub {
    font-size: 11px;
    opacity: 0.8;
    margin-top: 2px;
  }
}
.kpi-items {
  display: flex;
  flex: 1;
  justify-content: space-around;
  gap: 20px;
}
.kpi-item {
  text-align: center;
  .kv {
    font-size: 20px;
    font-weight: 800;
  }
  .kl {
    font-size: 11px;
    opacity: 0.85;
    margin-top: 2px;
  }
}

/* 话术列表 */
.script-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.script-item {
  display: flex;
  gap: 12px;
  padding: 10px;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 6px;
}
.si-left {
  flex: 1;
  .si-title {
    font-size: 12px;
    font-weight: 700;
    color: #303133;
    margin-bottom: 4px;
  }
  .si-desc {
    font-size: 11px;
    color: #909399;
    line-height: 1.5;
  }
}
.si-right {
  min-width: 110px;
  text-align: right;
  .si-num {
    font-size: 18px;
    font-weight: 800;
    color: #1e6ecf;
  }
  .si-sub {
    font-size: 11px;
    color: #909399;
  }
  .si-bar {
    margin-top: 4px;
    height: 4px;
    background: #eef3fb;
    border-radius: 2px;
    overflow: hidden;
  }
  .si-fill {
    height: 100%;
    background: linear-gradient(90deg, #1e6ecf, #4a90e2);
  }
}

/* AI 话术生成器暗卡 */
.dark-card {
  background: linear-gradient(135deg, #0a1f3d, #1a3358);
  border-color: #0a1f3d;
  padding: 16px;
  position: relative;
  overflow: hidden;
}
.ai-box {
  color: #fff;
}
.ai-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
.ai-avatar {
  background: rgba(74, 144, 226, 0.15);
  border-radius: 50%;
  padding: 6px;
}
.ai-title {
  font-size: 14px;
  font-weight: 700;
}
.ai-body {
  font-size: 12px;
  line-height: 1.6;
  color: #c9d4e2;
  margin-bottom: 12px;
}
.ai-chips {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
  .chip {
    background: rgba(74, 144, 226, 0.15);
    color: #7fb3ff;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 11px;
  }
}
.ai-btn {
  width: 100%;
  background: #1e6ecf;
  color: #fff;
  border: none;
  border-radius: 4px;
  padding: 10px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: background 0.2s;
  &:hover {
    background: #1857a8;
  }
}
</style>
