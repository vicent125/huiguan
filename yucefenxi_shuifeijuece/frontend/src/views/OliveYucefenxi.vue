<template>
  <main class="page-shell">
    <header class="hero">
      <div>
        <p class="eyebrow">油橄榄 · 水肥预测 v2.1</p>
        <h1>土壤水分与水肥预算</h1>
        <p class="subtitle">基于连续 15 天传感器历史预测未来 1–3 天土壤含水量，并计算灌溉与施肥预算。</p>
      </div>
      <el-tag :type="healthOk ? 'success' : 'info'" size="large">
        {{ healthOk ? '预测服务正常' : '等待检测服务' }}
      </el-tag>
    </header>

    <el-alert
      title="预测结果仅用于辅助决策，不会自动向设备下发指令；示例数据是历史演示，不代表当前果园实况。"
      type="warning"
      :closable="false"
      show-icon
      class="notice"
    />

    <section class="workspace">
      <el-card class="input-card" shadow="never">
        <template #header>
          <div class="card-header">
            <div>
              <strong>预测输入</strong>
              <span>可加载内置示例后直接运行，也可粘贴现场 JSON 数据</span>
            </div>
            <el-button @click="loadExample">加载完整示例</el-button>
          </div>
        </template>

        <el-input
          v-model="requestText"
          type="textarea"
          :rows="24"
          resize="vertical"
          spellcheck="false"
          class="json-input"
        />
        <div class="actions">
          <el-button type="primary" size="large" :loading="loading" @click="runPrediction">
            生成预测
          </el-button>
          <el-button size="large" @click="formatJson">格式化 JSON</el-button>
        </div>
      </el-card>

      <el-card class="summary-card" shadow="never">
        <template #header><strong>运行摘要</strong></template>
        <el-empty v-if="!result" description="加载示例并生成预测后，结果将在这里显示" />
        <template v-else>
          <div class="summary-grid">
            <div class="metric">
              <span>区域 / 站点</span>
              <b>{{ result.region }} / {{ requestPayload.site_id || '未提供' }}</b>
            </div>
            <div class="metric"><span>数据截止日期</span><b>{{ result.as_of_date }}</b></div>
            <div class="metric"><span>模型状态</span><b>{{ statusText(result.moisture_forecast.status) }}</b></div>
            <div class="metric"><span>自动执行</span><b>{{ result.can_auto_execute ? '允许' : '禁止' }}</b></div>
          </div>
          <el-alert
            v-if="result.moisture_forecast.warning"
            :title="result.moisture_forecast.warning"
            type="info"
            :closable="false"
            class="result-alert"
          />
          <div ref="chartRef" class="chart"></div>
        </template>
      </el-card>
    </section>

    <template v-if="result">
      <el-card class="result-card" shadow="never">
        <template #header><strong>土壤水分预测</strong></template>
        <el-table :data="result.moisture_forecast.daily || []" stripe empty-text="当前输入不足或站点尚未完成本地验证">
          <el-table-column prop="date" label="日期" min-width="120" />
          <el-table-column label="含水量 (m³/m³)" min-width="150">
            <template #default="scope">{{ numberText(scope.row.vwc_m3_m3) }}</template>
          </el-table-column>
          <el-table-column label="历史 90% 区间" min-width="190">
            <template #default="scope">{{ numberText(scope.row.lower90) }} – {{ numberText(scope.row.upper90) }}</template>
          </el-table-column>
          <el-table-column prop="model" label="模型" min-width="150" />
        </el-table>
        <p v-if="result.moisture_forecast.missing?.length" class="missing-inputs">
          仍需输入：{{ result.moisture_forecast.missing.join('、') }}
        </p>
      </el-card>

      <section class="two-column">
        <el-card class="result-card" shadow="never">
          <template #header>
            <div class="result-title"><strong>灌溉预算</strong><el-tag>{{ statusText(result.irrigation.status) }}</el-tag></div>
          </template>
          <el-table :data="result.irrigation.daily || []" stripe empty-text="缺少灌溉计算参数">
            <el-table-column prop="date" label="日期" min-width="110" />
            <el-table-column prop="gross_irrigation_mm" label="毛灌水量 (mm)" min-width="135" />
            <el-table-column prop="irrigation_l" label="全园用水 (L)" min-width="125">
              <template #default="scope">{{ scope.row.irrigation_l ?? '需提供面积' }}</template>
            </el-table-column>
          </el-table>
          <p v-if="result.irrigation.missing?.length" class="missing-inputs">仍需输入：{{ result.irrigation.missing.join('、') }}</p>
        </el-card>

        <el-card class="result-card" shadow="never">
          <template #header>
            <div class="result-title"><strong>施肥预算</strong><el-tag>{{ statusText(result.fertilizer.status) }}</el-tag></div>
          </template>
          <el-table :data="result.fertilizer.daily || []" stripe empty-text="缺少施肥计算参数">
            <el-table-column prop="date" label="日期" min-width="110" />
            <el-table-column label="N (kg/ha)"><template #default="scope">{{ scope.row.nutrients_kg_ha?.N }}</template></el-table-column>
            <el-table-column label="P₂O₅ (kg/ha)" min-width="115"><template #default="scope">{{ scope.row.nutrients_kg_ha?.P2O5 }}</template></el-table-column>
            <el-table-column label="K₂O (kg/ha)" min-width="110"><template #default="scope">{{ scope.row.nutrients_kg_ha?.K2O }}</template></el-table-column>
          </el-table>
          <p v-if="result.fertilizer.missing?.length" class="missing-inputs">仍需输入：{{ result.fertilizer.missing.join('、') }}</p>
        </el-card>
      </section>

      <el-card class="result-card raw-card" shadow="never">
        <template #header><strong>完整计算结果</strong></template>
        <pre>{{ JSON.stringify(result, null, 2) }}</pre>
      </el-card>
    </template>
  </main>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { shengchengYuce } from '../api/yucejuece'
