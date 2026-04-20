import { defineStore } from 'pinia'

export const useSegmentStore = defineStore('segment', {
  state: () => ({
    savedSegments: []
  }),
  actions: {
    addSegment(segment) {
      const exist = this.savedSegments.find((s) => s.name === segment.name)
      if (exist) {
        Object.assign(exist, segment)
      } else {
        this.savedSegments.push({
          id: Date.now(),
          createdAt: new Date().toLocaleString(),
          ...segment
        })
      }
    },
    setList(list) {
      this.savedSegments = list
    }
  }
})
