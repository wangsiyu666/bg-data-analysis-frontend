<template>
  <div class="generate-bar">
    <div class="gb-box">
      <textarea
        v-model="inner"
        rows="2"
        placeholder="小助手一直都在，有其他关于策略和运营信息可以这里继续补充"
      />
    </div>
    <div class="gb-right">
      <div class="gb-step">{{ stepLabel }}</div>
      <button class="gb-btn" :disabled="loading" @click="handleClick">
        {{ loading ? '生成中...' : '生成策略' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  loading: Boolean,
  stepLabel: { type: String, default: 'setp3' }
})
const emit = defineEmits(['update:modelValue', 'generate'])

const inner = ref(props.modelValue)
watch(inner, (v) => emit('update:modelValue', v))
watch(() => props.modelValue, (v) => (inner.value = v))

function handleClick() {
  emit('generate', inner.value)
}
</script>

<style lang="scss" scoped>
.generate-bar {
  display: flex;
  gap: 14px;
  align-items: stretch;
  background: transparent;
  padding: 6px 0;
}
.gb-box {
  flex: 1;
  background: #f5f7fa;
  border: 1px dashed #c7d3e6;
  border-radius: 6px;
  padding: 10px 14px;
  textarea {
    width: 100%;
    min-height: 48px;
    background: transparent;
    border: none;
    outline: none;
    resize: none;
    font-size: 13px;
    color: #606266;
    &::placeholder {
      color: #a8adb5;
    }
  }
}
.gb-right {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  min-width: 140px;
}
.gb-step {
  font-size: 12px;
  color: #909399;
}
.gb-btn {
  background: #f2a443;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 10px 32px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(242, 164, 67, 0.35);
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
