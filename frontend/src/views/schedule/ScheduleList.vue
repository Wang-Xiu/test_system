<template>
  <div class="schedule-list">
    <div class="toolbar">
      <el-select v-model="projectFilter" placeholder="按项目筛选" clearable style="width: 200px; margin-right: 10px;" @change="fetchSchedules">
        <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
      </el-select>
      <el-button type="primary" @click="handleAdd">新建定时任务</el-button>
    </div>

    <el-table :data="schedules" border style="width: 100%">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="cron_expression" label="Cron 表达式" width="150" />
      <el-table-column prop="is_active" label="状态" width="100">
        <template #default="{ row }">
          <el-switch :model-value="row.is_active" @change="handleToggle(row)" />
        </template>
      </el-table-column>
      <el-table-column prop="last_run_at" label="上次执行" width="180">
        <template #default="{ row }">
          {{ row.last_run_at ? new Date(row.last_run_at).toLocaleString() : '-' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-popconfirm title="确定删除？" @confirm="handleDelete(row)">
            <template #reference>
              <el-button size="small" type="danger" link>删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" title="新建定时任务" width="500px">
      <el-form :model="formData" label-width="90px">
        <el-form-item label="项目" required>
          <el-select v-model="formData.project_id" style="width: 100%;" @change="onProjectChange">
            <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="名称" required>
          <el-input v-model="formData.name" />
        </el-form-item>
        <el-form-item label="环境" required>
          <el-select v-model="formData.environment_id" style="width: 100%;">
            <el-option v-for="env in envOptions" :key="env.id" :label="env.name" :value="env.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="套件" required>
          <el-select v-model="formData.suite_id" style="width: 100%;">
            <el-option v-for="s in suiteOptions" :key="s.id" :label="s.name" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="Cron" required>
          <el-input v-model="formData.cron_expression" placeholder="如 0 9 * * 1-5 (工作日9点)" />
          <div style="font-size: 12px; color: #909399; margin-top: 4px;">
            格式: 分 时 日 月 周 (5段标准cron)
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitCreate">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getSchedules, createSchedule, toggleSchedule, deleteSchedule, type Schedule } from '@/api/schedule'
import { getProjects, type Project } from '@/api/project'
import { getEnvironments, type Environment } from '@/api/environment'
import { getSuites, type TestSuite } from '@/api/suite'

const projects = ref<Project[]>([])
const schedules = ref<Schedule[]>([])
const projectFilter = ref<number | undefined>(undefined)
const dialogVisible = ref(false)
const formData = ref({ project_id: 0, name: '', environment_id: 0, suite_id: 0, cron_expression: '' })
const envOptions = ref<Environment[]>([])
const suiteOptions = ref<TestSuite[]>([])

const fetchSchedules = async () => {
  schedules.value = await getSchedules(projectFilter.value)
}

onMounted(async () => {
  projects.value = await getProjects()
  fetchSchedules()
})

const onProjectChange = async (pid: number) => {
  if (pid) {
    envOptions.value = await getEnvironments(pid)
    suiteOptions.value = await getSuites(pid)
  } else {
    envOptions.value = []
    suiteOptions.value = []
  }
}

const handleAdd = () => {
  formData.value = { project_id: projectFilter.value || 0, name: '', environment_id: 0, suite_id: 0, cron_expression: '' }
  if (formData.value.project_id) onProjectChange(formData.value.project_id)
  dialogVisible.value = true
}

const submitCreate = async () => {
  if (!formData.value.project_id || !formData.value.name || !formData.value.cron_expression) {
    ElMessage.warning('请填写必填字段')
    return
  }
  await createSchedule(formData.value)
  ElMessage.success('创建成功')
  dialogVisible.value = false
  fetchSchedules()
}

const handleToggle = async (row: Schedule) => {
  await toggleSchedule(row.id)
  fetchSchedules()
}

const handleDelete = async (row: Schedule) => {
  await deleteSchedule(row.id)
  ElMessage.success('删除成功')
  fetchSchedules()
}
</script>

<style scoped>
.schedule-list { background: #fff; padding: 20px; border-radius: 4px; }
.toolbar { margin-bottom: 20px; display: flex; align-items: center; }
</style>
