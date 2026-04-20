import { createRouter, createWebHashHistory } from 'vue-router'
import BasicLayout from '@/layout/BasicLayout.vue'

const routes = [
  {
    path: '/',
    component: BasicLayout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/Index.vue'),
        meta: { title: '首页', breadcrumb: ['首页'] }
      },
      {
        path: 'segment',
        name: 'Segment',
        component: () => import('@/views/segment/Index.vue'),
        meta: { title: '客群分析', breadcrumb: ['首页', '客群分析'] }
      },
      {
        path: 'product-ops',
        name: 'ProductOps',
        component: () => import('@/views/product-ops/Index.vue'),
        meta: { title: '产品运营', breadcrumb: ['首页', '产品运营'] }
      },
      {
        path: 'customer-ops',
        name: 'CustomerOps',
        component: () => import('@/views/customer-ops/Index.vue'),
        meta: { title: '客群运营', breadcrumb: ['首页', '客群运营'] }
      },
      {
        path: 'evaluation',
        name: 'Evaluation',
        component: () => import('@/views/evaluation/Index.vue'),
        meta: {
          title: '运营评估',
          breadcrumb: ['首页', '客服分析', '产品运营', '客服运营', '运营评估']
        }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

export default router
