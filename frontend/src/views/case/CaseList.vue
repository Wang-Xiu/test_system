<template>
  <div class="case-list">
    <div class="toolbar">
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

    <el-table
      v-loading="loading"
      :data="cases"
      style="width: 100%"
      @selection-change="handleSelectionChange"
      border
    >
      <el-table-column type="selection" width="55" />
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="用例名称" />
      <el-table-column prop="description" label="描述" show-overflow-tooltip />
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="250" fixed="right">
        <template #default="{ row }">
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
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑用例' : '新建用例'"
      width="60%"
      :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="formData" :rules="rules" label-width="80px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入用例名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="formData.description" placeholder="请输入用例描述" />
        </el-form-item>
        <el-form-item label="YAML" prop="yaml_content">
          <el-input
            v-model="formData.yaml_content"
            type="textarea"
            :rows="15"
            placeholder="请输入 YAML 格式的测试用例"
            style="font-family: monospace;"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitLoading">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 导入文件弹窗 -->
    <el-dialog
      v-model="importDialogVisible"
      :title="importType === 'openapi' ? '导入 OpenAPI (Swagger) JSON' : '导入 HAR 抓包文件'"
      width="30%"
    >
      <el-upload
        class="upload-demo"
        drag
        action=""
        :auto-upload="false"
        :on-change="handleFileChange"
        :limit="1"
        accept=".json,.har"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或 <em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            只能上传 {{ importType === 'openapi' ? 'JSON' : 'HAR 或 JSON' }} 文件
          </div>
        </template>
      </el-upload>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="importDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitImport" :loading="importLoading" :disabled="!selectedFile">
            开始生成
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 示例查看弹窗 -->
    <el-dialog v-model="exampleDialogVisible" title="文件格式示例" width="60%">
      <el-tabs v-model="activeExampleTab">
        <el-tab-pane label="OpenAPI (Swagger) 示例" name="openapi">
          <pre class="example-code"><code>{
  "openapi": "3.0.0",
  "info": {
    "title": "Sample API",
    "version": "1.0.0"
  },
  "paths": {
    "/api/users": {
      "get": {
        "summary": "获取用户列表",
        "responses": {
          "200": { "description": "成功" }
        }
      },
      "post": {
        "summary": "创建用户",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "username": { "type": "string" },
                  "age": { "type": "integer" }
                }
              }
            }
          }
        }
      }
    }
  }
}</code></pre>
        </el-tab-pane>
        <el-tab-pane label="HAR 文件示例" name="har">
          <div style="margin-bottom: 10px; color: #666;">
            提示：HAR 文件通常通过浏览器开发者工具 (F12) -> Network 面板 -> 右键 "Save all as HAR with content" 导出。
          </div>
          <pre class="example-code"><code>{
  "log": {
    "version": "1.2",
    "creator": { "name": "WebInspector", "version": "537.36" },
    "entries": [
      {
        "request": {
          "method": "POST",
          "url": "https://api.example.com/login",
          "queryString": [],
          "headers": [
            { "name": "Content-Type", "value": "application/json" }
          ],
          "postData": {
            "mimeType": "application/json",
            "text": "{\"username\":\"admin\",\"password\":\"123456\"}"
          }
        },
        "response": {
          "status": 200,
          "content": {
            "mimeType": "application/json",
            "text": "{\"token\":\"abc...\"}"
          }
        }
      }
    ]
  }
}</code></pre>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, UploadFile } from 'element-plus'
import { getCases, createCase, updateCase, deleteCase, generateFromOpenAPI, generateFromHAR, type TestCase } from '@/api/case'
import { runTasks } from '@/api/task'

const loading = ref(false)
const cases = ref<TestCase[]>([])
const selectedCases = ref<TestCase[]>([])

// Dialog state
const dialogVisible = ref(false)
const isEdit = ref(false)
const submitLoading = ref(false)
const formRef = ref<FormInstance>()

const formData = ref({
  id: 0,
  name: '',
  description: '',
  yaml_content: ''
})

// Import dialog state
const importDialogVisible = ref(false)
const importType = ref<'openapi' | 'har'>('openapi')
const importLoading = ref(false)
const selectedFile = ref<File | null>(null)

// Example dialog state
const exampleDialogVisible = ref(false)
const activeExampleTab = ref('openapi')

const rules = {
  name: [{ required: true, message: '请输入用例名称', trigger: 'blur' }],
  yaml_content: [{ required: true, message: '请输入 YAML 内容', trigger: 'blur' }]
}

const fetchCases = async () => {
  loading.value = true
  try {
    cases.value = await getCases()
  } catch (error) {
    // Error handled by interceptor
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchCases()
})

const handleSelectionChange = (val: TestCase[]) => {
  selectedCases.value = val
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString()
}

const handleAdd = () => {
  isEdit.value = false
  formData.value = {
    id: 0,
    name: '',
    description: '',
    yaml_content: 'name: 示例用例\nrequest:\n  method: GET\n  url: https://httpbin.org/get\nvalidate:\n  - eq:\n      status_code: 200'
  }
  dialogVisible.value = true
}

const handleEdit = (row: TestCase) => {
  isEdit.value = true
  formData.value = { ...row }
  dialogVisible.value = true
}

const handleDelete = async (row: TestCase) => {
  try {
    await deleteCase(row.id)
    ElMessage.success('删除成功')
    fetchCases()
  } catch (error) {
    // Error handled
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true
      try {
        if (isEdit.value) {
          await updateCase(formData.value.id, {
            name: formData.value.name,
            description: formData.value.description,
            yaml_content: formData.value.yaml_content
          })
          ElMessage.success('更新成功')
        } else {
          await createCase({
            name: formData.value.name,
            description: formData.value.description,
            yaml_content: formData.value.yaml_content
          })
          ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        fetchCases()
      } catch (error) {
        // Error handled
      } finally {
        submitLoading.value = false
      }
    }
  })
}

const handleRunSingle = async (row: TestCase) => {
  try {
    await runTasks([row.id])
    ElMessage.success('任务已提交执行')
  } catch (error) {
    // Error handled
  }
}

const handleRun = async () => {
  if (selectedCases.value.length === 0) return
  try {
    const ids = selectedCases.value.map(c => c.id)
    await runTasks(ids)
    ElMessage.success(`已提交 ${ids.length} 个用例执行`)
    // Clear selection
    selectedCases.value = []
  } catch (error) {
    // Error handled
  }
}

const handleImportCommand = (command: string) => {
  if (command === 'example') {
    exampleDialogVisible.value = true
    return
  }
  importType.value = command as 'openapi' | 'har'
  selectedFile.value = null
  importDialogVisible.value = true
}

const handleFileChange = (uploadFile: UploadFile) => {
  if (uploadFile.raw) {
    selectedFile.value = uploadFile.raw
  }
}

const submitImport = async () => {
  if (!selectedFile.value) return
  
  importLoading.value = true
  try {
    let res
    if (importType.value === 'openapi') {
      res = await generateFromOpenAPI(selectedFile.value)
    } else {
      res = await generateFromHAR(selectedFile.value)
    }
    ElMessage.success(res.message)
    importDialogVisible.value = false
    fetchCases()
  } catch (error) {
    // Error handled by interceptor
  } finally {
    importLoading.value = false
  }
}
</script>

<style scoped>
.case-list {
  background: #fff;
  padding: 20px;
  border-radius: 4px;
}

.toolbar {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
}

.example-code {
  background-color: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 13px;
  line-height: 1.5;
  overflow-x: auto;
  border: 1px solid #e4e7ed;
}
</style>
