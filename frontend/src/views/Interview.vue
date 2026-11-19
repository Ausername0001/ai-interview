
<template>
  <div class="interview-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <div>
        <h2>AI 面试</h2>
        <p>基于候选人简历开展智能面试</p>
      </div>

      <el-tag :type="completed ? 'success' : 'primary'">
        {{ completed ? '面试已结束' : '面试进行中' }}
      </el-tag>
    </div>

    <el-row :gutter="20">
      <!-- 左侧面试信息 -->
      <el-col :span="6">
        <el-card shadow="never" class="info-card">
          <h3>面试信息</h3>

          <div class="info-item">
            <span>简历文件</span>
            <p>{{ sessionData.filename || '未提供' }}</p>
          </div>

          <el-divider />

          <div class="info-item">
            <span>当前阶段</span>
            <p>{{ sessionData.stage_name || '开场与自我介绍' }}</p>
          </div>

          <el-divider />

          <div class="info-item">
            <span>对话轮数</span>
            <p>{{ totalTurns }}</p>
          </div>

          <el-divider />

          <div class="info-item">
            <span>会话 ID</span>
            <p class="session-id">{{ sessionId }}</p>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧对话区域 -->
      <el-col :span="18">
        <el-card shadow="never" class="chat-card">
          <template #header>
            <div class="chat-header">
              <span>面试对话</span>
              <span class="chat-tip">AI 面试官</span>
            </div>
          </template>

          <!-- 对话消息 -->
          <div class="chat-messages">
            <div
              v-for="(item, index) in messages"
              :key="index"
              class="message"
              :class="item.role"
            >
              <div class="avatar">
                {{ item.role === 'ai' ? 'AI' : '我' }}
              </div>

              <div class="message-content">
                <div class="message-name">
                  {{ item.role === 'ai' ? 'AI 面试官' : '候选人' }}
                </div>

                <div class="message-bubble">
                  {{ item.content }}
                </div>
              </div>
            </div>

            <div v-if="sending" class="loading-tip">
              <el-icon class="is-loading"><Loading /></el-icon>
              AI 正在思考，请稍候...
            </div>
          </div>

          <!-- 面试结束提示 -->
          <el-alert
            v-if="completed"
            title="本次面试已结束"
            description="AI 已完成面试流程，可以进入面试报告模块查看结果。"
            type="success"
            show-icon
            :closable="false"
          />

          <!-- 输入区域 -->
          <div v-if="!completed" class="input-area">
            <el-input
              v-model="inputText"
              type="textarea"
              :rows="4"
              resize="none"
              placeholder="请输入你的回答，按 Enter 发送，Shift + Enter 换行"
              :disabled="sending"
              @keydown.enter.exact.prevent="sendMessage"
            />

            <div class="input-footer">
              <span>请认真回答，AI 将根据你的回答继续追问</span>

              <el-button
                type="primary"
                :loading="sending"
                :disabled="!inputText.trim() || sending"
                @click="sendMessage"
              >
                发送回答
                <el-icon><Promotion /></el-icon>
              </el-button>
            </div>
          </div>

          <div v-else class="finished-actions">
            <el-button type="primary" @click="goToReport">
              查看面试报告
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import {
  Loading,
  Promotion
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const sessionId = route.params.sessionId

const sessionData = ref({
  filename: '',
  stage: '',
  stage_name: ''
})

const messages = ref([])
const inputText = ref('')
const sending = ref(false)
const completed = ref(false)
const totalTurns = ref(0)
const summary = ref(null)

// 初始化面试页面
onMounted(() => {
  if (!sessionId) {
    ElMessage.warning('缺少面试会话 ID')
    router.push('/resume')
    return
  }

  const savedData = sessionStorage.getItem(
    `interview_${sessionId}`
  )

  if (!savedData) {
    ElMessage.error('未找到面试会话信息，请重新创建面试')
    router.push('/resume')
    return
  }

  try {
    const data = JSON.parse(savedData)

    sessionData.value = data

    // 将 AI 的第一个问题加入聊天记录
    if (data.answer) {
      messages.value.push({
        role: 'ai',
        content: data.answer
      })
    }
  } catch (error) {
    console.error('读取面试信息失败：', error)
    ElMessage.error('面试信息读取失败')
  }
})

// 发送候选人回答
async function sendMessage() {
  const message = inputText.value.trim()

  if (!message || sending.value || completed.value) {
    return
  }

  // 显示候选人的回答
  messages.value.push({
    role: 'user',
    content: message
  })

  inputText.value = ''
  sending.value = true

  try {
    const response = await axios.post('/api/chat', {
      session_id: sessionId,
      message: message
    })

    const data = response.data

    // 更新面试阶段
    sessionData.value.stage = data.stage || sessionData.value.stage
    sessionData.value.stage_name =
      data.stage_name || sessionData.value.stage_name

    totalTurns.value = data.total_turns ?? totalTurns.value + 1

    // 显示 AI 的回复
    if (data.answer) {
      messages.value.push({
        role: 'ai',
        content: data.answer
      })
    }

    // 判断面试是否结束
    if (data.completed) {
      completed.value = true
      summary.value = data.summary || null

      sessionStorage.setItem(
        `summary_${sessionId}`,
        JSON.stringify(summary.value)
      )

      ElMessage.success('面试已结束')
    }

  } catch (error) {
    console.error('发送回答失败：', error)

    // 请求失败时移除刚刚添加的回答，允许重新发送
    messages.value.pop()
    inputText.value = message

    ElMessage.error(
      error.response?.data?.detail ||
      '发送失败，请检查网络或后端服务'
    )
  } finally {
    sending.value = false
  }
}

// 进入面试报告页面
function goToReport() {
  router.push(`/report/${sessionId}`)
}
</script>

<style scoped>
.interview-page {
  width: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
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

.info-card,
.chat-card {
  border: none;
  border-radius: 10px;
}

.info-card h3 {
  margin: 0 0 24px;
  font-size: 16px;
}

.info-item span {
  color: #909399;
  font-size: 13px;
}

.info-item p {
  color: #303133;
  font-size: 14px;
  font-weight: 600;
  margin: 8px 0 0;
  word-break: break-all;
}

.session-id {
  font-size: 11px !important;
  font-weight: normal !important;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.chat-tip {
  color: #909399;
  font-size: 12px;
  font-weight: normal;
}

.chat-messages {
  min-height: 360px;
  max-height: 520px;
  overflow-y: auto;
  padding: 10px 4px 24px;
}

.message {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.message.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 38px;
  height: 38px;
  flex-shrink: 0;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #409eff;
  color: white;
  font-size: 13px;
  font-weight: bold;
}

.message.user .avatar {
  background: #67c23a;
}

.message-content {
  max-width: 80%;
}

.message-name {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.message.user .message-name {
  text-align: right;
}

.message-bubble {
  padding: 14px 16px;
  border-radius: 8px;
  background: #f2f6fc;
  color: #303133;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
}

.message.user .message-bubble {
  background: #ecf5ff;
}

.loading-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #909399;
  font-size: 13px;
  padding: 12px;
}

.input-area {
  border-top: 1px solid #ebeef5;
  padding-top: 20px;
}

.input-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 14px;
}

.input-footer span {
  color: #909399;
  font-size: 12px;
}

.finished-actions {
  display: flex;
  justify-content: flex-end;
  padding-top: 20px;
}
</style>
