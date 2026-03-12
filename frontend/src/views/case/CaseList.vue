<template>
  <div class="case-list">
    <div class="toolbar">
      <el-select v-model="projectFilter" placeholder="按项目筛选" clearable style="width: 200px; margin-right: 10px;" @change="fetchCases">
        <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
      </el-select>
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>新建用例
      </el-button>
      <el-button type="success" :disabled="selectedCases.length === 0" @click="handleRun">
        <el-icon><VideoPlay /></el-icon>批量执行
      </el-button>

      <el-dropdown style="margin-left: 10px;" @command="handleImportCommand">
        <el-button type="info">
          <el-icon><Upload /></el-icon>自动生成用例<el-icon class="el-icon--right"><arrow-down /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="openapi">导入 OpenAPI (Swagger) JSON</el-dropdown-item>
            <el-dropdown-item command="har">导入 HAR 抓包文件</el-dropdown-item>
            <el-dropdown-item divided command="example">查看文件格式示例</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>

    <el-table v-loading="loading" :data="cases" style="width: 100%" @selection-change="handleSelectionChange" border>
      <el-table-column type="selection" width="55" />
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="用例名称" />
      <el-table-column prop="description" label="描述" show-overflow-tooltip />
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="280" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="primary" link @click="handleDebug(row)">调试</el-button>
          <el-button size="small" type="primary" link @click="handleRunSingle(row)">执行</el-button>
          <el-button size="small" type="primary" link @click="handleEdit(row)">编辑</el-button>
          <el-popconfirm title="确定要删除该用例吗？" @confirm="handleDelete(row)">
            <template #reference>
              <el-button size="small" type="danger" link>删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- 编辑/新建弹窗 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑用例' : '新建用例'" width="60%" :close-on-click-modal="false">
      <el-form ref="formRef" :model="formData" :rules="rules" label-width="80px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入用例名称" />
        </el-form-item>
        <el-form-item label="所属项目">
          <el-select v-model="formData.project_id" placeholder="选择项目（可选）" clearable style="width: 100%;">
            <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="formData.description" placeholder="请输入用例描述" />
        </el-form-item>
        <el-form-item label="YAML" prop="yaml_content">
          <el-input v-model="formData.yaml_content" type="textarea" :rows="15" placeholder="请输入 YAML 格式的测试用例" style="font-family: monospace;" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">确定</el-button>
      </template>
    </el-dialog>

    <!-- 导入文件弹窗 -->
    <el-dialog v-model="importDialogVisible" :title="importType === 'openapi' ? '导入 OpenAPI (Swagger) JSON' : '导入 HAR 抓包文件'" width="30%">
      <el-upload class="upload-demo" drag action="" :auto-upload="false" :on-change="handleFileChange" :limit="1" accept=".json,.har">
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">将文件拖到此处，或 <em>点击上传</em></div>
        <template #tip>
          <div class="el-upload__tip">只能上传 {{ importType === 'openapi' ? 'JSON' : 'HAR 或 JSON' }} 文件</div>
        </template>
      </el-upload>
      <template #footer>
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitImport" :loading="importLoading" :disabled="!selectedFile">开始生成</el-button>
      </template>
    </el-dialog>

    <!-- 调试结果弹窗 -->
    <el-dialog v-model="debugDialogVisible" title="调试结果" width="60%">
      <div v-if="debugLoading" style="text-align: center; padding: 40px;">
        <el-icon class="is-loading" :size="32"><Loading /></el-icon>
        <p>正在执行调试...</p>
      </div>
      <div v-else-if="debugResult">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="状态">
            <el-tag :type="debugResult.status === 'pass' ? 'success' : 'danger'">{{ debugResult.status }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="耗时">{{ debugResult.response?.elapsed_ms }}ms</el-descriptions-item>
          <el-descriptions-item label="请求方法">{{ debugResult.request?.method }}</el-descriptions-item>
          <el-descriptions-item label="状态码">{{ debugResult.response?.status_code }}</el-descriptions-item>
        </el-descriptions>
        <el-collapse style="margin-top: 15px;">
          <el-collapse-item title="请求详情">
            <pre class="debug-pre">{{ JSON.stringify(debugResult.request, null, 2) }}</pre>
          </el-collapse-item>
          <el-collapse-item title="响应体">
            <pre class="debug-pre">{{ JSON.stringify(debugResult.response?.body, null, 2) }}</pre>
          </el-collapse-item>
          <el-collapse-item title="断言结果">
            <div v-for="(v, i) in debugResult.validations" :key="i" style="margin-bottom: 4px;">
              <el-tag :type="v.result === 'pass' ? 'success' : 'danger'" size="small">{{ v.result }}</el-tag>
              <span style="margin-left: 8px;">{{ v.rule }}</span>
            </div>
          </el-collapse-item>
          <el-collapse-item v-if="debugResult.extracted_vars && Object.keys(debugResult.extracted_vars).length" title="提取的变量">
            <pre class="debug-pre">{{ JSON.stringify(debugResult.extracted_vars, null, 2) }}</pre>
          </el-collapse-item>
        </el-collapse>
      </div>
    </el-dialog>

    <!-- 示例查看弹窗 -->
    <el-dialog v-model="exampleDialogVisible" title="文件格式示例" width="60%">
      <el-tabs v-model="activeExampleTab">
        <el-tab-pane label="OpenAPI (Swagger) 示例" name="openapi">
          <pre class="example-code"><code>{
  "openapi": "3.0.0",
  "info": { "title": "Sample API", "version": "1.0.0" },
  "paths": {
    "/api/users": {
      "get": { "summary": "获取用户列表", "responses": { "200": { "description": "成功" } } }
    }
  }
}</code></pre>
        </el-tab-pane>
        <el-tab-pane label="HAR 文件示例" name="har">
          <pre class="example-code"><code>{
  "log": {
    "entries": [{
      "request": { "method": "POST", "url": "https://api.example.com/login",
        "headers": [{ "name": "Content-Type", "value": "application/json" }],
        "postData": { "mimeType": "application/json", "text": "{\"username\":\"admin\"}" }
      }
    }]
  }
}</code></pre>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>

    <!-- 执行选项弹窗（选择环境） -->
    <el-dialog v-model="runDialogVisible" title="执行选项" width="400px">
      <el-form label-width="80px">
        <el-form-item label="项目">
          <el-select v-model="runProjectId" placeholder="选择项目" clearable style="width: 100%;" @change="onRunProjectChange">
            <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </el-form-item>
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
import { Loading } from '@element-plus/icons-vue'
import type { FormInstance, UploadFile } from 'element-plus'
import { getCases, createCase, updateCase, deleteCase, generateFromOpenAPI, generateFromHAR, type TestCase } from '@/api/case'
import { runTasks } from '@/api/task'
import { getProjects, type Project } from '@/api/project'
import { getEnvironments, type Environment } from '@/api/environment'
import request from '@/utils/request'

const loading = ref(false)
const cases = ref<TestCase[]>([])
const projects = ref<Project[]>([])
const selectedCases = ref<TestCase[]>([])
const projectFilter = ref<number | undefined>(undefined)

const dialogVisible = ref(false)
const isEdit = ref(false)
const submitLoading = ref(false)
const formRef = ref<FormInstance>()
const formData = ref({ id: 0, name: '', description: '', yaml_content: '', project_id: undefined as number | undefined })

const importDialogVisible = ref(false)
const importType = ref<'openapi' | 'har'>('openapi')
const importLoading = ref(false)
const selectedFile = ref<File | null>(null)
const exampleDialogVisible = ref(false)
const activeExampleTab = ref('openapi')

// Debug
const debugDialogVisible = ref(false)
const debugLoading = ref(false)
const debugResult = ref<any>(null)

// Run options
const runDialogVisible = ref(false)
const runProjectId = ref<number | undefined>(undefined)
const runEnvId = ref<number | undefined>(undefined)
const runEnvs = ref<Environment[]>([])
const pendingRunCaseIds = ref<number[]>([])

const rules = {
  name: [{ required: true, message: '请输入用例名称', trigger: 'blur' }],
  yaml_content: [{ required: true, message: '请输入 YAML 内容', trigger: 'blur' }]
}

const fetchCases = async () => {
  loading.value = true
  try {
    const params: any = {}
    if (projectFilter.value) params.project_id = projectFilter.value
    cases.value = await getCases(0, 100, params.project_id)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  projects.value = await getProjects()
  fetchCases()
})

const handleSelectionChange = (val: TestCase[]) => { selectedCases.value = val }
const formatDate = (dateStr: string) => new Date(dateStr).toLocaleString()

const handleAdd = () => {
  isEdit.value = false
  formData.value = { id: 0, name: '', description: '', yaml_content: 'name: 示例用例\nrequest:\n  method: GET\n  url: https://httpbin.org/get\nvalidate:\n  - eq:\n      status_code: 200', project_id: projectFilter.value }
  dialogVisible.value = true
}

const handleEdit = (row: TestCase) => {
  isEdit.value = true
  formData.value = { ...row, project_id: (row as any).project_id }
  dialogVisible.value = true
}

const handleDelete = async (row: TestCase) => {
  await deleteCase(row.id)
  ElMessage.success('删除成功')
  fetchCases()
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitLoading.value = true
    try {
      const payload = { name: formData.value.name, description: formData.value.description, yaml_content: formData.value.yaml_content, project_id: formData.value.project_id || null }
      if (isEdit.value) {
        await updateCase(formData.value.id, payload)
        ElMessage.success('更新成功')
      } else {
        await createCase(payload)
        ElMessage.success('创建成功')
      }
      dialogVisible.value = false
      fetchCases()
    } finally {
      submitLoading.value = false
    }
  })
}

