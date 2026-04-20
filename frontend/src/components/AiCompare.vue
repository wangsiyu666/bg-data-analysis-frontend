<template>
  <div class="ai-compare">
    <div class="ac-title">
      <svg viewBox="0 0 16 16" width="14" height="14"><path d="M2 10h3v4H2zm4-6h3v10H6zm4 3h3v7h-3z" fill="#1e6ecf"/></svg>
      <span>AI运营情况对比图 (2026年)</span>
    </div>

    <div class="ac-main">
      <!-- 左侧说明 -->
      <div class="ac-desc">
        <div class="desc-row">
          <span class="dot blue"></span>
          <div>
            <div class="desc-title">{{ data.ai.title }}</div>
            <div class="desc-sub">{{ data.ai.desc }}</div>
          </div>
        </div>
        <div class="desc-row" style="margin-top:120px">
          <span class="dot dark"></span>
          <div>
            <div class="desc-title">{{ data.manual.title }}</div>
            <div class="desc-sub">{{ data.manual.desc }}</div>
          </div>
        </div>
      </div>

      <!-- 右侧双层环形图（带四周指标） -->
      <div class="ac-ring">
        <!-- AI 外圈指标（上半圈） -->
        <div class="ind ind-top-1">
          <div class="ind-title">{{ data.ai.indicators[0].label }}</div>
          <div class="ind-val">{{ data.ai.indicators[0].value }} <span class="u">{{ data.ai.indicators[0].unit }}</span></div>
        </div>
        <div class="ind ind-top-2">
          <div class="ind-val">{{ data.ai.indicators[1].value }} <span class="u">{{ data.ai.indicators[1].unit }}</span></div>
          <div class="ind-title">{{ data.ai.indicators[1].label }}</div>
        </div>
        <div class="ind ind-left-1">
          <div class="ind-title">{{ data.ai.indicators[3].label }}</div>
          <div class="ind-val">{{ data.ai.indicators[3].value }} <span class="u">{{ data.ai.indicators[3].unit }}</span></div>
        </div>
        <div class="ind ind-right-1">
          <div class="ind-title">{{ data.ai.indicators[2].label }}</div>
          <div class="ind-val">{{ data.ai.indicators[2].value }} <span class="u">{{ data.ai.indicators[2].unit }}</span></div>
        </div>

        <!-- 中心文字 -->
        <div class="center-text">
          <div class="ct-label">{{ data.center.label1 }}</div>
          <div class="ct-value up">{{ data.center.value1 }}</div>
          <div class="divider"></div>
          <div class="ct-value">{{ data.center.value2 }}</div>
          <div class="ct-label">营收同比增长</div>
        </div>

        <!-- 人工 内圈指标（下半圈） -->
        <div class="ind ind-bot-1">
          <div class="ind-val">{{ data.manual.indicators[0].value }} <span class="u">{{ data.manual.indicators[0].unit }}</span></div>
          <div class="ind-title">{{ data.manual.indicators[0].label }}</div>
        </div>
        <div class="ind ind-bot-2">
          <div class="ind-val">{{ data.manual.indicators[1].value }} <span class="u">{{ data.manual.indicators[1].unit }}</span></div>
          <div class="ind-title">{{ data.manual.indicators[1].label }}</div>
        </div>
        <div class="ind ind-left-2">
          <div class="ind-title">{{ data.manual.indicators[3].label }}</div>
          <div class="ind-val">{{ data.manual.indicators[3].value }} <span class="u">{{ data.manual.indicators[3].unit }}</span></div>
        </div>
        <div class="ind ind-right-2">
          <div class="ind-val">{{ data.manual.indicators[2].value }} <span class="u">{{ data.manual.indicators[2].unit }}</span></div>
          <div class="ind-title">{{ data.manual.indicators[2].label }}</div>
        </div>

        <!-- 双环 SVG -->
        <svg class="ring-svg" viewBox="0 0 320 320">
          <!-- 外环 AI -->
          <circle cx="160" cy="160" r="118" fill="none" stroke="#e6eef9" stroke-width="26" />
          <circle cx="160" cy="160" r="118" fill="none" stroke="#1e6ecf" stroke-width="26"
            stroke-dasharray="520 220" stroke-linecap="round"
            transform="rotate(-90 160 160)"
            class="ring-anim" />
          <!-- 内环 人工 -->
          <circle cx="160" cy="160" r="82" fill="none" stroke="#eef3fb" stroke-width="22" />
          <circle cx="160" cy="160" r="82" fill="none" stroke="#0a3a78" stroke-width="22"
            stroke-dasharray="340 200" stroke-linecap="round"
            transform="rotate(-90 160 160)"
            class="ring-anim-2" />
        </svg>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({ data: { type: Object, required: true } })
</script>

<style lang="scss" scoped>
.ai-compare {
  background: #fff;
  border-radius: 8px;
  padding: 14px 18px 18px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}
.ac-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 700;
  color: #303133;
  padding-bottom: 10px;
  border-bottom: 1px solid #f0f2f5;
}
.ac-main {
  display: grid;
  grid-template-columns: 150px 1fr;
  gap: 12px;
  margin-top: 14px;
}
.ac-desc {
  font-size: 12px;
  color: #606266;
  padding-top: 10px;
}
.desc-row {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-top: 6px;
    flex-shrink: 0;
    &.blue {
      background: #1e6ecf;
    }
    &.dark {
      background: #0a3a78;
    }
  }
  .desc-title {
    font-size: 13px;
    font-weight: 700;
    color: #303133;
    margin-bottom: 4px;
  }
  .desc-sub {
    font-size: 11px;
    color: #909399;
    line-height: 1.55;
  }
}
.ac-ring {
  position: relative;
  height: 360px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.ring-svg {
  width: 320px;
  height: 320px;
}
.ring-anim {
  animation: ring-draw 1.4s ease-out;
}
.ring-anim-2 {
  animation: ring-draw 1.8s ease-out;
}
@keyframes ring-draw {
  from { stroke-dasharray: 0 1500; }
}
.center-text {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  z-index: 2;
  .ct-label {
    font-size: 11px;
    color: #909399;
  }
  .ct-value {
    font-size: 22px;
    font-weight: 800;
    color: #103a70;
    margin: 2px 0;
    &.up {
      color: #1e6ecf;
    }
  }
  .divider {
    width: 60%;
    height: 1px;
    background: #e4e7ed;
    margin: 4px auto;
  }
}
.ind {
  position: absolute;
  font-size: 12px;
  color: #606266;
  text-align: center;
  z-index: 3;
  .ind-title {
    font-size: 11px;
    color: #909399;
  }
  .ind-val {
    font-weight: 700;
    font-size: 14px;
    color: #1e6ecf;
    .u {
      font-size: 11px;
      font-weight: 400;
      color: #606266;
    }
  }
}
/* 环绕指标位置 */
.ind-top-1 { top: 0; left: 70px; }
.ind-top-2 { top: 0; right: 70px; }
.ind-left-1 { top: 110px; left: 0; }
.ind-right-1 { top: 110px; right: 0; }
.ind-bot-1 { bottom: 50px; left: 60px; }
.ind-bot-2 { bottom: 0; right: 70px; .ind-val { color: #0a3a78; } }
.ind-left-2 { top: 190px; left: 30px; .ind-val { color: #0a3a78; } }
.ind-right-2 { top: 190px; right: 30px; .ind-val { color: #0a3a78; } }
.ind-bot-1 .ind-val { color: #0a3a78; }
</style>
