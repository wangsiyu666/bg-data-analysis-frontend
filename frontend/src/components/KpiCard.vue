<template>
  <div class="kpi-card" :class="['style-' + card.style]" @mouseenter="showTip = true" @mouseleave="showTip = false">
    <!-- 深蓝大卡 -->
    <template v-if="card.style === 'dark'">
      <div class="dark-value">
        <CountNumber :end="card.mainValue" />
        <span class="dark-unit">{{ card.unit }}</span>
      </div>
      <div class="dark-anno">{{ card.annotation }}</div>
      <div class="dark-yoy">
        <CountNumber :end="card.yoyValue" :decimals="1" :suffix="card.yoySuffix" />
        <span class="yoy-arrow up">↑</span>
      </div>
      <div class="dark-trend">
        <div v-for="b in card.trendBars" :key="b.year" class="tb">
          <div class="tb-bar" :style="{ height: b.value + '%' }"></div>
          <div class="tb-year">{{ b.year }}</div>
        </div>
      </div>
    </template>

    <!-- 白底小卡 -->
    <template v-else>
      <div class="light-head">
        <div class="light-icon" :class="card.icon">
          <svg v-if="card.icon === 'chart'" viewBox="0 0 20 20" width="22" height="22" fill="none">
            <path d="M3 17V7l4 6 4-9 4 4 2-2v11H3z" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          <svg v-else-if="card.icon === 'scale'" viewBox="0 0 20 20" width="22" height="22" fill="none">
            <path d="M10 3v14M4 7h12M5 13a2 2 0 01-2-2l2-4 2 4a2 2 0 01-2 2zM15 13a2 2 0 01-2-2l2-4 2 4a2 2 0 01-2 2z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          <svg v-else viewBox="0 0 20 20" width="22" height="22" fill="none">
            <circle cx="7" cy="7" r="3" stroke="currentColor" stroke-width="1.5" />
            <circle cx="14" cy="8" r="2.5" stroke="currentColor" stroke-width="1.5" />
            <path d="M2 17c0-3 2.5-5 5-5s5 2 5 5M10 17c0-2.5 2-4 4-4s4 1.5 4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
          </svg>
        </div>
        <div class="light-yoy" :class="card.yoy >= 0 ? 'up' : 'down'">
          <span>{{ card.yoy >= 0 ? '+' : '' }}{{ card.yoy }}%</span>
          <span class="arrow">{{ card.yoy >= 0 ? '↑' : '↓' }}</span>
        </div>
      </div>
      <div class="light-value">
        <CountNumber :end="card.mainValue" :decimals="1" :suffix="card.mainUnit" />
      </div>
      <div class="light-desc">{{ card.desc }}</div>
      <div class="light-bottom">
        <div class="pill">{{ card.labelBottom }}</div>
      </div>
    </template>

    <transition name="fade">
      <div class="tip" v-if="showTip && card.tooltip">{{ card.tooltip }}</div>
    </transition>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import CountNumber from './CountNumber.vue'

defineProps({ card: { type: Object, required: true } })
const showTip = ref(false)
</script>

<style lang="scss" scoped>
.kpi-card {
  position: relative;
  border-radius: 8px;
  padding: 14px 16px;
  min-height: 130px;
  display: flex;
  flex-direction: column;
  transition: box-shadow 0.2s, transform 0.2s;
  &:hover {
    transform: translateY(-2px);
  }
}
/* 深蓝卡 */
.style-dark {
  background: linear-gradient(160deg, #103a70 0%, #1e6ecf 120%);
  color: #fff;
  box-shadow: 0 2px 12px rgba(16, 58, 112, 0.25);
  .dark-value {
    font-size: 26px;
    font-weight: 700;
    line-height: 1.2;
    .dark-unit {
      font-size: 14px;
      margin-left: 4px;
      font-weight: 400;
    }
  }
  .dark-anno {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.75);
    margin-top: 2px;
  }
  .dark-yoy {
    margin-top: 10px;
    font-size: 22px;
    font-weight: 700;
    display: flex;
    align-items: baseline;
    gap: 4px;
    .yoy-arrow.up {
      color: #8fe388;
      font-size: 14px;
    }
  }
  .dark-trend {
    margin-top: auto;
    display: flex;
    gap: 6px;
    height: 40px;
    align-items: end;
    .tb {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 4px;
      .tb-bar {
        width: 80%;
        background: rgba(255, 255, 255, 0.35);
        border-radius: 2px 2px 0 0;
        min-height: 6px;
      }
      .tb-year {
        font-size: 9px;
        color: rgba(255, 255, 255, 0.55);
      }
    }
  }
}
/* 白底卡 */
.style-light {
  background: #fff;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  &:hover {
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
  }
  .light-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .light-icon {
    width: 36px;
    height: 36px;
    border-radius: 8px;
    background: #eef3fb;
    color: #1e6ecf;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .light-yoy {
    font-size: 12px;
    font-weight: 700;
    display: flex;
    align-items: baseline;
    gap: 2px;
    &.up {
      color: #67c23a;
    }
    &.down {
      color: #f56c6c;
    }
    .arrow {
      font-size: 14px;
    }
  }
  .light-value {
    margin-top: 10px;
    font-size: 26px;
    font-weight: 700;
    color: #1e6ecf;
    line-height: 1.2;
  }
  .light-desc {
    font-size: 11px;
    color: #909399;
    margin-top: 6px;
    line-height: 1.4;
    flex: 1;
  }
  .light-bottom {
    margin-top: 8px;
  }
  .pill {
    display: inline-block;
    padding: 4px 12px;
    background: linear-gradient(90deg, #1e6ecf, #4a90e2);
    color: #fff;
    font-size: 12px;
    font-weight: 600;
    border-radius: 12px;
  }
}
.tip {
  position: absolute;
  bottom: 100%;
  left: 10px;
  background: rgba(0, 0, 0, 0.8);
  color: #fff;
  padding: 6px 10px;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
  z-index: 20;
}
</style>
