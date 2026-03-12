<template>
  <div class="suite-list">
    <div class="toolbar">
      <el-select v-model="projectFilter" placeholder="按项目筛选" clearable style="width: 200px; margin-right: 10px;" @change="fetchSuites">
        <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
      </el-select>
      <el-button type="primary" @click="handleAdd">新建套件</el-button>
    </div>

    <el-table :data="suites" border style="width: 100%">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="套件名称" />
      <el-table-column prop="description" label="描述" show-overflow-tooltip />
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">{{ new Date(row.created_at).toLocaleString() }}</template>
      </el-table-column>
      <el-table-column label="操作" width="300" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="success" link @click="handleRun(row)">执行</el-button>
          <el-button size="small" type="primary" link @click="$router.push(`/suites/${row.id}`)">编辑用例</el-button>
          <el-popconfirm title="确定删除？" @confirm="handleDelete(row)">
            <template #reference>
              <el-button size="small" type="danger" link>删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新建套件弹窗 -->
    <el-dialog v-model="dialogVisible" title="新建套件" width="500px">
      <el-form :model="formData" label-width="80px">
        <el-form-item label="项目" required>
          <el-select v-model="formData.project_id" style="width: 100%;" placeholder="选择项目">
            <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="名称" required>
          <el-input v-model="formData.name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="formData.description" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitCreate">确定</el-button>
      </template>
    </el-dialog>

    <!-- 执行选环境弹窗 -->
    <el-dialog v-model="runDialogVisible" title="选择执行环境" width="400px">
      <el-form label-width="60px">
        <el-form-item label="环境">
          <el-select v-model="runEnvId" placeholder="选择环境（可选）" clearable style="width: 100%;">
            <el-option v-for="env in runEnvs" :key="env.id" :label="env.name" :value="env.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="runDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmRun">执行</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getSuites, createSuite, deleteSuite, runSuite, type TestSuite } from '@/api/suite'
import { getProjects, type Project } from '@/api/project'
import { getEnvironments, type Environment } from '@/api/environment'

const projects = ref<Project[]>([])
const suites = ref<TestSuite[]>([])
const projectFilter = ref<number | undefined>(undefined)
const dialogVisible = ref(false)
const formData = ref({ project_id: 0, name: '', description: '' })

const runDialogVisible = ref(false)
const runEnvId = ref<number | undefined>(undefined)
const runEnvs = ref<Environment[]>([])
const runningSuiteId = ref(0)

const fetchSuites = async () => {
  suites.value = await getSuites(projectFilter.value)
}

onMounted(async () => {
  projects.value = await getProjects()
  fetchSuites()
})

const handleAdd = () => {
  formData.value = { project_id: projectFilter.value || 0, name: '', description: '' }
  dialogVisible.value = true
}

const submitCreate = async () => {
  if (!formData.value.project_id || !formData.value.name) {
    ElMessage.warning('请填写项目和名称')
    return
  }
  await createSuite({ ...formData.value, case_ids: [] })
  ElMessage.success('创建成功')
  dialogVisible.value = false
  fetchSuites()
}

const handleDelete = async (row: TestSuite) => {
  await deleteSuite(row.id)
  ElMessage.success('删除成功')
  fetchSuites()
}

const handleRun = async (row: TestSuite) => {
  runningSuiteId.value = row.id
  runEnvId.value = undefined
  runEnvs.value = await getEnvironments(row.project_id)
  runDialogVisible.value = true
}

const confirmRun = async () => {
  const res = await runSuite(runningSuiteId.value, runEnvId.value)
  ElMessage.success(res.message)
  runDialogVisible.value = false
}
</script>

<style scoped>
.suite-list { background: #fff; padding: 20px; border-radius: 4px; }
.toolbar { margin-bottom: 20px; display: flex; align-items: center; }
</style>
