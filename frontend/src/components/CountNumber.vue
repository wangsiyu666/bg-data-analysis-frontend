<template>
  <span ref="el">{{ display }}</span>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { CountUp } from 'countup.js'

const props = defineProps({
  end: { type: Number, required: true },
  decimals: { type: Number, default: 0 },
  duration: { type: Number, default: 1.2 },
  prefix: { type: String, default: '' },
  suffix: { type: String, default: '' },
  useGrouping: { type: Boolean, default: true }
})

const el = ref(null)
const display = ref('0')
let instance = null

function init() {
  instance = new CountUp(el.value, props.end, {
    decimalPlaces: props.decimals,
    duration: props.duration,
    prefix: props.prefix,
    suffix: props.suffix,
    useGrouping: props.useGrouping,
    separator: ','
  })
  if (!instance.error) instance.start()
  else display.value = String(props.end)
}

onMounted(() => {
  init()
})

watch(() => props.end, (v) => {
  if (instance) instance.update(v)
})
</script>
