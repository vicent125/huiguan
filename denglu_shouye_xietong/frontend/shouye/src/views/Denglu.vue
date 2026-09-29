<template>
  <div class="login-page">
    <!-- 左侧介绍区域 -->
    <section class="login-banner">
      <div class="brand">
        <div class="brand-logo">
          田
        </div>
        <div class="brand-text">
          <h1>智慧农情</h1>
          <span>SMART AGRICULTURE</span>
        </div>
      </div>
      <div class="banner-content">
        <span class="banner-subtitle">
          SMART FARM MANAGEMENT
        </span>
        <h2>
          智慧农情监测与<br />
          决策管理系统
        </h2>
        <p>
          统一管理作物、土壤、气象、灌溉和施肥数据，
          为农业生产提供智能化决策支持。
        </p>
        <div class="feature-list">
          <div class="feature-item">
            <span class="feature-number">01</span>
            <div>
              <strong>实时监测</strong>
              <p>实时掌握农田环境与作物生长情况</p>
            </div>
          </div>
          <div class="feature-item">
            <span class="feature-number">02</span>
            <div>
              <strong>智能决策</strong>
              <p>自动生成灌溉和施肥建议</p>
            </div>
          </div>
          <div class="feature-item">
            <span class="feature-number">03</span>
            <div>
              <strong>风险预警</strong>
              <p>及时发现天气、墒情和设备异常</p>
            </div>
          </div>
        </div>
      </div>
      <div class="banner-footer">
        智慧农业数字化管理平台
      </div>
    </section>
    <!-- 右侧登录区域 -->
    <section class="login-panel">
      <div class="login-card">
        <header class="login-header">
          <span>WELCOME BACK</span>
          <h2>登录管理系统</h2>
          <p>请输入账号和密码进入系统</p>
        </header>
        <form @submit.prevent="handleLogin">
          <!-- 账号 -->
          <div class="form-group">
            <label for="username">账号</label>
            <div
              class="input-box"
              :class="{
                'input-box--error':
                  submitted && !form.username
              }"
            >
              <span class="input-icon">◎</span>
              <input
                id="username"
                v-model.trim="form.username"
                type="text"
                placeholder="请输入账号"
                autocomplete="username"
                @input="clearMessage"
              />
            </div>
            <p
              v-if="submitted && !form.username"
              class="field-error"
            >
              请输入账号
            </p>
          </div>
          <!-- 密码 -->
          <div class="form-group">
            <label for="password">密码</label>
            <div
              class="input-box"
              :class="{
                'input-box--error':
                  submitted && !form.password
              }"
            >
              <span class="input-icon">◇</span>
              <input
                id="password"
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="请输入密码"
                autocomplete="current-password"
                @input="clearMessage"
              />
              <button
                class="show-password-button"
                type="button"
                @click="showPassword = !showPassword"
              >
                {{ showPassword ? '隐藏' : '显示' }}
              </button>
            </div>
            <p
              v-if="submitted && !form.password"
              class="field-error"
            >
              请输入密码
            </p>
          </div>
          <!-- 记住密码 -->
          <div class="form-options">
            <label class="remember-password">
              <input
                v-model="form.remember"
                type="checkbox"
              />
              <span class="checkbox-icon">✓</span>
              <span>记住密码</span>
            </label>
            <span class="account-tip">
              admin / 123456
            </span>
          </div>
          <!-- 错误提示 -->
          <div
            v-if="message"
            class="login-message"
            :class="{
              'login-message--success': loginSuccess
            }"
          >
            {{ message }}
          </div>
          <!-- 登录按钮 -->
          <button
            class="login-button"
            type="submit"
            :disabled="loading"
          >
            <template v-if="!loading">
              登录
            </template>
            <template v-else>
              <span class="loading-circle"></span>
              正在登录
            </template>
          </button>
        </form>
        <footer class="login-footer">
          <span></span>
          智慧农情管理系统
          <span></span>
        </footer>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

// 获取路由实例，用于登录跳转
const router = useRouter()

const showPassword = ref(false)
const submitted = ref(false)
const loading = ref(false)
const message = ref('')
const loginSuccess = ref(false)
const form = reactive({
  username: '',
  password: '',
  remember: false
})

// 页面加载读取记住账号
onMounted(() => {
  const savedAccount = localStorage.getItem('rememberedAccount')
  if (!savedAccount) return
  try {
    const account = JSON.parse(savedAccount)
    form.username = account.username || ''
    form.password = account.password || ''
    form.remember = true
  } catch (err) {
    localStorage.removeItem('rememberedAccount')
  }
})

