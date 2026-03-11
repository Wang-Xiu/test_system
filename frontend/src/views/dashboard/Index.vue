<template>
  <div class="dashboard-container">
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
              <span>最近执行任务</span>
            </div>
          </template>
          <el-table :data="stats.recent_tasks" style="width: 100%">
            <el-table-column prop="id" label="任务ID" width="100" />
            <el-table-column prop="status" label="状态">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间">
              <template #default="{ row }">
                {{ new Date(row.created_at).toLocaleString() }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Document, Monitor, Calendar, DataLine } from '@element-plus/icons-vue'
import request from '@/utils/request'

interface DashboardStats {
  total_cases: number
  total_tasks: number
  today_tasks: number
  success_rate: number
  recent_tasks: any[]
}

const stats = ref<DashboardStats>({
  total_cases: 0,
  total_tasks: 0,
  today_tasks: 0,
  success_rate: 0,
  recent_tasks: []
})

const fetchStats = async () => {
  try {
    const res = await request.get<any, DashboardStats>('/dashboard/stats')
    stats.value = res
  } catch (error) {
    console.error('Failed to fetch dashboard stats', error)
  }
}

onMounted(() => {
  fetchStats()
})

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    pending: 'info',
    running: 'warning',
    success: 'success',
    failed: 'danger',
    error: 'danger'
  }
  return map[status] || 'info'
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    pending: '等待中',
    running: '执行中',
    success: '成功',
    failed: '失败',
    error: '系统错误'
  }
  return map[status] || status
}
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
}

.stat-card {
  position: relative;
  height: 120px;
}

.stat-title {
  font-size: 14px;
  color: #909399;
  margin-bottom: 10px;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.stat-icon {
  position: absolute;
  right: 20px;
  top: 30px;
  font-size: 48px;
  opacity: 0.8;
}

.mt-20 {
  margin-top: 20px;
}
</style>
