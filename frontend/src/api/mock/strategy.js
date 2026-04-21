// 策略/渠道/话术/效果预测 Mock 数据

function rand(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min
}

export const mockStrategy = {
  segmentByCondition({ name, condition } = {}) {
    const count = rand(1200000, 15800000)
    const audienceIds = Array.from({ length: Math.min(20, count) }, (_, i) => `user_${i + 1}`)
    return { count, name, condition, audienceIds }
  },

  seedExpand({ seeds = '', target = 100000 } = {}) {
    const count = Math.min(Number(target) || 100000, 20000000)
    const audienceIds = Array.from({ length: Math.min(20, count) }, (_, i) => `user_seed_${i + 1}`)
    return { count, expanded: count, audienceIds }
  },

  segmentByProduct({ productIds = [], target = 100000 } = {}) {
    const count = Math.min(Number(target) || 100000, 20000000) * Math.max(1, productIds.length)
    const total = Math.min(count, 25000000)
    const audienceIds = Array.from({ length: Math.min(20, total) }, (_, i) => `user_prod_${i + 1}`)
    return { count: total, audienceIds }
  },

  uploadUsers() {
    const count = rand(5000, 200000)
    const audienceIds = Array.from({ length: Math.min(20, count) }, (_, i) => `user_up_${i + 1}`)
    return { count, audienceIds }
  },

  generate({ text, products = [], segment } = {}) {
    const pNames = products.map((p) => p.name).join(',')
    return {
      id: 'S' + Date.now(),
      name: `AI智能${products[0]?.category || '套餐'}精准运营策略`,
      categories: ['挽留', '升级', '交叉销售'],
      condition: segment?.condition || '若无圈选客群此处为空',
      descDetail: {
        desc: `基于AI智能体分析，面向${segment?.name || '目标客群'}推荐${pNames || '主打产品'}，提升ARPU和留存。`,
        paymentMethod: '首月免费，次月起按月扣费，支持话费/余额/微信支付',
        relatedProducts: pNames,
        benefits: '首月0元体验+定向流量10GB+视频会员1个月',
        validity: '2026-01-01 至 2026-12-31'
      },
      expectedArpuLift: (Math.random() * 30 + 10).toFixed(1) + '/月',
      segmentSize: segment?.count || 0,
      userText: text
    }
  },

  execute({ strategyId } = {}) {
    return {
      strategyId,
      channels: [
        { id: 'app', name: 'APP推送', icon: 'Cellphone', rank: 1 },
        { id: 'sms', name: '短信', icon: 'ChatDotRound', rank: 2 }
      ],
      scripts: {
        app: [
          {
            id: 'app-1',
            title: '版本A - 利益吸引',
            content: '【尊享福利】识别到您的5G使用已达上限，升级128档套餐首月0元，流量翻倍不限速，点此一键升级。'
          },
          {
            id: 'app-2',
            title: '版本B - 场景化',
            content: '【贴心提醒】您最近经常使用视频/会议应用，128档专享大流量+视频会员，立即体验更流畅的5G生活。'
          }
        ],
        sms: [
          {
            id: 'sms-1',
            title: '版本A - 简洁直达',
            content: '【电信】尊敬的用户，您可升级5G 128档套餐，首月0元，流量翻倍，回复"Y"立即办理。TD退订。'
          },
          {
            id: 'sms-2',
            title: '版本B - 权益突出',
            content: '【电信】升128档送视频会员+10GB定向流量，点击 t.cn/xxx 办理，首月免费。TD退订。'
          }
        ],
        outcall: [
          { id: 'oc-1', title: '版本A - 标准话术', content: '您好，为您推荐专享升级方案...' },
          { id: 'oc-2', title: '版本B - 情景话术', content: '您好，针对您的使用情况推荐...' }
        ]
      },
      frequency: { level: '标准', times: 2, options: [{ label: '保守', times: 1 }, { label: '标准', times: 2 }, { label: '激进', times: 4 }] },
      bestTime: { weekdays: [2, 4, 6], label: '周二 / 周四 / 周六 19:00 - 21:00 转化率最高' },
      planId: 'PLAN_mock_' + Date.now(),
      scriptIds: ['SCR_1', 'SCR_2', 'SCR_3', 'SCR_4']
    }
  },

  predict({ strategyId, dimension = 'region' } = {}) {
    let categories = []
    if (dimension === 'region') categories = ['北京', '上海', '广州', '深圳', '成都', '武汉']
    else if (dimension === 'arpu') categories = ['0-29', '30-59', '60-89', '90-119', '120-149', '150+']
    else categories = ['18-24', '25-34', '35-44', '45-54', '55+']

    const pCvr = { from: 0.142, to: 2.1 }
    const pRoi = { from: 1.8, to: 4.0 }
    const pRr = { from: 0.925, to: 2.0 }

    const makeSeries = (base) => categories.map(() => +(base + Math.random() * base).toFixed(2))
    return {
      strategyId,
      dimension,
      categories,
      pCvr,
      pRoi,
      pRr,
      series: [
        { name: 'P-CVR(%)', data: makeSeries(1.2) },
        { name: 'P-ROI', data: makeSeries(2.5) },
        { name: 'P-RR(%)', data: makeSeries(1.3) }
      ]
    }
  },

  publish(payload) {
    return { ok: true, id: 'PUB' + Date.now(), payload }
  }
}