import request from '../api/qingqiu'

const starter = {
  region: '雅安',
  site_id: 'Site1',
  as_of_date: '2023-12-31',
  days: 3,
  history_daily: [],
}

const requestText = ref(JSON.stringify(starter, null, 2))
const result = ref(null)
const loading = ref(false)
const healthOk = ref(false)
const chartRef = ref(null)
let chart = null

const requestPayload = computed(() => {
  try { return JSON.parse(requestText.value) } catch { return {} }
})

const statusMap = {
  historical_model_needs_local_confirmation: '模型已运行，需本地确认',
  outside_training_sites: '超出已验证站点',
  needs_inputs: '需要补充输入',
  scenario_estimate: '情景预算',
  budget_schedule_not_ml_optimum: '预算排程（非机器学习最优值）',
  model_missing: '模型文件缺失',
}

function statusText(status) { return statusMap[status] || status || '未知' }
function numberText(value) { return Number.isFinite(value) ? Number(value).toFixed(4) : '—' }

async function loadExample() {
  try {
    const response = await fetch('/olive-sensor-request.json')
    if (!response.ok) throw new Error('示例文件读取失败')
    requestText.value = JSON.stringify(await response.json(), null, 2)
    ElMessage.success('已加载 15 天完整传感器示例')
  } catch (error) { ElMessage.error(error.message) }
}

function formatJson() {
  try {
    requestText.value = JSON.stringify(JSON.parse(requestText.value), null, 2)
    ElMessage.success('JSON 格式正确')
  } catch (error) { ElMessage.error(`JSON 格式错误：${error.message}`) }
}

