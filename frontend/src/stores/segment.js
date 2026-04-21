import { defineStore } from 'pinia'

// 客群/运营过程中的共享状态
export const useSegmentStore = defineStore('segment', {
  state: () => ({
    // 客群分析页保存后的客群列表（来自后端 /audience/save 等）
    savedSegments: [],

    // 当前正在操作的客群 audience_ids（圈选结果聚合）
    // 供产品推荐、策略生成、执行优化等后续接口使用
    currentAudienceIds: [],

    // 最近一次策略生成结果
    currentStrategyId: '',

    // 最近一次执行优化产物
    currentPlanId: '',
    currentScriptIds: []
  }),
  actions: {
    addSegment(segment) {
      const exist = this.savedSegments.find((s) => s.name === segment.name)
      if (exist) {
        Object.assign(exist, segment)
      } else {
        this.savedSegments.push({
          id: segment.id || Date.now(),
          createdAt: new Date().toLocaleString(),
          ...segment
        })
      }
    },
    setList(list) {
      this.savedSegments = list || []
    },
    setAudienceIds(ids) {
      this.currentAudienceIds = Array.isArray(ids) ? ids : []
    },
    setStrategyId(id) {
      this.currentStrategyId = id || ''
    },
    setExecutionArtifacts({ planId, scriptIds } = {}) {
      this.currentPlanId = planId || ''
      this.currentScriptIds = scriptIds || []
    },
    reset() {
      this.currentAudienceIds = []
      this.currentStrategyId = ''
      this.currentPlanId = ''
      this.currentScriptIds = []
    }
  }
})
