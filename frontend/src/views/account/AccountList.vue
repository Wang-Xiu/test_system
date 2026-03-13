<template>
  <div class="account-list">
    <div class="toolbar">
      <el-select v-model="projectFilter" placeholder="按项目筛选" clearable style="width: 200px; margin-right: 10px;" @change="fetchAccounts">
        <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
      </el-select>
      <el-button type="primary" @click="handleAdd">新建账号</el-button>
    </div>

    <el-table :data="accounts" border style="width: 100%">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="账号标识" />
      <el-table-column prop="username" label="用户名/UID" />
      <el-table-column prop="description" label="描述" show-overflow-tooltip />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 1 ? 'success' : 'danger'">{{ row.status === 1 ? '正常' : '禁用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">{{ new Date(row.created_at).toLocaleString() }}</template>
      </el-table-column>
      <el-table-column label="操作" width="300" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="success" link @click="handleRefresh(row)">刷新Token</el-button>
          <el-button size="small" type="primary" link @click="handleEdit(row)">编辑</el-button>
          <el-popconfirm title="确定删除？" @confirm="handleDelete(row)">
            <template #reference>
              <el-button size="small" type="danger" link>删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- 刷新 Token 选环境弹窗 -->
    <el-dialog v-model="refreshDialogVisible" title="选择环境" width="400px">
      <el-form label-width="60px">
        <el-form-item label="环境">
          <el-select v-model="refreshEnvId" placeholder="选择环境（可选，不选则为项目级）" clearable style="width: 100%;">
            <el-option v-for="env in environments" :key="env.id" :label="env.name" :value="env.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="refreshDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmRefresh" :loading="refreshing">确定刷新</el-button>
      </template>
    </el-dialog>

    <!-- 新建/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑账号' : '新建账号'" width="500px">
      <el-form :model="formData" label-width="100px">
        <el-form-item label="项目" required>
          <el-select v-model="formData.project_id" style="width: 100%;" placeholder="选择项目" :disabled="isEdit">
            <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="账号标识" required>
          <el-input v-model="formData.name" placeholder="如：测试主账号" />
        </el-form-item>
        <el-form-item label="用户名/UID" required>
          <el-input v-model="formData.username" placeholder="登录账号或UID" />
        </el-form-item>
        <el-form-item label="密码/凭证">
          <el-input v-model="formData.password" type="password" show-password placeholder="登录密码，可为空" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="formData.description" type="textarea" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="formData.status" :active-value="1" :inactive-value="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getAccounts, createAccount, updateAccount, deleteAccount, type TestAccount } from '@/api/account'
import { getProjects, type Project } from '@/api/project'
import { getEnvironments, type Environment } from '@/api/environment'
import request from '@/utils/request'

const projects = ref<Project[]>([])
const accounts = ref<TestAccount[]>([])
const projectFilter = ref<number | undefined>(undefined)

const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref(0)
const formData = ref({
  project_id: undefined as number | undefined,
  name: '',
  username: '',
  password: '',
  description: '',
  status: 1
})

const refreshDialogVisible = ref(false)
const refreshEnvId = ref<number | undefined>(undefined)
const environments = ref<Environment[]>([])
const currentRefreshAccount = ref<TestAccount | null>(null)
const refreshing = ref(false)

const fetchAccounts = async () => {
  accounts.value = await getAccounts(0, 1000, projectFilter.value)
}

onMounted(async () => {
  projects.value = await getProjects()
  fetchAccounts()
})

const handleAdd = () => {
  isEdit.value = false
  formData.value = {
    project_id: projectFilter.value,
    name: '',
    username: '',
    password: '',
    description: '',
    status: 1
  }
  dialogVisible.value = true
}

const handleEdit = (row: TestAccount) => {
  isEdit.value = true
  editId.value = row.id
  formData.value = {
    project_id: row.project_id,
    name: row.name,
    username: row.username,
    password: row.password || '',
    description: row.description || '',
    status: row.status
  }
  dialogVisible.value = true
}

const handleDelete = async (row: TestAccount) => {
  await deleteAccount(row.id)
  ElMessage.success('删除成功')
  fetchAccounts()
}

const handleRefresh = async (row: TestAccount) => {
  currentRefreshAccount.value = row
  refreshEnvId.value = undefined
  environments.value = await getEnvironments(row.project_id)
  refreshDialogVisible.value = true
}

const confirmRefresh = async () => {
  if (!currentRefreshAccount.value) return
  
  refreshing.value = true
  try {
    const res = await request.post<any, {message: string, token: string, variable_key: string}>('/auth/refresh', {
      account_id: currentRefreshAccount.value.id,
      environment_id: refreshEnvId.value
    })
    ElMessage.success(`${res.message}，已保存到变量 ${res.variable_key}`)
    refreshDialogVisible.value = false
  } finally {
    refreshing.value = false
  }
}

const submitForm = async () => {
  if (!formData.value.project_id || !formData.value.name || !formData.value.username) {
    ElMessage.warning('请填写必填项')
    return
  }
  
  if (isEdit.value) {
    await updateAccount(editId.value, formData.value)
    ElMessage.success('更新成功')
  } else {
    await createAccount(formData.value)
    ElMessage.success('创建成功')
  }
  dialogVisible.value = false
  fetchAccounts()
}
</script>

<style scoped>
.account-list { background: #fff; padding: 20px; border-radius: 4px; }
.toolbar { margin-bottom: 20px; display: flex; align-items: center; }
</style>
