<template>
  <div class="assistant-bar">
    <div class="ab-head">你好！我是你的运营小助手</div>
    <div class="ab-body">
      <textarea
        v-model="inner"
        rows="2"
        :placeholder="placeholder"
      />
      <button class="ab-btn" :disabled="loading" @click="handleClick">
        {{ loading ? '生成中...' : '开始分析' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  placeholder: {
    type: String,
    default: '请说明您运营的目标、运营的产品特征等信息，然后由运营小助手会推荐合适的产品和客群。'
  },
  loading: Boolean
})

const emit = defineEmits(['update:modelValue', 'analyze'])

const inner = ref(props.modelValue)
watch(inner, (v) => emit('update:modelValue', v))
watch(() => props.modelValue, (v) => (inner.value = v))

function handleClick() {
  emit('analyze', inner.value)
}
</script>

<style lang="scss" scoped>
.assistant-bar {
  background: #e9f1fb;
  border: 1px solid #b6d2ef;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}
.ab-head {
  background: #1e6ecf;
  color: #fff;
  font-size: 15px;
  font-weight: 700;
  padding: 10px 18px;
}
.ab-body {
  position: relative;
  padding: 14px 18px 16px;
  textarea {
    width: 100%;
    min-height: 48px;
    padding: 8px 10px;
    background: transparent;
    border: none;
    outline: none;
    resize: none;
    font-size: 13px;
    color: #103a70;
    line-height: 1.6;
    &::placeholder {
      color: #5a7ea8;
    }
  }
}
.ab-btn {
  position: absolute;
  right: 16px;
  bottom: 12px;
  background: #1e6ecf;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 6px 22px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
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
</style>
