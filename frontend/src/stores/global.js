import { defineStore } from 'pinia'

export const useGlobalStore = defineStore('global', {
  state: () => ({
    loading: false,
    loadingText: '数据加载中，请稍候...'
  }),
  actions: {
    showLoading(text) {
      this.loadingText = text || '数据加载中，请稍候...'
      this.loading = true
    },
    hideLoading() {
      this.loading = false
    }
  }
})
