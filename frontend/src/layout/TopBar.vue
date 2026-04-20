<template>
  <div class="top-bar">
    <div class="brand">
      <div class="logo-icon">
        <svg viewBox="0 0 28 28" width="26" height="26" fill="none">
          <circle cx="14" cy="14" r="13" stroke="currentColor" stroke-width="2" />
          <path d="M10 9 L5 14 L10 19" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none" />
          <path d="M18 9 L23 14 L18 19" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none" />
        </svg>
      </div>
      <span class="brand-text">TeleCompass智能运营</span>
    </div>

    <nav class="nav-tabs">
      <router-link
        v-for="n in navs"
        :key="n.path"
        :to="n.path"
        class="nav-item"
        :class="{ active: route.path === n.path }"
      >
        {{ n.label }}
      </router-link>
    </nav>

    <div class="now">{{ now }}</div>
  </div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const navs = [
  { path: '/dashboard', label: '首页' },
  { path: '/segment', label: '客群分析' },
  { path: '/product-ops', label: '产品运营' },
  { path: '/customer-ops', label: '客群运营' },
  { path: '/evaluation', label: '运营评估' }
]

const now = ref('')
let timer = null

function pad(n) {
  return String(n).padStart(2, '0')
}

function formatNow() {
  const d = new Date()
  const weekMap = ['日', '一', '二', '三', '四', '五', '六']
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日 星期${weekMap[d.getDay()]}  ${pad(
    d.getHours()
  )}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

onMounted(() => {
  now.value = formatNow()
  timer = setInterval(() => {
    now.value = formatNow()
  }, 1000)
})

onBeforeUnmount(() => {
  clearInterval(timer)
})
</script>

<style lang="scss" scoped>
.top-bar {
  position: sticky;
  top: 0;
  z-index: 20;
  height: 68px;
  background: #0a1f3d;
  color: #fff;
  display: flex;
  align-items: center;
  padding: 0 32px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.18);
}
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 260px;
}
.logo-icon {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: #1e6ecf;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
}
.brand-text {
  font-size: 17px;
  font-weight: 700;
  letter-spacing: 0.5px;
}
.nav-tabs {
  flex: 1;
  display: flex;
  justify-content: center;
  gap: 60px;
}
.nav-item {
  position: relative;
  color: #c9d4e2;
  font-size: 16px;
  font-weight: 500;
  text-decoration: none;
  padding: 8px 0;
  transition: color 0.2s;
  &:hover {
    color: #fff;
  }
  &.active {
    color: #fff;
    font-weight: 700;
    font-size: 17px;
    &::after {
      content: '';
      position: absolute;
      left: 50%;
      transform: translateX(-50%);
      bottom: -4px;
      width: 48px;
      height: 3px;
      border-radius: 2px;
      background: #4a90e2;
    }
  }
}
.now {
  font-size: 13px;
  color: #c9d4e2;
  min-width: 220px;
  text-align: right;
}
</style>
