<template>
  <div class="weather-forecast">
    <div class="container">
      <h1>未来三天天气预报</h1>

      <div v-if="loading" class="loading">加载天气数据中...</div>
      <el-alert v-else-if="error" :title="error" type="error" show-icon :closable="false" />

      <template v-else>
        <div ref="tpbiao" class="chart-container"></div>
        <div ref="rabiao" class="chart-container"></div>

        <div class="analysis-box">
          <h3>天气分析建议</h3>
          <ul>
            <li>最高温度：{{ tmax[0] }}°C ~ {{ tmax[2] }}°C</li>
            <li>最低温度：{{ tmin[0] }}°C ~ {{ tmin[2] }}°C</li>
            <li>降雨概率：{{ rgailv[0] }}% → {{ rgailv[1] }}% → {{ rgailv[2] }}%</li>
            <li>{{ weatherAdvice }}</li>
          </ul>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick, computed } from 'vue'
import * as echarts from 'echarts'
import api from '../api'

const tpbiao = ref(null)
const rabiao = ref(null)

const days = ref(['今天', '明天', '后天'])
const tmax = ref([32, 30, 28])
const tmin = ref([25, 24, 23])
const rgailv = ref([10, 40, 70])
const loading = ref(true)
const error = ref(null)

let tchart = null
let rchart = null

const weatherAdvice = computed(() => {
  const maxRain = Math.max(...rgailv.value)
  if (maxRain >= 60) {
    return '后天降雨概率较高，出门请记得带伞，建议减少户外灌溉作业。'
  } else if (maxRain >= 30) {
    return '近期有降雨可能，注意调整灌溉计划。'
  } else {
    return '天气晴朗，蒸发量较大，建议适当增加灌溉频次。'
  }
})

// 防抖
function debounce(fn, delay = 150) {
  let timer = null
  return (...args) => {
    clearTimeout(timer)
    timer = setTimeout(() => fn(...args), delay)
  }
}

const loadWeatherData = async () => {
  loading.value = true
  error.value = null
  try {
    const res = await api.get('/tianqifenxi/tianqiyubao')
    if (res.data.code === 200) {
      const data = res.data.data
      // 根据后端返回格式适配
      if (data.forecast_list && data.forecast_list.length >= 3) {
        days.value = data.forecast_list.map((item, idx) => {
          const labels = ['今天', '明天', '后天']
          return labels[idx] || item.forecast_date || `第${idx + 1}天`
        })
        tmax.value = data.forecast_list.map(item => item.max_temp ?? 30)
        tmin.value = data.forecast_list.map(item => item.min_temp ?? 20)
        rgailv.value = data.forecast_list.map(item => item.rain_probability ?? 0)
      }
    } else {
      error.value = res.data.message || '加载失败'
    }
  } catch (err) {
    console.error('加载天气数据失败:', err)
    error.value = '加载天气数据失败: ' + (err.response?.data?.message || err.message)
  } finally {
    loading.value = false
  }
}

const initCharts = async () => {
  await nextTick()
  if (!tpbiao.value || !rabiao.value) return

  // 方案A 图表色
  const chartColors = ['#2D9B6C', '#94A3B8', '#D97706', '#60A5FA']

  tchart = echarts.init(tpbiao.value)
  const tempOption = {
    color: chartColors,
    title: { text: '未来三天温度趋势', left: 'center' },
    tooltip: { trigger: 'axis' },
    legend: { data: ['最高温度', '最低温度'], bottom: 0 },
    grid: { left: '3%', right: '4%', bottom: '10%', containLabel: true },
    xAxis: { type: 'category', boundaryGap: true, data: days.value },
    yAxis: { type: 'value', name: '温度 (°C)' },
    series: [
      {
        name: '最高温度', type: 'line', data: tmax.value,
        symbol: 'circle', symbolSize: 12, label: { show: true, position: 'top', formatter: '{c}°C' }
      },
      {
        name: '最低温度', type: 'line', data: tmin.value,
        symbol: 'circle', symbolSize: 12, label: { show: true, position: 'bottom', formatter: '{c}°C' }
      }
    ]
  }
  tchart.setOption(tempOption)

  rchart = echarts.init(rabiao.value)
  const rainOption = {
    color: chartColors,
    title: { text: '未来三天降雨概率', left: 'center' },
    tooltip: { trigger: 'axis', formatter: '{b}: {c}%' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: days.value },
    yAxis: { type: 'value', name: '降雨概率 (%)', min: 0, max: 100 },
    series: [{
      data: rgailv.value, type: 'bar', barWidth: '40%',
      label: { show: true, position: 'top', formatter: '{c}%' }
    }]
  }
  rchart.setOption(rainOption)
}

const handleResize = debounce(() => {
  tchart?.resize()
  rchart?.resize()
})

onMounted(async () => {
  await loadWeatherData()
  await initCharts()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  tchart?.dispose()
  rchart?.dispose()
})
</script>

<style scoped>
.weather-forecast {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  background: #FAFAF8;
}
.container {
  max-width: 800px;
  width: 100%;
  background: #FFFFFF;
  padding: 30px;
  border: 1px solid #E7E5E4;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(28, 25, 23, 0.06);
}
h1 {
  text-align: center;
  color: #1C1917;
  margin-bottom: 30px;
}
.loading, .error {
  text-align: center;
  padding: 40px;
  color: #78716C;
}
.error {
  color: #B45309;
}
.chart-container {
  width: 100%;
  height: 350px;
  margin-bottom: 30px;
  background: #FFFFFF;
  border: 1px solid #E7E5E4;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(28, 25, 23, 0.06);
  padding: 10px;
}
.analysis-box {
  background-color: #FFFFFF;
  border: 1px solid #E7E5E4;
  border-left: 5px solid #0F766F;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(28, 25, 23, 0.06);
  margin-top: 20px;
}
.analysis-box h3 {
  margin-top: 0;
  color: #0F766F;
}
.analysis-box ul {
  list-style: none;
  padding: 0;
  margin: 0;
}
.analysis-box li {
  padding: 8px 0;
  border-bottom: 1px dashed #E7E5E4;
  font-size: 16px;
  color: #1C1917;
}
.analysis-box li:last-child {
  border-bottom: none;
}
</style>
