<template>
  <div class="task-list">
    <div class="toolbar">
      <el-button type="primary" @click="fetchTasks">
        <el-icon><Refresh /></el-icon>刷新
      </el-button>
    </div>

    <el-table
      v-loading="loading"
      :data="tasks"
      style="width: 100%"
      border
    >
      <el-table-column prop="id" label="任务ID" width="80" />
      <el-table-column prop="case_ids" label="用例IDs" width="150" show-overflow-tooltip />
      <el-table-column prop="status" label="状态" width="120">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column prop="finished_at" label="完成时间" width="180">
        <template #default="{ row }">
          {{ row.finished_at ? formatDate(row.finished_at) : '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="error_msg" label="错误信息" show-overflow-tooltip />
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button 
            v-if="row.status === 'success' || row.status === 'failed'"
            size="small" 
            type="primary" 
            link 
            @click="viewReport(row)"
          >
            查看报告
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { getTasks, type TestTask } from '@/api/task'

const loading = ref(false)
const tasks = ref<TestTask[]>([])
let timer: number | null = null

const fetchTasks = async () => {
  loading.value = true
  try {
    tasks.value = await getTasks()
  } catch (error) {
    // Error handled by interceptor
  } finally {
    loading.value = false
  }
}

// Auto refresh every 5 seconds
onMounted(() => {
  fetchTasks()
  timer = window.setInterval(() => {
    // Only refresh silently if not already loading
    if (!loading.value) {
      getTasks().then(res => {
        tasks.value = res
      }).catch(() => {})
    }
  }, 5000)
})

onUnmounted(() => {
  if (timer) {
    clearInterval(timer)
  }
})

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString()
}

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

const viewReport = (row: TestTask) => {
  if (row.report_path) {
    // Open report in new tab via backend static file service
    window.open(`http://localhost:8006${row.report_path}`, '_blank')
  } else {
    alert('报告路径不存在')
  }
}
</script>

<style scoped>
.task-list {
  background: #fff;
  padding: 20px;
  border-radius: 4px;
}

.toolbar {
  margin-bottom: 20px;
}
</style>
