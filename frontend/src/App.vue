<template>
  <el-container class="layout">
    <el-aside width="220px" class="sidebar">
      <div class="logo">
        AI 面试官
      </div>

      <el-menu
        router
        :default-active="$route.path"
        class="menu"
      >
        <el-menu-item index="/">
          <el-icon><House /></el-icon>
          <span>工作台</span>
        </el-menu-item>

        <el-menu-item index="/resume">
          <el-icon><Document /></el-icon>
          <span>简历管理</span>
        </el-menu-item>

        <el-menu-item index="/interview">
          <el-icon><ChatDotRound /></el-icon>
          <span>AI 面试</span>
        </el-menu-item>

        <el-menu-item index="/report">
          <el-icon><DataAnalysis /></el-icon>
          <span>面试报告</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        智能招聘与面试管理平台
      </el-header>

      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import {
  House,
  Document,
  ChatDotRound,
  DataAnalysis
} from '@element-plus/icons-vue'
</script>