// 清空提示文字
function clearMessage() {
  message.value = ''
  loginSuccess.value = false
}

// 登录提交函数
async function handleLogin() {
  submitted.value = true
  message.value = ''
  loginSuccess.value = false
  // 前端空校验
  if (!form.username || !form.password) return
  loading.value = true
  try {
    const res = await axios.post('/api/denglu', {
      username: form.username,
      password: form.password
    })
    const result = res.data
    if (result.code === 200) {
      loginSuccess.value = true
      message.value = result.message
      // 存储token
      localStorage.setItem('token', result.data.token)
      // 记住账号逻辑
      if (form.remember) {
        localStorage.setItem('rememberedAccount', JSON.stringify(form))
      } else {
        localStorage.removeItem('rememberedAccount')
      }
      // 登录成功跳转到首页 /
      router.push('/home')
    } else {
      message.value = result.message
    }
  } catch (err) {
    message.value = "无法连接后端，请确认Flask服务已经启动"
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
.login-page {
  width: 100vw;
  height: 100vh;
  display: flex;
  font-family: "Microsoft Yahei", sans-serif;
}
.login-banner {
  width: 55%;
  background: linear-gradient(135deg, #237c44, #35a75c);
  color: #fff;
  padding: 60px 80px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.brand {
  display: flex;
  align-items: center;
  gap: 16px;
}
.brand-logo {
  width: 50px;
  height: 50px;
  background: #fff;
  color: #237c44;
  font-size: 26px;
  font-weight: bold;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.brand-text h1 {
  font-size: 28px;
  line-height: 1;
}
.brand-text span {
  font-size: 13px;
  opacity: 0.8;
}
.banner-subtitle {
  font-size: 14px;
  letter-spacing: 2px;
  opacity: 0.8;
}
.banner-content h2 {
  font-size: 42px;
  line-height: 1.3;
  margin: 12px 0 20px;
}
.banner-content p {
  font-size: 16px;
  opacity: 0.9;
  line-height: 1.8;
  margin-bottom: 40px;
}
.feature-list {
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.feature-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}
.feature-number {
  width: 36px;
  height: 36px;
  border: 1px solid #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.feature-item strong {
  display: block;
  font-size: 18px;
  margin-bottom: 6px;
}
.feature-item p {
  font-size: 14px;
  opacity: 0.85;
  margin: 0;
}
.banner-footer {
  font-size: 14px;
  opacity: 0.7;
}
.login-panel {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f7faf8;
}
.login-card {
  width: 420px;
  background: #fff;
  border-radius: 16px;
  padding: 40px 36px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}
.login-header span {
  font-size: 13px;
  color: #666;
  letter-spacing: 1px;
}
.login-header h2 {
  font-size: 26px;
  color: #222;
  margin: 6px 0 8px;
}
.login-header p {
  color: #999;
  font-size: 14px;
  margin-bottom: 32px;
}
.form-group {
  margin-bottom: 24px;
}
.form-group label {
  display: block;
  font-size: 14px;
  color: #333;
  margin-bottom: 8px;
}
.input-box {
  display: flex;
  align-items: center;
  border: 1px solid #ddd;
  border-radius: 10px;
  padding: 0 14px;
  height: 48px;
  transition: border 0.2s;
}
.input-box--error {
  border-color: #e64340;
}
.input-icon {
  color: #999;
  margin-right: 12px;
}
.input-box input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 15px;
  color: #333;
}
.show-password-button {
  border: none;
  background: transparent;
  color: #237c44;
  font-size: 13px;
  cursor: pointer;
}
.field-error {
  color: #e64340;
  font-size: 13px;
  margin-top: 6px;
}
.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.remember-password {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #555;
  cursor: pointer;
}
.account-tip {
  font-size: 13px;
  color: #999;
}
.login-message {
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 14px;
  margin-bottom: 20px;
  background: #ffe9e9;
  color: #e64340;
}
.login-message--success {
  background: #e6f7ef;
  color: #237c44;
}
.login-button {
  width: 100%;
  height: 48px;
  border: none;
  border-radius: 10px;
  background: #237c44;
  color: #fff;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
.login-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}
.loading-circle {
  width: 16px;
  height: 16px;
  border: 2px solid #fff;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
.login-footer {
  text-align: center;
  margin-top: 30px;
  font-size: 13px;
  color: #aaa;
  display: flex;
  align-items: center;
  gap: 10px;
}
.login-footer span {
  flex: 1;
  height: 1px;
  background: #eee;
}
</style>
