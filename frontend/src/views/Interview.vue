
<template>
  <div class="interview-page">
    <div class="page-header">
      <div>
        <h2>AI 面试</h2>
        <p>基于候选人简历开展智能面试</p>
      </div>
      <el-tag v-if="sessionData" type="success">
        面试会话已创建
      </el-tag>
    </div>

    <el-card v-if="sessionData" shadow="never">
      <div class="candidate-info">
        <div>
          <span class="info-label">候选人简历</span>
          <div class="info-value">{{ sessionData.filename }}</div>
        </div>

        <div>
          <span class="info-label">当前面试阶段</span>
          <div class="info-value">
            {{ sessionData.stage_name || sessionData.stage }}
          </div>
        </div>
      </div>

      <el-divider />

      <div class="chat-title">
        <el-icon><ChatDotRound /></el-icon>
        <span>面试对话</span>
      </div>

      <div class="message">
        <div class="avatar">AI</div>
        <div class="message-content">
          <div class="message-name">AI 面试官</div>
          <div class="message-bubble">
            {{ sessionData.answer || '面试会话已创建，请继续。' }}
          </div>
        </div>
      </div>

      <el-alert
        title="会话创建成功"
        description="AI 已根据候选人简历生成第一个面试问题。下一步将接入候选人回答和连续对话功能。"
        type="success"
        :closable="false"
        show-icon
      />
    </el-card>

    <el-empty
      v-else
      description="暂未找到面试会话，请先上传简历并创建面试"
    >
      <el-button type="primary" @click="goToResume">
        前往简历管理
      </el-button>
    </el-empty>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ChatDotRound } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const sessionData = ref(null)

onMounted(() => {
  const sessionId = route.params.sessionId

  if (!sessionId) return

  const savedData = sessionStorage.getItem(
    `interview_${sessionId}`
  )

  if (savedData) {
    try {
      sessionData.value = JSON.parse(savedData)
    } catch (error) {
      console.error('读取面试会话信息失败：', error)
    }
  }
})

function goToResume() {
  router.push('/resume')
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
  color: #909399;
  font-size: 14px;
}

.candidate-info {
  display: flex;
  gap: 80px;
  padding: 10px 0;
}

.info-label {
  color: #909399;
  font-size: 13px;
}

.info-value {
  margin-top: 8px;
  color: #303133;
  font-weight: 600;
}

.chat-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  margin-bottom: 24px;
}

.message {
  display: flex;
  gap: 14px;
  margin-bottom: 28px;
}

.avatar {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  border-radius: 50%;
  background: #409eff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
}

.message-content {
  flex: 1;
}

.message-name {
  color: #606266;
  font-size: 13px;
  margin-bottom: 10px;
}

.message-bubble {
  display: inline-block;
  max-width: 85%;
  padding: 16px;
  border-radius: 8px;
  background: #f2f6fc;
  color: #303133;
  line-height: 1.8;
  white-space: pre-wrap;
}

.el-alert {
  margin-top: 24px;
}
</style>
