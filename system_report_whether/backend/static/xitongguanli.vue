<template>
  <div class="bg-gray-50 text-gray-800 font-sans min-h-screen pt-8">
    <div class="max-w-5xl mx-auto p-6">

      <!-- 头部 -->
      <header class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900 flex items-center gap-2">
          <span class="text-blue-600"></span> 系统管理
        </h1>
      </header>

      <!-- 导航 Tabs -->
      <div class="border-b border-gray-200 mb-6">
        <nav class="flex space-x-8" aria-label="Tabs">
          <button 
            @click="activeTab = 'yuzhishezhi'" 
            :class="[
              'tab-btn py-4 px-1 text-sm font-medium',
              activeTab === 'yuzhishezhi' 
                ? 'border-b-2 border-blue-600 text-blue-600' 
                : 'border-b-2 border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            ]"
          >
            预警阈值设置
          </button>

          <button 
            @click="activeTab = 'caozuorizhi'; loadLogs()" 
            :class="[
              'tab-btn py-4 px-1 text-sm font-medium',
              activeTab === 'caozuorizhi' 
                ? 'border-b-2 border-blue-600 text-blue-600' 
                : 'border-b-2 border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            ]"
          >
            操作日志
          </button>
        </nav>
      </div>

      <main class="bg-white rounded-xl shadow-xs border border-gray-100 p-6">

        <!-- 预警阈值设置 -->
        <section v-show="activeTab === 'yuzhishezhi'" class="tab-content">
          <div class="mb-6">
            <h2 class="text-xl font-semibold text-gray-900">预警阈值设置</h2>
          </div>

          <form @submit.prevent="handleFormSubmit" class="space-y-6 max-w-xl">
            <div class="grid grid-cols-1 gap-6 sm:grid-cols-2">
              <div>
                <label for="maxzhi" class="block text-sm font-medium text-gray-700 mb-2">阈值最大值</label>
                <input 
                  type="number" 
                  id="maxzhi" 
                  v-model.number="formData.maxZhi" 
                  required 
                  placeholder="请输入最大值" 
                  class="block w-full rounded-lg border border-gray-300 px-4 py-2.5 text-gray-900 shadow-xs focus:border-blue-500 focus:ring-2 focus:ring-blue-200 focus:outline-hidden transition"
                >
              </div>

              <div>
                <label for="minzhi" class="block text-sm font-medium text-gray-700 mb-2">阈值最小值</label>
                <input 
                  type="number" 
                  id="minzhi" 
                  v-model.number="formData.minZhi" 
                  required 
                  placeholder="请输入最小值" 
                  class="block w-full rounded-lg border border-gray-300 px-4 py-2.5 text-gray-900 shadow-xs focus:border-blue-500 focus:ring-2 focus:ring-blue-200 focus:outline-hidden transition"
                >
              </div>
            </div>

            <div>
              <label for="jibie" class="block text-sm font-medium text-gray-700 mb-2">预警等级</label>
              <select 
                id="jibie" 
                v-model="formData.jiBie" 
                required
                class="block w-full rounded-lg border border-gray-300 px-4 py-2.5 text-gray-900 shadow-xs focus:border-blue-500 focus:ring-2 focus:ring-blue-200 focus:outline-hidden transition bg-white"
              >
                <option value="" disabled>请选择预警等级</option>
                <option value="提示">提示</option>
                <option value="次要">次要</option>
                <option value="重要">重要</option>
                <option value="紧急">紧急</option>
              </select>
            </div>

            <div class="pt-2">
              <button 
                type="submit" 
                :disabled="saving"
                class="w-full sm:w-auto px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg shadow-md hover:shadow-lg focus:outline-hidden focus:ring-2 focus:ring-blue-400 transition cursor-pointer disabled:opacity-50"
              >
                {{ saving ? '保存中...' : '保存配置' }}
              </button>
            </div>
          </form>
        </section>

        <!-- 操作日志 -->
        <section v-show="activeTab === 'caozuorizhi'" class="tab-content">
          <div class="mb-6 flex justify-between items-center">
            <div>
              <h2 class="text-xl font-semibold text-gray-900">操作日志</h2>
            </div>
            <span class="inline-flex items-center rounded-md bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700 ring-1 ring-blue-600/10 ring-inset">
              实时更新
            </span>
          </div>

          <div v-if="logLoading" class="text-center py-8 text-gray-400">加载中...</div>
          <div v-else-if="logs.length === 0" class="text-center py-8 text-gray-400">暂无操作日志</div>

          <div v-else class="overflow-x-auto border border-gray-200 rounded-lg">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th scope="col" class="px-6 py-3.5 text-left text-sm font-semibold text-gray-900">操作时间</th>
                  <th scope="col" class="px-6 py-3.5 text-left text-sm font-semibold text-gray-900">操作类型</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200 bg-white">
                <tr 
                  v-for="log in logs" 
                  :key="log.id"
                  :class="{'bg-blue-50/50': log.isNew}"
                >
                  <td class="whitespace-nowrap px-6 py-4 text-sm text-gray-500 font-sans">
                    {{ log.time }}
                  </td>
                  <td 
                    :class="[
                      'whitespace-nowrap px-6 py-4 text-sm',
                      log.isNew ? 'text-blue-900 font-semibold' : 'text-gray-900 font-medium'
                    ]"
                  >
                    {{ log.action }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const API_BASE = ''

// 切换状态
const activeTab = ref('yuzhishezhi') 
const saving = ref(false)
const logLoading = ref(false)

// 表单数据绑定
const formData = ref({
  maxZhi: null,
  minZhi: null,
  jiBie: ''
})

// 列表数据 
const logs = ref([])

const getFormattedTime = () => {
  const now = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`
}

// 加载日志
const loadLogs = async () => {
  logLoading.value = true
  try {
    const res = await axios.get(`${API_BASE}/api/system/logs`)
    if (res.data.code === 200) {
      logs.value = res.data.data || []
    }
  } catch (err) {
    console.error('加载日志失败:', err)
    logs.value = []
  } finally {
    logLoading.value = false
  }
}

// 表单提交
const handleFormSubmit = async () => {
  const { maxZhi, minZhi, jiBie } = formData.value

  if (Number(minZhi) >= Number(maxZhi)) {
    alert('错误：最小值不能大于或等于最大值！')
    return
  }

  saving.value = true
  try {
    const res = await axios.post(`${API_BASE}/api/system/threshold`, {
      max_value: maxZhi,
      min_value: minZhi,
      level: jiBie
    })

    if (res.data.code === 200) {
      alert(`保存成功！
最大值：${maxZhi}
最小值：${minZhi}
预警等级：${jiBie}`)

      // 添加到本地日志
      logs.value.unshift({
        id: Date.now(),
        time: getFormattedTime(),
        action: `更新阈值配置 (最大:${maxZhi} / 最小:${minZhi} / 等级:${jiBie})`,
        isNew: true
      })
    } else {
      alert('保存失败：' + res.data.message)
    }
  } catch (err) {
    alert('保存失败：' + (err.response?.data?.message || err.message))
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadLogs()
})
</script>

<style scoped>
</style>
