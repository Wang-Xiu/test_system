<template>
  <div class="suite-edit">
    <div class="header-bar">
      <el-page-header @back="$router.push('/suites')">
        <template #content>
          <span>编辑套件: {{ suite?.name || '加载中...' }}</span>
        </template>
      </el-page-header>
    </div>

    <el-row :gutter="20">
      <!-- 左侧：可选用例 -->
      <el-col :span="10">
        <el-card>
          <template #header>
            <span>可选用例</span>
          </template>
          <el-table :data="availableCases" border size="small" max-height="500">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="name" label="名称" show-overflow-tooltip />
            <el-table-column label="操作" width="80">
              <template #default="{ row }">
                <el-button size="small" type="primary" link @click="addCase(row)">添加</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- 右侧：已选用例（可拖拽排序） -->
      <el-col :span="14">
        <el-card>
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span>已选用例（拖拽排序）</span>
              <el-button type="primary" size="small" @click="saveSuite" :loading="saving">保存排序</el-button>
            </div>
          </template>
          <el-table :data="selectedCases" border size="small" row-key="id" max-height="500">
            <el-table-column label="序号" width="60">
              <template #default="{ $index }">{{ $index + 1 }}</template>
            </el-table-column>
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="name" label="名称" show-overflow-tooltip />
            <el-table-column label="操作" width="120">
              <template #default="{ $index }">
                <el-button size="small" link @click="moveUp($index)" :disabled="$index === 0">上移</el-button>
                <el-button size="small" link @click="moveDown($index)" :disabled="$index === selectedCases.length - 1">下移</el-button>
                <el-button size="small" type="danger" link @click="removeCase($index)">移除</el-button>
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
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getSuite, updateSuite, type SuiteDetail } from '@/api/suite'
import { getCases, type TestCase } from '@/api/case'

const route = useRoute()
const suiteId = Number(route.params.id)

const suite = ref<SuiteDetail | null>(null)
const allCases = ref<TestCase[]>([])
const selectedCases = ref<{ id: number; name: string }[]>([])
const saving = ref(false)

const availableCases = ref<TestCase[]>([])

const refreshAvailable = () => {
  const selectedIds = new Set(selectedCases.value.map(c => c.id))
  availableCases.value = allCases.value.filter(c => !selectedIds.has(c.id))
}

onMounted(async () => {
  suite.value = await getSuite(suiteId)
  // 如果套件没有关联项目，或者想显示所有用例，可以不传 project_id
  allCases.value = await getCases(0, 1000, suite.value?.project_id || undefined)
  selectedCases.value = (suite.value?.cases || []).map(c => ({ id: c.id, name: c.name }))
  refreshAvailable()
})

const addCase = (c: TestCase) => {
  selectedCases.value.push({ id: c.id, name: c.name })
  refreshAvailable()
}

const removeCase = (index: number) => {
  selectedCases.value.splice(index, 1)
  refreshAvailable()
}

const moveUp = (index: number) => {
  if (index <= 0) return
  const arr = selectedCases.value
  ;[arr[index - 1], arr[index]] = [arr[index], arr[index - 1]]
}

const moveDown = (index: number) => {
  const arr = selectedCases.value
  if (index >= arr.length - 1) return
  ;[arr[index], arr[index + 1]] = [arr[index + 1], arr[index]]
}

const saveSuite = async () => {
  saving.value = true
  try {
    await updateSuite(suiteId, { case_ids: selectedCases.value.map(c => c.id) })
    ElMessage.success('保存成功')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.suite-edit { background: #fff; padding: 20px; border-radius: 4px; }
.header-bar { margin-bottom: 20px; }
</style>
