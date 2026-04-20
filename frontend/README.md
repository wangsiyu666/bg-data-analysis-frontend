# TeleCompass 智能运营系统 - 前端

基于 Vue 3 + Vite + Element Plus + ECharts 开发的前端工程。

## 技术栈

- Vue 3.5 + Vite 5
- Element Plus（按需自动引入）
- ECharts 5
- Pinia、Vue Router 4
- Axios（统一请求封装 + mock 兜底）
- CountUp.js（数字滚动动画）

## 页面

| 路由             | 页面     | 数据来源 |
| ---------------- | -------- | -------- |
| `/dashboard`     | 首页     | 写死     |
| `/segment`       | 客群分析 | 接口     |
| `/product-ops`   | 产品运营 | 接口     |
| `/customer-ops`  | 客群运营 | 接口     |
| `/evaluation`    | 运营评估 | 写死     |

## 开始

```bash
npm install
npm run dev
```

默认 `.env.development` 开启了 mock 模式（`VITE_USE_MOCK=true`），所有接口由前端 mock 数据返回，页面可直接体验完整效果。

## 接口切换到真实后端

修改 `.env.development`：

```
VITE_USE_MOCK=false
VITE_MOCK_FALLBACK=false
VITE_API_BASE=/api     # 或真实地址
```

`VITE_MOCK_FALLBACK=true` 时，真实请求失败会自动回退到 mock（开发调试方便）。

`vite.config.js` 中已配置 `/api` 代理到 `http://localhost:8080`，后端变更修改这里即可。

## 预留接口一览

### 客群分析 `src/api/segment.js`

- `POST /api/segment/text-to-sql`  自然语言 → SQL
- `POST /api/segment/query`        执行 SQL 得到列与数据
- `POST /api/segment/save`         保存客群
- `POST /api/segment/multi-analysis` 多维诊断（生命周期/雷达/条形/诊断表）
- `GET  /api/segment/list`         已保存客群列表

### 产品运营 / 客群运营 `src/api/product.js` & `src/api/strategy.js`

- `POST /api/product/recommend`               助手推荐 TOP4 产品
- `POST /api/product/search`                  关键词搜索产品
- `POST /api/product/recommend-by-segment`    按已圈客群推荐产品（客群运营页专用）
- `POST /api/segment/by-condition`            口径（特征组合）圈选
- `POST /api/segment/seed-expand`             种子扩散
- `POST /api/segment/by-product`              按产品圈选客群
- `POST /api/segment/upload`                  文件上传解析客群
- `POST /api/strategy/generate`               策略生成智能体
- `POST /api/strategy/execute`                策略执行（渠道/话术/频率/时刻）
- `POST /api/strategy/predict`                策略效果预测（P-CVR / P-ROI / P-RR）
- `POST /api/strategy/publish`                策略发布

## 目录结构

```
src/
├── api/          # axios 实例、各接口、mock/
├── components/   # 通用组件 (EChart / CountNumber / KpiCard / ChannelCard / ops/*)
├── layout/       # BasicLayout / TopBar / SideMenu
├── mock/         # 页面 1/5 的写死数据
├── router/       # 路由定义
├── stores/       # Pinia 全局状态（loading、已保存客群）
├── styles/       # 全局样式变量
├── views/        # 5 个页面
├── App.vue
└── main.js
```
