<template>
  <div class="page customer-ops">
    <AssistantBar
      v-model="assistantText"
      :loading="assistantLoading"
      @analyze="handleAnalyze"
    />
    <!-- 客群运营页：先圈客群，后选产品 -->
    <SegmentSelector
      :selected-products="selectedProducts"
      :show-product-recommend="false"
      step-label="setp1"
      @change="handleSegmentChange"
      class="block-mt"
    />
    <ProductSelector
      v-model="selectedProducts"
      :products="products"
      :enable-segment-recommend="true"
      :current-segment="{ name: segmentInfo.conditionName, count: segmentInfo.total }"
      step-label="setp2"
      @update:products="(list) => (products = list)"
      class="block-mt"
    />
    <GenerateBar
      v-model="generateText"
      :loading="generateLoading"
      step-label="setp3"
      @generate="handleGenerate"
      class="block-mt"
    />
    <StrategyArea
      :strategy-data="strategyData"
      :execution-data="executionData"
      :predict-data="predictData"
      :selected-products="selectedProducts"
      :segment-count="segmentInfo.total"
      publish-label="发布策略"
      class="block-mt"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import AssistantBar from '@/components/ops/AssistantBar.vue'
import ProductSelector from '@/components/ops/ProductSelector.vue'
import SegmentSelector from '@/components/ops/SegmentSelector.vue'
import GenerateBar from '@/components/ops/GenerateBar.vue'
import StrategyArea from '@/components/ops/StrategyArea.vue'
import { recommendProducts, searchProducts } from '@/api/product'
import { generateStrategy, executeStrategy, predictStrategy } from '@/api/strategy'

const assistantText = ref('')
const assistantLoading = ref(false)
const products = ref([])
const selectedProducts = ref([])

const segmentInfo = reactive({ total: 0, parts: [], conditionName: '', condition: '' })
const generateText = ref('')
const generateLoading = ref(false)

const strategyData = ref(null)
const executionData = ref(null)
const predictData = ref(null)

function handleSegmentChange(info) {
  segmentInfo.total = info.total
  segmentInfo.parts = info.parts
  segmentInfo.conditionName = info.conditionName
  segmentInfo.condition = info.condition
}

async function handleAnalyze(text) {
  if (!text?.trim()) {
    ElMessage.warning('请先输入运营目标/客群特征')
    return
  }
  assistantLoading.value = true
  try {
    const res = await recommendProducts({ text })
    products.value = res
    ElMessage.success('已推荐 TOP4 产品')
  } finally {
    assistantLoading.value = false
  }
}

async function handleGenerate(text) {
  if (!segmentInfo.total) {
    ElMessage.warning('请先圈选客群')
    return
  }
  generateLoading.value = true
  try {
    const strategyRes = await generateStrategy({
      text: text || assistantText.value,
      products: selectedProducts.value,
      segment: {
        name: segmentInfo.conditionName,
        condition: segmentInfo.condition,
        count: segmentInfo.total
      }
    })
    strategyData.value = strategyRes
    const execRes = await executeStrategy({ strategyId: strategyRes.id })
    executionData.value = execRes
    const predRes = await predictStrategy({ strategyId: strategyRes.id, dimension: 'region' })
    predictData.value = predRes
    ElMessage.success('策略已生成')
  } finally {
    generateLoading.value = false
  }
}

onMounted(async () => {
  try {
    const res = await searchProducts({ keyword: '' })
    products.value = res
  } catch (e) {}
})
</script>

<style lang="scss" scoped>
.page {
  padding-bottom: 30px;
}
.block-mt {
  margin-top: 14px;
}
</style>
