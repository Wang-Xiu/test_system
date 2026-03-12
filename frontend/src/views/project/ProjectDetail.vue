<template>
  <div class="project-detail">
    <div class="header-bar">
      <el-page-header @back="$router.push('/projects')">
        <template #content>
          <span>{{ project?.name || '加载中...' }}</span>
        </template>
      </el-page-header>
    </div>

    <el-tabs v-model="activeTab" type="border-card">
      <!-- 环境管理 -->
      <el-tab-pane label="环境管理" name="envs">
        <div class="tab-toolbar">
          <el-button type="primary" size="small" @click="handleAddEnv">新建环境</el-button>
        </div>
        <el-table :data="environments" border style="width: 100%">
          <el-table-column prop="name" label="环境名称" />
          <el-table-column prop="base_url" label="Base URL" show-overflow-tooltip />
          <el-table-column prop="is_default" label="默认" width="80">
            <template #default="{ row }">
              <el-tag v-if="row.is_default" type="success" size="small">是</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200">
            <template #default="{ row }">
              <el-button size="small" type="primary" link @click="handleEditEnv(row)">编辑</el-button>
              <el-popconfirm title="确定删除？" @confirm="handleDeleteEnv(row)">
                <template #reference>
                  <el-button size="small" type="danger" link>删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 变量管理 -->
      <el-tab-pane label="变量管理" name="vars">
        <div class="tab-toolbar">
          <el-select v-model="varEnvFilter" placeholder="按环境筛选" clearable style="width: 200px; margin-right: 10px;">
            <el-option label="项目级变量" :value="0" />
            <el-option v-for="env in environments" :key="env.id" :label="env.name" :value="env.id" />
          </el-select>
          <el-button type="primary" size="small" @click="handleAddVar">新建变量</el-button>
        </div>
        <el-table :data="filteredVariables" border style="width: 100%">
          <el-table-column prop="key" label="变量名" width="200" />
          <el-table-column prop="value" label="变量值" show-overflow-tooltip />
          <el-table-column prop="var_type" label="类型" width="100" />
          <el-table-column prop="description" label="描述" show-overflow-tooltip />
          <el-table-column label="作用域" width="120">
            <template #default="{ row }">
              <el-tag v-if="row.environment_id" type="warning" size="small">环境</el-tag>
              <el-tag v-else type="info" size="small">项目</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150">
            <template #default="{ row }">
              <el-button size="small" type="primary" link @click="handleEditVar(row)">编辑</el-button>
              <el-popconfirm title="确定删除？" @confirm="handleDeleteVar(row)">
                <template #reference>
                  <el-button size="small" type="danger" link>删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 环境弹窗 -->
    <el-dialog v-model="envDialogVisible" :title="isEditEnv ? '编辑环境' : '新建环境'" width="500px">
      <el-form :model="envForm" label-width="90px">
        <el-form-item label="环境名称" required>
          <el-input v-model="envForm.name" placeholder="如 development / staging / production" />
        </el-form-item>
        <el-form-item label="Base URL">
          <el-input v-model="envForm.base_url" placeholder="如 https://staging-api.example.com" />
        </el-form-item>
        <el-form-item label="默认环境">
          <el-switch v-model="envForm.is_default" />
        </el-form-item>
        <el-form-item label="认证类型">
          <el-select v-model="authType" placeholder="选择认证类型" clearable style="width: 100%;">
            <el-option label="Bearer Token" value="bearer" />
            <el-option label="Basic Auth" value="basic" />
            <el-option label="API Key" value="api_key" />
          </el-select>
        </el-form-item>
        <template v-if="authType === 'bearer'">
          <el-form-item label="Token">
            <el-input v-model="authToken" placeholder="Bearer token value" />
          </el-form-item>
        </template>
        <template v-if="authType === 'basic'">
          <el-form-item label="用户名">
            <el-input v-model="authUsername" />
          </el-form-item>
          <el-form-item label="密码">
            <el-input v-model="authPassword" type="password" show-password />
          </el-form-item>
        </template>
        <template v-if="authType === 'api_key'">
          <el-form-item label="Key Name">
            <el-input v-model="apiKeyName" placeholder="如 X-API-Key" />
          </el-form-item>
          <el-form-item label="Key Value">
            <el-input v-model="apiKeyValue" />
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="envDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitEnv">确定</el-button>
      </template>
    </el-dialog>

    <!-- 变量弹窗 -->
    <el-dialog v-model="varDialogVisible" :title="isEditVar ? '编辑变量' : '新建变量'" width="500px">
      <el-form :model="varForm" label-width="90px">
        <el-form-item label="变量名" required>
          <el-input v-model="varForm.key" placeholder="如 base_token" />
        </el-form-item>
        <el-form-item label="变量值" required>
          <el-input v-model="varForm.value" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="varForm.var_type" style="width: 100%;">
            <el-option label="字符串" value="string" />
            <el-option label="整数" value="integer" />
            <el-option label="JSON" value="json" />
            <el-option label="密钥" value="secret" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联环境">
          <el-select v-model="varForm.environment_id" placeholder="不选则为项目级变量" clearable style="width: 100%;">
            <el-option v-for="env in environments" :key="env.id" :label="env.name" :value="env.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="varForm.description" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="varDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitVar">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getProject, type Project } from '@/api/project'
