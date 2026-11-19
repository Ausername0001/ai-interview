
<template>
  <div class="dashboard">
    <!-- 页面标题 -->
    <div class="page-header">
      <div>
        <h2>工作台</h2>
        <p>欢迎使用 AI 智能面试官系统</p>
      </div>
      <el-button type="primary" @click="goToResume">
        <el-icon><Upload /></el-icon>
        上传简历
      </el-button>
    </div>

    <!-- 数据统计 -->
    <el-row :gutter="20" class="statistics">
      <el-col :span="6" v-for="item in statistics" :key="item.title">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div>
              <p class="stat-title">{{ item.title }}</p>
              <h2>{{ item.value }}</h2>
              <span>{{ item.description }}</span>
            </div>
            <div class="stat-icon" :style="{ background: item.bg }">
              <el-icon :size="26" :color="item.color">
                <component :is="item.icon" />
              </el-icon>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快捷操作 -->
    <el-card shadow="never" class="section-card">
      <template #header>
        <div class="card-header">
          <span>快捷操作</span>
        </div>
      </template>

      <el-row :gutter="20">
        <el-col :span="8">
          <div class="quick-item" @click="goToResume">
            <el-icon :size="28" color="#409EFF">
              <Upload />
            </el-icon>
            <div>
              <h3>上传简历</h3>
              <p>上传候选人简历并自动解析</p>
            </div>
          </div>
        </el-col>

        <el-col :span="8">
          <div class="quick-item" @click="goToInterview">
            <el-icon :size="28" color="#67C23A">
              <ChatDotRound />
            </el-icon>
            <div>
              <h3>开始面试</h3>
              <p>创建 AI 面试会话</p>
            </div>
          </div>
        </el-col>

        <el-col :span="8">
          <div class="quick-item" @click="goToReport">
            <el-icon :size="28" color="#E6A23C">
              <Document />
            </el-icon>
            <div>
              <h3>查看报告</h3>
              <p>查看历史面试评价</p>
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 最近面试 -->
    <el-card shadow="never" class="section-card">
      <template #header>
        <div class="card-header">
          <span>最近面试</span>
          <el-button text type="primary" @click="goToReport">
            查看全部
          </el-button>
        </div>
      </template>

      <el-table :data="recentInterviews" style="width: 100%">
        <el-table-column prop="name" label="候选人" />
        <el-table-column prop="position" label="应聘岗位" />
        <el-table-column prop="date" label="面试时间" />
        <el-table-column label="面试状态">
          <template #default="scope">
            <el-tag :type="scope.row.status === '已完成' ? 'success' : 'warning'">
              {{ scope.row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default>
            <el-button text type="primary" @click="goToReport">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <div class="footer-tip">
      AI 智能面试官 · 智能招聘与面试管理平台
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import {
  Upload,
  ChatDotRound,
  Document,
  User,
  DataAnalysis,
  CircleCheck,
  Clock
} from '@element-plus/icons-vue'

const router = useRouter()

// 第一版使用模拟统计数据
const statistics = [
  {
    title: '面试总数',
    value: 128,
    description: '累计面试次数',
    icon: DataAnalysis,
    color: '#409EFF',
    bg: '#ecf5ff'
  },
  {
    title: '候选人数',
    value: 96,
    description: '累计候选人数量',
    icon: User,
    color: '#67C23A',
    bg: '#f0f9eb'
  },
  {
    title: '已完成面试',
    value: 86,
    description: '已生成面试报告',
    icon: CircleCheck,
    color: '#E6A23C',
    bg: '#fdf6ec'
  },
  {
    title: '待处理面试',
    value: 10,
    description: '等待继续处理',
    icon: Clock,
    color: '#909399',
    bg: '#f4f4f5'
  }
]

// 第一版使用模拟面试记录
const recentInterviews = [
  {
    name: '张同学',
    position: '技术实习生',
    date: '2026-11-16',
    status: '已完成'
  },
  {
    name: '李同学',
    position: '技术实习生',
    date: '2026-11-15',
    status: '进行中'
  },
  {
    name: '王同学',
    position: '技术实习生',
    date: '2026-11-14',
    status: '已完成'
  }
]

function goToResume() {
  router.push('/resume')
}

function goToInterview() {
  router.push('/interview')
}

function goToReport() {
  router.push('/report')
}
</script>

<style scoped>
.dashboard {
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

.statistics {
  margin-bottom: 24px;
}

.stat-card {
  border: none;
  border-radius: 10px;
}

.stat-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.stat-title {
  color: #909399;
  font-size: 14px;
  margin: 0 0 12px;
}

.stat-content h2 {
  margin: 0 0 8px;
  font-size: 28px;
  color: #303133;
}

.stat-content span {
  color: #a8abb2;
  font-size: 12px;
}

.stat-icon {
  width: 54px;
  height: 54px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.section-card {
  margin-bottom: 24px;
  border: none;
  border-radius: 10px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
}

.quick-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #f8fafc;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.quick-item:hover {
  background: #ecf5ff;
}

.quick-item h3 {
  font-size: 15px;
  margin: 0 0 8px;
  color: #303133;
}

.quick-item p {
  font-size: 12px;
  margin: 0;
  color: #909399;
}

.footer-tip {
  text-align: center;
  color: #c0c4cc;
  font-size: 12px;
  padding: 10px 0;
}
</style>
