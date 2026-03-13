<template>
  <div class="project-list">
    <div class="toolbar">
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>新建项目
      </el-button>
    </div>

    <el-table v-loading="loading" :data="projects" style="width: 100%" border>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="项目名称" />
      <el-table-column prop="description" label="描述" show-overflow-tooltip />
      <el-table-column prop="base_url" label="Base URL" show-overflow-tooltip />
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ new Date(row.created_at).toLocaleString() }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="250" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="primary" link @click="goDetail(row)">管理</el-button>
          <el-button size="small" type="primary" link @click="handleEdit(row)">编辑</el-button>
          <el-popconfirm title="确定删除该项目？" @confirm="handleDelete(row)">
            <template #reference>
              <el-button size="small" type="danger" link>删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑项目' : '新建项目'" width="600px">
      <el-form ref="formRef" :model="formData" :rules="rules" label-width="120px">
        <el-tabs v-model="activeTab">
          <el-tab-pane label="基本信息" name="basic">
            <el-form-item label="项目名称" prop="name">
              <el-input v-model="formData.name" placeholder="请输入项目名称" />
            </el-form-item>
            <el-form-item label="描述">
              <el-input v-model="formData.description" type="textarea" :rows="3" placeholder="请输入项目描述" />
            </el-form-item>
            <el-form-item label="Base URL">
              <el-input v-model="formData.base_url" placeholder="如 https://api.example.com" />
            </el-form-item>
          </el-tab-pane>
          <el-tab-pane label="登录配置" name="auth">
            <el-form-item label="登录 URL">
              <el-input v-model="formData.auth_config.url" placeholder="如 /api/login" />
            </el-form-item>
            <el-form-item label="请求方法">
              <el-select v-model="formData.auth_config.method" style="width: 100%">
                <el-option label="POST" value="POST" />
                <el-option label="GET" value="GET" />
              </el-select>
            </el-form-item>
            <el-form-item label="请求体 (JSON)">
              <el-input v-model="authBodyStr" type="textarea" :rows="4" placeholder='如 {"username": "${username}", "password": "${password}"}' />
              <div style="font-size: 12px; color: #999;">支持占位符：${username}, ${password}</div>
            </el-form-item>
            <el-form-item label="Token 提取">
              <el-input v-model="formData.auth_config.token_jsonpath" placeholder="JSONPath，如 $.data.token" />
            </el-form-item>
            <el-form-item label="保存变量名">
              <el-input v-model="formData.auth_config.variable_key" placeholder="如 token" />
            </el-form-item>
          </el-tab-pane>
        </el-tabs>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance } from 'element-plus'
import { getProjects, createProject, updateProject, deleteProject, type Project } from '@/api/project'

const router = useRouter()
const loading = ref(false)
const projects = ref<Project[]>([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitLoading = ref(false)
const formRef = ref<FormInstance>()
const activeTab = ref('basic')

const formData = ref({ 
  id: 0, 
  name: '', 
  description: '', 
  base_url: '',
  auth_config: {
    url: '',
    method: 'POST',
    token_jsonpath: '',
    variable_key: 'token'
  } as any
})
const authBodyStr = ref('')
const rules = { name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }] }

const fetchProjects = async () => {
  loading.value = true
  try {
    projects.value = await getProjects()
  } finally {
    loading.value = false
  }
}

onMounted(() => fetchProjects())

const handleAdd = () => {
  isEdit.value = false
  activeTab.value = 'basic'
  formData.value = { 
    id: 0, 
    name: '', 
    description: '', 
    base_url: '',
    auth_config: { url: '', method: 'POST', token_jsonpath: '', variable_key: 'token' }
  }
  authBodyStr.value = ''
  dialogVisible.value = true
}

const handleEdit = (row: Project) => {
  isEdit.value = true
  activeTab.value = 'basic'
  formData.value = { 
    id: row.id, 
    name: row.name, 
    description: row.description || '', 
    base_url: row.base_url || '',
    auth_config: row.auth_config || { url: '', method: 'POST', token_jsonpath: '', variable_key: 'token' }
  }
  authBodyStr.value = formData.value.auth_config.body ? JSON.stringify(formData.value.auth_config.body, null, 2) : ''
  dialogVisible.value = true
}

const handleDelete = async (row: Project) => {
  await deleteProject(row.id)
  ElMessage.success('删除成功')
  fetchProjects()
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    // 解析 authBodyStr
    let parsedBody = {}
    if (authBodyStr.value.trim()) {
      try {
        parsedBody = JSON.parse(authBodyStr.value)
      } catch (e) {
        ElMessage.error('请求体 JSON 格式不正确')
        return
      }
    }
    
    submitLoading.value = true
    try {
      const authConfig = {
        ...formData.value.auth_config,
        body: parsedBody
      }
      
      const payload = { 
        name: formData.value.name, 
        description: formData.value.description, 
        base_url: formData.value.base_url,
        auth_config: authConfig
      }
      
      if (isEdit.value) {
        await updateProject(formData.value.id, payload)
        ElMessage.success('更新成功')
      } else {
        await createProject(payload)
        ElMessage.success('创建成功')
      }
      dialogVisible.value = false
      fetchProjects()
    } finally {
      submitLoading.value = false
    }
  })
}

const goDetail = (row: Project) => {
  router.push(`/projects/${row.id}`)
}
</script>

<style scoped>
.project-list { background: #fff; padding: 20px; border-radius: 4px; }
.toolbar { margin-bottom: 20px; }
</style>
