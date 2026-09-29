<template>
  <div class="bg-slate-50 p-4 md:p-8">
    <div class="max-w-4xl mx-auto bg-white p-6 md:p-8 rounded-2xl shadow-xl border border-slate-100 print-card">

      <!-- 头部 -->
      <div class="mb-6 border-b border-slate-100 pb-4 flex justify-between items-center">
        <div>
          <h1 class="text-2xl font-bold text-slate-800 flex items-center gap-2">
            智能农业报告中心
          </h1>
          <p class="text-sm text-slate-400 mt-1">水肥一体化监控系统 / 数据分析</p>
        </div>
        <span class="no-print bg-emerald-100 text-emerald-800 text-xs px-2.5 py-1 rounded-full font-semibold">
          系统运行正常
        </span>
      </div>

      <!-- 列表页 -->
      <div v-if="currentView === 'liebiao'">
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-lg font-bold text-slate-700 flex items-center gap-2">
            <span class="w-1.5 h-5 bg-emerald-500 rounded-full"></span>
            报告列表
          </h2>
        </div>

        <div v-if="loading" class="text-center py-8 text-slate-400">加载中...</div>
        <div v-else-if="reports.length === 0" class="text-center py-8 text-slate-400">暂无报告数据</div>

        <div v-else class="overflow-hidden border border-slate-200 rounded-xl shadow-sm">
          <table class="w-full border-collapse bg-white text-left text-sm text-slate-600">
            <thead class="bg-slate-50 text-slate-700 font-semibold border-b border-slate-100">
              <tr>
                <th class="px-6 py-4">报告名称</th>
                <th class="px-6 py-4">生成时间</th>
                <th class="px-6 py-4 text-right">操作</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-for="report in reports" :key="report.id" class="hover:bg-slate-50 transition">
                <td class="px-6 py-4 font-medium text-slate-900">{{ report.report_title }}</td>
                <td class="px-6 py-4 text-slate-400">{{ report.create_time }}</td>
                <td class="px-6 py-4 text-right">
                  <button @click="viewReport(report.id)" class="bg-emerald-50 hover:bg-emerald-100 text-emerald-600 px-4 py-2 rounded-lg font-medium transition text-xs shadow-sm">
                    查看报告
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 详情页 -->
      <div v-if="currentView === 'baogao'" class="space-y-6">

        <div class="flex justify-between items-center border-b border-slate-100 pb-4 no-print">
          <button @click="currentView = 'liebiao'" class="text-slate-500 hover:text-slate-800 flex items-center gap-1 text-sm font-semibold transition">
            ← 返回列表
          </button>
          <span class="text-xs bg-slate-100 text-slate-500 px-2 py-1 rounded">详情及导出模式</span>
        </div>

        <div v-if="detailLoading" class="text-center py-8 text-slate-400">加载报告中...</div>

        <template v-else-if="currentReport">
          <div class="text-center md:text-left py-2">
            <h2 class="text-xl font-bold text-slate-800">{{ currentReport.report_title }}</h2>
            <p class="text-xs text-slate-400 mt-1">报告生成时间：{{ currentReport.create_time }}</p>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">

            <!-- 基础信息 -->
            <div class="p-4 bg-slate-50 rounded-xl border border-slate-100">
              <h3 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">基础信息</h3>
              <div class="grid grid-cols-1 gap-2 text-sm">
                <div v-for="(val, key) in formatJSON(currentReport.basic_info)" :key="key">
                  <span class="font-semibold text-slate-700">{{ formatKey(key) }}：</span>
                  <span class="text-slate-600">{{ val }}</span>
                </div>
                <div v-if="!formatJSON(currentReport.basic_info).crop_name && currentReport.growth_period">
                  <span class="font-semibold text-slate-700">生育期：</span>
                  <span class="text-slate-600">{{ currentReport.growth_period }}</span>
                </div>
              </div>
            </div>

            <!-- 天气 -->
            <div class="p-4 bg-amber-50/50 rounded-xl border border-amber-100">
              <h3 class="text-xs font-bold text-amber-500 uppercase tracking-wider mb-3">天气摘要</h3>
              <div class="grid grid-cols-1 gap-2 text-sm">
                <div v-for="(val, key) in formatJSON(currentReport.weather_summary)" :key="key">
                  <span class="font-semibold text-slate-700">{{ formatKey(key) }}：</span>
                  <span class="text-slate-600">{{ val }}</span>
                </div>
              </div>
            </div>

            <!-- 监测数据 -->
            <div class="p-4 bg-sky-50/60 rounded-xl border border-sky-100 md:col-span-2">
              <h3 class="text-xs font-bold text-sky-600 uppercase tracking-wider mb-3">监测数据摘要</h3>
              <div class="grid grid-cols-3 gap-2 text-center">
                <div v-for="(val, key) in formatJSON(currentReport.monitor_summary)" :key="key" class="bg-white p-2 rounded-lg border border-sky-100/50">
                  <span class="block text-xs text-slate-400">{{ formatKey(key) }}</span>
                  <span class="text-sm font-bold text-sky-600">{{ val }}</span>
                </div>
              </div>
            </div>

            <!-- 水肥分析 + 决策建议 -->
            <div class="p-4 bg-emerald-50/40 rounded-xl border border-emerald-100 md:col-span-2 space-y-3">
              <div>
                <h3 class="text-xs font-bold text-emerald-700 uppercase tracking-wider mb-1">水肥分析结果</h3>
                <div class="text-sm text-slate-600 leading-relaxed space-y-1">
                  <div v-for="(val, key) in formatJSON(currentReport.water_fertilizer_result)" :key="key">
                    <span class="font-semibold text-slate-700">{{ formatKey(key) }}：</span>
                    <span>{{ val }}</span>
                  </div>
                </div>
              </div>
              <div class="border-t border-emerald-100/50 pt-2">
                <h3 class="text-xs font-bold text-emerald-700 uppercase tracking-wider mb-1">决策建议</h3>
                <div class="text-sm text-slate-600 leading-relaxed space-y-1">
                  <div v-for="(val, key) in formatJSON(currentReport.decision_suggestion)" :key="key">
                    <span class="font-semibold text-slate-700">{{ formatKey(key) }}：</span>
                    <span>{{ val }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 风险说明 -->
            <div class="p-4 bg-rose-50/50 rounded-xl border border-rose-100">
              <h3 class="text-xs font-bold text-rose-500 uppercase tracking-wider mb-2">风险说明</h3>
              <div class="text-sm text-rose-950 leading-relaxed space-y-1">
                <div v-for="(val, key) in formatJSON(currentReport.risk_description)" :key="key">
                  <span class="font-semibold text-slate-700">{{ formatKey(key) }}：</span>
                  <span>{{ val }}</span>
                </div>
              </div>
            </div>

            <!-- 设备建议 -->
            <div class="p-4 bg-indigo-50/50 rounded-xl border border-indigo-100">
              <h3 class="text-xs font-bold text-indigo-500 uppercase tracking-wider mb-2">设备执行建议</h3>
              <div class="text-sm text-indigo-950 leading-relaxed space-y-1">
                <div v-for="(val, key) in formatJSON(currentReport.device_suggestion)" :key="key">
                  <span class="font-semibold text-slate-700">{{ formatKey(key) }}：</span>
                  <span>{{ val }}</span>
                </div>
              </div>
            </div>

          </div>
        </template>

        <!-- 底部 -->
        <div class="pt-6 border-t border-slate-100 flex justify-between items-center no-print">
          <span class="text-xs text-slate-400">准备就绪，可随时保存为 PDF</span>
          <button @click="dcPDF" class="bg-slate-800 hover:bg-slate-900 text-white px-5 py-2.5 rounded-xl text-xs font-semibold transition shadow-md hover:shadow-lg flex items-center gap-1.5">
            导出为 PDF
          </button>
        </div>

      </div>

    </div>
  </div>
</template>

<script>
import axios from 'axios'

const API_BASE = ''

// 字段名中文映射
const keyMap = {
  crop_name: '作物名称',
  growth_period: '生育期',
  soil_moisture: '土壤湿度',
  avg_max_temp: '平均最高温度',
  forecast_days: '预报天数',
  water_status: '水分状态',
  irrigation_suggestion: '灌溉建议',
  fertilization_suggestion: '施肥建议',
  drought_risk: '干旱风险',
  pest_risk: '病虫害风险',
  pump_runtime: '水泵运行时间',
  valve_status: '阀门状态',
  ph_value: 'pH值',
  ec_value: 'EC值',
  nitrogen: '氮含量',
  phosphorus: '磷含量',
  potassium: '钾含量'
}

export default {
  name: 'AgricultureReport',

  data() {
    return {
      currentView: 'liebiao',
      reports: [],
      currentReport: null,
      loading: false,
      detailLoading: false
    }
  },

  mounted() {
    this.loadReports()
  },

  methods: {
    formatKey(key) {
      return keyMap[key] || key
    },

    formatJSON(str) {
      if (!str) return {}
      if (typeof str === 'object') return str
      try {
        return JSON.parse(str)
      } catch (e) {
        return { '原始数据': str }
      }
    },

    async loadReports() {
      this.loading = true
      try {
        const res = await axios.get(`${API_BASE}/api/baogaozhongxin/baogaojilu`)
        if (res.data.code === 200) {
          this.reports = res.data.data.list || []
        }
      } catch (err) {
        console.error('加载报告列表失败:', err)
        this.reports = []
      } finally {
        this.loading = false
      }
    },

    async viewReport(id) {
      this.currentView = 'baogao'
      this.detailLoading = true
      try {
        const res = await axios.get(`${API_BASE}/api/baogaozhongxin/baogaojilu/${id}`)
        if (res.data.code === 200) {
          this.currentReport = res.data.data
        }
      } catch (err) {
        console.error('加载报告详情失败:', err)
        alert('加载报告失败: ' + (err.response?.data?.message || err.message))
      } finally {
        this.detailLoading = false
      }
    },

    dcPDF() {
      window.print()
    }
  }
}
</script>

<style scoped>
@media print {
  .no-print {
    display: none !important;
  }
  .print-card {
    box-shadow: none !important;
    border: 1px solid #e5e7eb !important;
  }
}
</style>
