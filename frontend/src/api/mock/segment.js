// 客群分析接口 Mock 数据

function rand(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min
}

export const mockSegment = {
  textToSql({ text } = {}) {
    const keyword = (text || '').trim()
    let sql = 'select city_id,user_online,sex_id,count(*) from user_behavior where arpu=80;'
    if (keyword.includes('ARPU>89') || keyword.includes('arpu>89')) {
      sql = 'select city_id, sex_id, age, count(*) from user_behavior where arpu>89 group by city_id, sex_id, age;'
    } else if (keyword.includes('高价值')) {
      sql = 'select city_id, sex_id, count(*) from user_behavior where arpu>120 and is_rhtc=1 group by city_id, sex_id;'
    } else if (keyword) {
      sql = `select city_id, user_online, sex_id, count(*) from user_behavior where /* ${keyword} */ arpu=80 group by city_id, user_online, sex_id;`
    }
    return { sql }
  },

  query({ sql } = {}) {
    const rows = []
    const cities = ['北京', '上海', '广州', '深圳', '成都', '武汉', '南京', '杭州', '西安', '郑州']
    const sexMap = ['未知', '男', '女']
    for (let i = 0; i < 20; i++) {
      rows.push({
        city_id: cities[i % cities.length],
        user_online: rand(1, 120),
        sex_id: sexMap[rand(1, 2)],
        'count(*)': rand(50, 5000)
      })
    }
    return {
      columns: [
        { prop: 'city_id', label: '城市' },
        { prop: 'user_online', label: '在网时长(月)' },
        { prop: 'sex_id', label: '性别' },
        { prop: 'count(*)', label: '用户数' }
      ],
      rows,
      total: 658,
      sql
    }
  },

  save({ name, condition } = {}) {
    return { id: Date.now(), name, condition }
  },

  multiAnalysis({ sql } = {}) {
    return {
      lifecycle: [
        { key: 'inflow', label: '入网期', desc: '在网时长<6个月', value: 35.18 },
        { key: 'growth', label: '成长期', desc: '在网时长<18个月', value: 42.16 },
        { key: 'mature', label: '成熟期', desc: '在网时长<36个月', value: 35.21 },
        { key: 'churn', label: '异动期', desc: '在网时长<60个月', value: 16.82 },
        { key: 'leave', label: '离网期', desc: '在网时长>60个月', value: 23.78 }
      ],
      valueBar: {
        categories: ['入网期', '成长期', '成熟期', '异动期', '离网期'],
        high: [345, 758, 234, 112, 34],
        low: [278, 432, 189, 76, 22]
      },
      radar: {
        indicator: [
          { name: '粘性', max: 100 },
          { name: '价值', max: 100 },
          { name: '竞抢', max: 100 },
          { name: '感知', max: 100 },
          { name: '活跃', max: 100 },
          { name: '传播', max: 100 }
        ],
        value: [85, 70, 62, 78, 92, 45]
      },
      diagnosisTable: [
        { period: '入网期', sticky: 85, value: 70, compete: 62, sense: 78, active: 92, spread: 45 },
        { period: '成长期', sticky: 78, value: 82, compete: 70, sense: 80, active: 88, spread: 55 },
        { period: '成熟期', sticky: 90, value: 85, compete: 76, sense: 82, active: 85, spread: 60 },
        { period: '异动期', sticky: 65, value: 60, compete: 58, sense: 62, active: 70, spread: 42 },
        { period: '离网期', sticky: 40, value: 35, compete: 30, sense: 40, active: 38, spread: 22 }
      ],
      sql
    }
  },

  list() {
    return [
      { id: 1, name: '高ARPU城市白领', condition: "FROM user_behavior WHERE arpu>89 AND user_online>=18" },
      { id: 2, name: '潜力新用户', condition: "FROM user_behavior WHERE user_online<6 AND prepay_bal>40" },
      { id: 3, name: '流失预警用户', condition: "FROM user_behavior WHERE user_online>=36 AND is_ywsk=1" }
    ]
  }
}
