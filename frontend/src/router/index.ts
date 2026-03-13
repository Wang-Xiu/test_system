import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import BasicLayout from '@/layout/BasicLayout.vue'

const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    component: BasicLayout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/Index.vue'),
        meta: { title: '数据看板' }
      },
      {
        path: 'projects',
        name: 'ProjectList',
        component: () => import('@/views/project/ProjectList.vue'),
        meta: { title: '项目管理' }
      },
      {
        path: 'projects/:id',
        name: 'ProjectDetail',
        component: () => import('@/views/project/ProjectDetail.vue'),
        meta: { title: '项目详情' }
      },
      {
        path: 'accounts',
        name: 'AccountList',
        component: () => import('@/views/account/AccountList.vue'),
        meta: { title: '账号管理' }
      },
      {
        path: 'cases',
        name: 'CaseList',
        component: () => import('@/views/case/CaseList.vue'),
        meta: { title: '测试用例管理' }
      },
      {
        path: 'tasks',
        name: 'TaskList',
        component: () => import('@/views/task/TaskList.vue'),
        meta: { title: '任务执行记录' }
      },
      {
        path: 'suites',
        name: 'SuiteList',
        component: () => import('@/views/suite/SuiteList.vue'),
        meta: { title: '测试套件' }
      },
      {
        path: 'suites/:id',
        name: 'SuiteEdit',
        component: () => import('@/views/suite/SuiteEdit.vue'),
        meta: { title: '编辑套件' }
      },
      {
        path: 'schedules',
        name: 'ScheduleList',
        component: () => import('@/views/schedule/ScheduleList.vue'),
        meta: { title: '定时任务' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
