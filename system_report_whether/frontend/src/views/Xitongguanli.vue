<template>
  <div class="system-page">
    <div class="system-container">

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

      <main class="system-panel">

        <!-- 预警 -->
        <section v-show="activeTab === 'yuzhishezhi'" class="tab-content">
          <div class="mb-6">
            <h2 class="text-xl font-semibold text-gray-900">预警阈值设置</h2>
          </div>

          <form @submit.prevent="handleFormSubmit" class="space-y-6 max-w-xl">
            <div class="grid grid-cols-1 gap-6 sm:grid-cols-2">
              <div>
                <label for="maxzhi" class="block text-sm font-medium text-gray-700 mb-2">阈值最大值</label>
                <el-input-number id="maxzhi" v-model="formData.maxZhi" :controls="false" placeholder="请输入最大值" />
              </div>

              <div>
                <label for="minzhi" class="block text-sm font-medium text-gray-700 mb-2">阈值最小值</label>
                <el-input-number id="minzhi" v-model="formData.minZhi" :controls="false" placeholder="请输入最小值" />
              </div>
            </div>

            <div>
              <label for="jibie" class="block text-sm font-medium text-gray-700 mb-2">预警等级</label>
              <el-select id="jibie" v-model="formData.jiBie" placeholder="请选择预警等级">
                <el-option label="提示" :value="1" />
                <el-option label="次要" :value="2" />
                <el-option label="重要" :value="3" />
                <el-option label="紧急" :value="4" />
              </el-select>
            </div>

            <div class="pt-2">
              <el-button native-type="submit" type="primary" :loading="saving">保存配置</el-button>
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
import { ElMessage } from 'element-plus'
import api from '../api'

// 切换
const activeTab = ref('yuzhishezhi') 
const saving = ref(false)
const logLoading = ref(false)
const thresholdId = ref(null)

// 数据绑定
const formData = ref({
  maxZhi: null,
  minZhi: null,
  jiBie: null
})

// 列表数据 
const logs = ref([])

const loadThreshold = async () => {
  try {
    const res = await api.get('/xitongguanli/yujingyuzhi', {
      params: { threshold_type: 'soil_moisture' }
    })
    const item = res.data.data?.[0]
    if (item) {
      thresholdId.value = item.id
      formData.value = {
        maxZhi: item.max_value,
        minZhi: item.min_value,
        jiBie: item.warning_level
      }
    }
  } catch (err) {
    ElMessage.error('加载阈值失败：' + (err.response?.data?.message || err.message))
  }
}

// 日志
const loadLogs = async () => {
  logLoading.value = true
  try {
    const res = await api.get('/xitongguanli/caozuorizhi')
    if (res.data.code === 200) {
      logs.value = (res.data.data?.list || []).map(log => ({
        id: log.id,
        time: log.operation_time,
        action: `${log.operation_type}：${log.operation_content || ''}`
      }))
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

  if (maxZhi === null || minZhi === null || jiBie === null) {
    ElMessage.warning('请完整填写阈值配置')
    return
  }
  if (Number(minZhi) >= Number(maxZhi)) {
    ElMessage.warning('最小值必须小于最大值')
    return
  }

  saving.value = true
  try {
    const payload = {
      threshold_type: 'soil_moisture',
      threshold_name: '土壤湿度预警',
      max_value: maxZhi,
      min_value: minZhi,
      warning_level: jiBie,
      description: '水肥一体化设备土壤湿度阈值',
      operator: '系统用户'
    }
    const url = thresholdId.value
      ? `/xitongguanli/yujingyuzhi/${thresholdId.value}`
      : '/xitongguanli/yujingyuzhi'
    const res = thresholdId.value
      ? await api.put(url, payload)
      : await api.post(url, payload)

    if (res.data.code === 200) {
      thresholdId.value = res.data.data.id
      ElMessage.success('阈值配置已保存')
      await loadLogs()
    } else {
      ElMessage.error('保存失败：' + res.data.message)
    }
  } catch (err) {
    ElMessage.error('保存失败：' + (err.response?.data?.message || err.message))
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadThreshold()
  loadLogs()
})
</script>

<style scoped>
.system-page {
  min-height: calc(100vh - 61px);
  padding: 32px 20px;
  background: #f4f7f5;
  text-align: left;
}

.system-container {
  width: min(100%, 980px);
  margin: 0 auto;
}

.system-panel {
  padding: 28px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 10px 24px rgb(15 23 42 / 7%);
}

header { margin-bottom: 24px; }
h1 { margin-bottom: 0; font-size: 28px; }
h2 { margin-bottom: 8px; font-size: 20px; }
nav { display: flex; gap: 24px; }
.tab-btn {
  padding: 14px 2px;
  border: 0;
  border-bottom: 2px solid transparent;
  color: #64748b;
  background: transparent;
  cursor: pointer;
}
.border-blue-600 { border-bottom-color: #2563eb; }
.text-blue-600 { color: #2563eb; }
.mb-6 { margin-bottom: 24px; }
.grid { display: grid; }
.grid-cols-1 { grid-template-columns: minmax(0, 1fr); }
.gap-6 { gap: 24px; }
.space-y-6 > * + * { margin-top: 24px; }
.max-w-xl { max-width: 576px; }
label { display: block; margin-bottom: 8px; font-size: 14px; font-weight: 500; }
.el-input-number, .el-select { width: 100%; }
.pt-2 { padding-top: 8px; }
.flex { display: flex; }
.justify-between { justify-content: space-between; }
.items-center { align-items: center; }
.text-center { text-align: center; }
.py-8 { padding-top: 32px; padding-bottom: 32px; }
.overflow-x-auto { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 14px 18px; border-bottom: 1px solid #e5e7eb; text-align: left; }
th { background: #f8fafc; font-weight: 600; }
.text-sm { font-size: 14px; }
.text-xs { font-size: 12px; }
.text-gray-400, .text-gray-500 { color: #64748b; }

@media (min-width: 640px) {
  .sm\:grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 640px) {
  .system-page { padding: 16px 12px; }
  .system-panel { padding: 18px; }
  nav { gap: 12px; }
}
</style>
