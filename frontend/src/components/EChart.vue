<template>
  <div ref="el" :style="{ width: '100%', height: height }"></div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, watch, ref, shallowRef } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  option: { type: Object, required: true },
  height: { type: String, default: '240px' },
  notMerge: { type: Boolean, default: true }
})

const el = ref(null)
const chart = shallowRef(null)
let ro = null

function render() {
  if (!chart.value || !props.option) return
  chart.value.setOption(props.option, { notMerge: props.notMerge, lazyUpdate: true })
}

onMounted(() => {
  chart.value = echarts.init(el.value)
  render()
  ro = new ResizeObserver(() => chart.value && chart.value.resize())
  ro.observe(el.value)
})

onBeforeUnmount(() => {
  ro && ro.disconnect()
  chart.value && chart.value.dispose()
})

watch(() => props.option, render, { deep: true })

defineExpose({ chart })
</script>
