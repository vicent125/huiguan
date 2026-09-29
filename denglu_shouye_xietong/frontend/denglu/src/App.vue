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
// 引入axios
import axios from 'axios'


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

// 真实对接后端登录函数
async function handleLogin() {
  submitted.value = true
  message.value = ''
  loginSuccess.value = false
  // 前端空校验
  if (!form.username || !form.password) return
  loading.value = true
  try {
    // 发起POST请求，代理自动转发到5000端口后端
    const res = await axios.post('/api/denglu', {
      username: form.username,
      password: form.password
    })
    const result = res.data
    if (result.code === 200) {
      loginSuccess.value = true
      message.value = result.message
      // 存储后端返回token
      localStorage.setItem('token', result.data.token)
      // 记住密码逻辑
      if (form.remember) {
        localStorage.setItem('rememberedAccount', JSON.stringify(form))
      } else {
        localStorage.removeItem('rememberedAccount')
      }
      //登录成功跳转首页

    } else {
      message.value = result.message
    }
  } catch (err) {
    // 后端未启动/网络异常提示
    message.value = "无法连接后端，请确认Flask服务已经启动"
  } finally {
    loading.value = false
  }
}
</script>