async function runPrediction() {
  let payload
  try { payload = JSON.parse(requestText.value) }
  catch (error) { ElMessage.error(`JSON 格式错误：${error.message}`); return }

  loading.value = true
  try {
    const response = await shengchengYuce(payload)
    if (response.code !== 200) throw new Error(response.message || '预测失败')
    result.value = response.data
    ElMessage.success('预测计算完成')
    await nextTick()
    renderChart()
  } catch (error) {
    result.value = null
    ElMessage.error(error.response?.data?.message || error.message || '无法连接预测服务')
  } finally { loading.value = false }
}

function renderChart() {
  if (!chartRef.value || !result.value) return
  chart?.dispose()
  chart = echarts.init(chartRef.value)
  const rows = result.value.moisture_forecast.daily || []
  chart.setOption({
    color: ['#17735f', '#8fb8a7'],
    tooltip: { trigger: 'axis' },
    legend: { data: ['预测含水量', '历史上界'] },
    grid: { left: 48, right: 24, top: 45, bottom: 36 },
    xAxis: { type: 'category', data: rows.map((row) => row.date) },
    yAxis: { type: 'value', name: 'm³/m³', scale: true },
    series: [
      { name: '预测含水量', type: 'line', smooth: true, symbolSize: 9, data: rows.map((row) => row.vwc_m3_m3) },
      { name: '历史上界', type: 'line', lineStyle: { type: 'dashed' }, data: rows.map((row) => row.upper90) },
    ],
  })
}

onMounted(async () => {
  try {
    const response = await request.get('/api/olive/health')
    healthOk.value = response.status === 'ok'
  } catch { healthOk.value = false }
})

onBeforeUnmount(() => chart?.dispose())
</script>

<style scoped>
.page-shell { min-height: 100vh; padding: 32px; background: #f4f7f3; color: #18332b; }
.hero { max-width: 1440px; margin: 0 auto 20px; display: flex; justify-content: space-between; gap: 24px; align-items: flex-start; }
.eyebrow { margin: 0 0 8px; color: #17735f; font-weight: 700; letter-spacing: .08em; }
h1 { margin: 0; font-size: clamp(28px, 4vw, 44px); }
.subtitle { margin: 12px 0 0; color: #61736d; }
.notice, .workspace, .result-card, .two-column { max-width: 1440px; margin-left: auto; margin-right: auto; }
.notice { margin-bottom: 20px; }
.workspace { display: grid; grid-template-columns: minmax(430px, .9fr) minmax(480px, 1.1fr); gap: 20px; }
.card-header, .result-title { display: flex; justify-content: space-between; align-items: center; gap: 16px; }
.card-header span { display: block; margin-top: 5px; color: #7a8984; font-size: 13px; }
.json-input :deep(textarea) { font-family: Consolas, 'Courier New', monospace; line-height: 1.5; }
.actions { display: flex; gap: 8px; margin-top: 16px; }
.summary-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.metric { padding: 16px; border: 1px solid #dce7e1; border-radius: 10px; background: #f8fbf9; }
.metric span { display: block; color: #71817b; margin-bottom: 8px; font-size: 13px; }
.metric b { font-size: 16px; }
.result-alert { margin-top: 16px; }
.chart { width: 100%; height: 340px; margin-top: 16px; }
.result-card { margin-top: 20px; }
.two-column { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.two-column .result-card { min-width: 0; }
.missing-inputs { padding: 12px; margin: 14px 0 0; border-radius: 8px; color: #8a5b14; background: #fff7e8; overflow-wrap: anywhere; }
.raw-card pre { max-height: 420px; overflow: auto; padding: 16px; border-radius: 8px; background: #13251f; color: #d8eee5; white-space: pre-wrap; overflow-wrap: anywhere; }
:deep(.el-card) { border-color: #dce7e1; border-radius: 14px; }
:deep(.el-button--primary) { background: #17735f; border-color: #17735f; }
@media (max-width: 980px) { .workspace, .two-column { grid-template-columns: 1fr; } .page-shell { padding: 18px; } }
@media (max-width: 560px) { .hero { flex-direction: column; } .summary-grid { grid-template-columns: 1fr; } }
</style>