const handleRunSingle = (row: TestCase) => {
  pendingRunCaseIds.value = [row.id]
  runProjectId.value = (row as any).project_id || undefined
  runEnvId.value = undefined
  runEnvs.value = []
  if (runProjectId.value) onRunProjectChange(runProjectId.value)
  runDialogVisible.value = true
}

const handleRun = () => {
  if (selectedCases.value.length === 0) return
  pendingRunCaseIds.value = selectedCases.value.map(c => c.id)
  runDialogVisible.value = true
}

const onRunProjectChange = async (pid: number) => {
  if (pid) {
    runEnvs.value = await getEnvironments(pid)
  } else {
    runEnvs.value = []
  }
  runEnvId.value = undefined
}

const confirmRun = async () => {
  try {
    await runTasks(pendingRunCaseIds.value, runProjectId.value, runEnvId.value)
    ElMessage.success('任务已提交执行')
    runDialogVisible.value = false
    selectedCases.value = []
  } catch (error) { /* handled */ }
}

// Debug
const handleDebug = async (row: TestCase) => {
  debugDialogVisible.value = true
  debugLoading.value = true
  debugResult.value = null
  try {
    const res = await request.post<any, any>('/debug/run', {
      yaml_content: row.yaml_content,
      environment_id: null,
    })
    debugResult.value = res
  } catch (e) {
    debugResult.value = { status: 'error', error: String(e) }
  } finally {
    debugLoading.value = false
  }
}

