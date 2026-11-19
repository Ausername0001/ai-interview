
<template>
  <div class="resume-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div>
        <h2>简历管理</h2>
        <p>上传候选人简历，自动提取简历文本信息</p>
      </div>
    </div>

    <!-- 上传区域 -->
    <el-card shadow="never" class="upload-card">
      <template #header>
        <div class="card-title">
          <el-icon><Upload /></el-icon>
          <span>上传简历</span>
        </div>
      </template>

      <div class="upload-area">
        <el-icon class="upload-icon" :size="48">
          <DocumentAdd />
        </el-icon>

        <h3>选择候选人简历</h3>
        <p>支持 PDF、DOCX 格式，文件大小不超过 10MB</p>

        <input
          ref="fileInput"
          type="file"
          accept=".pdf,.docx"
          hidden
          @change="handleFileChange"
        />

        <el-button @click="selectFile">
          选择文件
        </el-button>

        <div v-if="selectedFile" class="selected-file">
          <el-icon><Document /></el-icon>
          <span>{{ selectedFile.name }}</span>
          <el-button
            text
            type="danger"
            @click="clearFile"
          >
            移除
          </el-button>
        </div>

        <el-button
          type="primary"
          :disabled="!selectedFile || loading"
          :loading="loading"
          class="upload-button"
          @click="uploadResume"
        >
          {{ loading ? '正在解析...' : '上传并解析' }}
        </el-button>
      </div>
    </el-card>

    <!-- 解析结果 -->
    <el-card
      v-if="resumeResult"
      shadow="never"
      class="result-card"
    >
      <template #header>
        <div class="card-title">
          <el-icon><DocumentChecked /></el-icon>
          <span>简历解析结果</span>
          <el-tag type="success">解析成功</el-tag>
        </div>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="文件名称">
          {{ resumeResult.filename }}
        </el-descriptions-item>

        <el-descriptions-item label="文本长度">
          {{ resumeResult.length }} 字符
        </el-descriptions-item>

        <el-descriptions-item label="处理状态" :span="2">
          {{ resumeResult.message }}
        </el-descriptions-item>
      </el-descriptions>

      <div class="text-title">
        <span>简历文本内容</span>
        <el-button
          text
          type="primary"
          @click="copyResumeText"
        >
          复制文本
        </el-button>
      </div>

      <el-input
        v-model="resumeResult.resume_text"
        type="textarea"
        :rows="16"
        readonly
        resize="vertical"
      />

      <div class="result-actions">
        <el-button
          type="primary"
          :loading="creatingSession"
          @click="createInterviewSession"
>
          创建 AI 面试）
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import {
  Upload,
  DocumentAdd,
  Document,
  DocumentChecked
} from '@element-plus/icons-vue'

const fileInput = ref(null)
const router = useRouter()
const creatingSession = ref(false)
const selectedFile = ref(null)
const loading = ref(false)
const resumeResult = ref(null)

// 打开文件选择窗口
function selectFile() {
  fileInput.value.click()
}

// 选择文件后的检查
function handleFileChange(event) {
  const file = event.target.files[0]

  if (!file) return

  const fileName = file.name.toLowerCase()
  const isValidType =
    fileName.endsWith('.pdf') ||
    fileName.endsWith('.docx')

  if (!isValidType) {
    ElMessage.error('仅支持 PDF 和 DOCX 格式')
    event.target.value = ''
    return
  }

  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过 10MB')
    event.target.value = ''
    return
  }

  selectedFile.value = file
  resumeResult.value = null
}

// 移除文件
function clearFile() {
  selectedFile.value = null
  fileInput.value.value = ''
}

// 上传并解析简历
async function uploadResume() {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择简历文件')
    return
  }

  const formData = new FormData()

  // 字段名称必须与后端的 file 参数一致
  formData.append('file', selectedFile.value)

  loading.value = true

  try {
    const response = await axios.post(
      '/api/resume/parse',
      formData
    )

    resumeResult.value = response.data

    ElMessage.success(
      response.data.message || '简历解析成功'
    )
  } catch (error) {
    console.error('简历上传失败：', error)

    const errorMessage =
      error.response?.data?.detail ||
      error.message ||
      '上传失败，请检查后端服务'

    ElMessage.error(errorMessage)
  } finally {
    loading.value = false
  }
}

// 复制解析文本
async function copyResumeText() {
  try {
    await navigator.clipboard.writeText(
      resumeResult.value.resume_text
    )
    ElMessage.success('简历文本已复制')
  } catch {
    ElMessage.error('复制失败，请手动复制')
  }
}

// 根据解析后的简历创建 AI 面试会话
async function createInterviewSession() {
  if (!resumeResult.value?.resume_text) {
    ElMessage.warning('请先成功解析一份简历')
    return
  }

  creatingSession.value = true

  try {
    const response = await axios.post('/api/session', {
      resume_text: resumeResult.value.resume_text
    })

    const data = response.data

    // 保存首次面试问题，供面试页面读取
    sessionStorage.setItem(
      `interview_${data.session_id}`,
      JSON.stringify({
        filename: resumeResult.value.filename,
        answer: data.answer,
        stage: data.stage,
        stage_name: data.stage_name
      })
    )

    ElMessage.success('面试会话创建成功')

    // 跳转到对应的面试页面
    router.push(`/interview/${data.session_id}`)

  } catch (error) {
    console.error('创建面试会话失败：', error)

    ElMessage.error(
      error.response?.data?.detail ||
      '创建面试会话失败，请检查后端服务'
    )
  } finally {
    creatingSession.value = false
  }
}

</script>

<style scoped>
.resume-page {
  width: 100%;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0 0 8px;
  font-size: 24px;
  color: #303133;
}

.page-header p {
  margin: 0;
  font-size: 14px;
  color: #909399;
}

.upload-card,
.result-card {
  border: none;
  border-radius: 10px;
  margin-bottom: 24px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
}

.upload-area {
  min-height: 280px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: #f8fafc;
  border: 1px dashed #c0c4cc;
  border-radius: 8px;
  padding: 30px;
}

.upload-icon {
  color: #409eff;
}

.upload-area h3 {
  margin: 16px 0 8px;
  color: #303133;
}

.upload-area p {
  color: #909399;
  font-size: 13px;
  margin-bottom: 20px;
}

.selected-file {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 20px;
  color: #606266;
  font-size: 14px;
}

.upload-button {
  margin-top: 24px;
  min-width: 140px;
}

.text-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 24px 0 12px;
  font-weight: 600;
}

.result-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