import { getEnvironments, createEnvironment, updateEnvironment, deleteEnvironment, type Environment } from '@/api/environment'
import { getVariables, createVariable, updateVariable, deleteVariable, type Variable } from '@/api/variable'

const route = useRoute()
const projectId = Number(route.params.id)

const project = ref<Project | null>(null)
const environments = ref<Environment[]>([])
const variables = ref<Variable[]>([])
const activeTab = ref('envs')

// --- Environment ---
const envDialogVisible = ref(false)
const isEditEnv = ref(false)
const envForm = ref({ id: 0, name: '', base_url: '', is_default: false })
const authType = ref('')
const authToken = ref('')
const authUsername = ref('')
const authPassword = ref('')
const apiKeyName = ref('')
const apiKeyValue = ref('')

// --- Variable ---
const varDialogVisible = ref(false)
const isEditVar = ref(false)
const varEnvFilter = ref<number | undefined>(undefined)
const varForm = ref({ id: 0, key: '', value: '', var_type: 'string', environment_id: undefined as number | undefined, description: '' })

const filteredVariables = computed(() => {
  if (varEnvFilter.value === undefined) return variables.value
  if (varEnvFilter.value === 0) return variables.value.filter(v => !v.environment_id)
  return variables.value.filter(v => v.environment_id === varEnvFilter.value)
})

const fetchAll = async () => {
  project.value = await getProject(projectId)
  environments.value = await getEnvironments(projectId)
  variables.value = await getVariables({ project_id: projectId })
}

onMounted(() => fetchAll())

// --- Environment handlers ---
const handleAddEnv = () => {
  isEditEnv.value = false
  envForm.value = { id: 0, name: '', base_url: '', is_default: false }
  authType.value = ''
  authToken.value = ''
  authUsername.value = ''
  authPassword.value = ''
  apiKeyName.value = ''
  apiKeyValue.value = ''
  envDialogVisible.value = true
}

const handleEditEnv = (row: Environment) => {
  isEditEnv.value = true
  envForm.value = { id: row.id, name: row.name, base_url: row.base_url || '', is_default: row.is_default }
  const ac = row.auth_config || {}
  authType.value = ac.type || ''
  authToken.value = ac.token || ''
  authUsername.value = ac.username || ''
  authPassword.value = ac.password || ''
  apiKeyName.value = ac.api_key_name || ''
  apiKeyValue.value = ac.api_key_value || ''
  envDialogVisible.value = true
}

const handleDeleteEnv = async (row: Environment) => {
  await deleteEnvironment(row.id)
  ElMessage.success('删除成功')
  fetchAll()
}

const buildAuthConfig = () => {
  if (!authType.value) return undefined
  const base: Record<string, any> = { type: authType.value }
  if (authType.value === 'bearer') base.token = authToken.value
  if (authType.value === 'basic') { base.username = authUsername.value; base.password = authPassword.value }
  if (authType.value === 'api_key') { base.api_key_name = apiKeyName.value; base.api_key_value = apiKeyValue.value }
  return base
}

const submitEnv = async () => {
  const payload: any = { name: envForm.value.name, base_url: envForm.value.base_url, is_default: envForm.value.is_default, auth_config: buildAuthConfig() }
  if (isEditEnv.value) {
    await updateEnvironment(envForm.value.id, payload)
    ElMessage.success('更新成功')
  } else {
    await createEnvironment(projectId, payload)
    ElMessage.success('创建成功')
  }
  envDialogVisible.value = false
  fetchAll()
}

// --- Variable handlers ---
const handleAddVar = () => {
  isEditVar.value = false
  varForm.value = { id: 0, key: '', value: '', var_type: 'string', environment_id: undefined, description: '' }
  varDialogVisible.value = true
}

const handleEditVar = (row: Variable) => {
  isEditVar.value = true
  varForm.value = { id: row.id, key: row.key, value: row.value, var_type: row.var_type, environment_id: row.environment_id || undefined, description: row.description || '' }
  varDialogVisible.value = true
}

const handleDeleteVar = async (row: Variable) => {
  await deleteVariable(row.id)
  ElMessage.success('删除成功')
  fetchAll()
}

const submitVar = async () => {
  const payload: any = { key: varForm.value.key, value: varForm.value.value, var_type: varForm.value.var_type, description: varForm.value.description, project_id: projectId, environment_id: varForm.value.environment_id || null }
  if (isEditVar.value) {
    await updateVariable(varForm.value.id, { key: payload.key, value: payload.value, var_type: payload.var_type, description: payload.description })
    ElMessage.success('更新成功')
  } else {
    await createVariable(payload)
    ElMessage.success('创建成功')
  }
  varDialogVisible.value = false
  fetchAll()
}
</script>

<style scoped>
.project-detail { background: #fff; padding: 20px; border-radius: 4px; }
.header-bar { margin-bottom: 20px; }
.tab-toolbar { margin-bottom: 15px; display: flex; align-items: center; }
</style>