// Import
const handleImportCommand = (command: string) => {
  if (command === 'example') { exampleDialogVisible.value = true; return }
  importType.value = command as 'openapi' | 'har'
  selectedFile.value = null
  importDialogVisible.value = true
}

const handleFileChange = (uploadFile: UploadFile) => {
  if (uploadFile.raw) selectedFile.value = uploadFile.raw
}

const submitImport = async () => {
  if (!selectedFile.value) return
  importLoading.value = true
  try {
    const res = importType.value === 'openapi'
      ? await generateFromOpenAPI(selectedFile.value)
      : await generateFromHAR(selectedFile.value)
    ElMessage.success(res.message)
    importDialogVisible.value = false
    fetchCases()
  } finally {
    importLoading.value = false
  }
}
</script>

<style scoped>
.case-list { background: #fff; padding: 20px; border-radius: 4px; }
.toolbar { margin-bottom: 20px; display: flex; align-items: center; }
.example-code { background-color: #f5f7fa; padding: 15px; border-radius: 4px; font-family: monospace; font-size: 13px; line-height: 1.5; overflow-x: auto; border: 1px solid #e4e7ed; }
.debug-pre { background: #f5f7fa; padding: 12px; border-radius: 4px; font-family: monospace; font-size: 12px; white-space: pre-wrap; word-break: break-all; max-height: 300px; overflow: auto; }
</style>
