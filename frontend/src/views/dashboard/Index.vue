<template>
  <div class="dashboard-container">
    <div class="filter-bar" style="margin-bottom: 15px;">
      <el-select v-model="projectFilter" placeholder="按项目筛选" clearable style="width: 200px;" @change="fetchAll">
        <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
      </el-select>
    </div>

    <el-row :gutter="20">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-title">总用例数</div>
          <div class="stat-value">{{ stats.total_cases }}</div>
          <el-icon class="stat-icon" color="#409EFF"><Document /></el-icon>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-title">总任务数</div>
          <div class="stat-value">{{ stats.total_tasks }}</div>
          <el-icon class="stat-icon" color="#E6A23C"><Monitor /></el-icon>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-title">今日任务数</div>
          <div class="stat-value">{{ stats.today_tasks }}</div>
          <el-icon class="stat-icon" color="#67C23A"><Calendar /></el-icon>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-title">任务成功率</div>
          <div class="stat-value">{{ stats.success_rate }}%</div>
          <el-icon class="stat-icon" color="#F56C6C"><DataLine /></el-icon>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="mt-20">
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>执行趋势（近7天）</span>
            </div>
          </template>
          <div ref="trendChartRef" style="height: 300px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="mt-20">
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header"><span>最近执行任务</span></div>
          </template>
          <el-table :data="stats.recent_tasks" style="width: 100%">
            <el-table-column prop="id" label="任务ID" width="100" />
            <el-table-column prop="status" label="状态">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间">
              <template #default="{ row }">{{ new Date(row.created_at).toLocaleString() }}</template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { Document, Monitor, Calendar, DataLine } from '@element-plus/icons-vue'
import request from '@/utils/request'
import { getProjects, type Project } from '@/api/project'
import * as echarts from 'echarts'

interface DashboardStats {
  total_cases: number
  total_tasks: number
  today_tasks: number
  success_rate: number
  recent_tasks: any[]
}

interface TrendItem {
  date: string
  success: number
  failed: number
  error: number
}

const projects = ref<Project[]>([])
const projectFilter = ref<number | undefined>(undefined)
const trendChartRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null

const stats = ref<DashboardStats>({
  total_cases: 0,
  total_tasks: 0,
  today_tasks: 0,
  success_rate: 0,
  recent_tasks: []
})

const fetchAll = async () => {
  const params: any = {}
  if (projectFilter.value) params.project_id = projectFilter.value

  const [statsRes, trendsRes] = await Promise.all([
    request.get<any, DashboardStats>('/dashboard/stats', { params }),
    request.get<any, TrendItem[]>('/dashboard/trends', { params: { ...params, days: 7 } }),
  ])
  stats.value = statsRes
  renderTrendChart(trendsRes)
}

const renderTrendChart = (trends: TrendItem[]) => {
  if (!trendChartRef.value) return
  if (!chartInstance) {
    chartInstance = echarts.init(trendChartRef.value)
  }
  chartInstance.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['成功', '失败', '错误'] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: trends.map(t => t.date) },
    yAxis: { type: 'value', minInterval: 1 },
    series: [
      { name: '成功', type: 'line', data: trends.map(t => t.success), itemStyle: { color: '#67C23A' }, smooth: true },
      { name: '失败', type: 'line', data: trends.map(t => t.failed), itemStyle: { color: '#F56C6C' }, smooth: true },
      { name: '错误', type: 'line', data: trends.map(t => t.error), itemStyle: { color: '#E6A23C' }, smooth: true },
    ],
  })
}

onMounted(async () => {
  projects.value = await getProjects()
  await nextTick()
  fetchAll()
})

const getStatusType = (status: string) => {
  const map: Record<string, string> = { pending: 'info', running: 'warning', success: 'success', failed: 'danger', error: 'danger' }
  return map[status] || 'info'
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = { pending: '等待中', running: '执行中', success: '成功', failed: '失败', error: '系统错误' }
  return map[status] || status
}
</script>

<style scoped>
.dashboard-container { padding: 20px; }
.stat-card { position: relative; height: 120px; }
.stat-title { font-size: 14px; color: #909399; margin-bottom: 10px; }
.stat-value { font-size: 28px; font-weight: bold; color: #303133; }
.stat-icon { position: absolute; right: 20px; top: 30px; font-size: 48px; opacity: 0.8; }
.mt-20 { margin-top: 20px; }
</style>
