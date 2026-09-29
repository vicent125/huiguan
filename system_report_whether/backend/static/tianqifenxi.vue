<template>
  <div class="weather-forecast">
    <div class="container">
      <h1>未来三天天气预报</h1>

      <div v-if="loading" class="loading">加载天气数据中...</div>
      <div v-else-if="error" class="error">{{ error }}</div>

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
import axios from 'axios'
import * as echarts from 'echarts'

const API_BASE = ''

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
    const res = await axios.get(`${API_BASE}/api/tianqifenxi/tianqiyubao`)
    if (res.data.code === 200) {
      const data = res.data.data
      // 根据后端返回格式适配
      if (data.forecast && data.forecast.length >= 3) {
        days.value = data.forecast.map((item, idx) => {
          const labels = ['今天', '明天', '后天']
          return item.date || labels[idx] || `第${idx+1}天`
        })
        tmax.value = data.forecast.map(item => item.max_temp || item.tmax || 30)
        tmin.value = data.forecast.map(item => item.min_temp || item.tmin || 20)
        rgailv.value = data.forecast.map(item => item.rain_prob || item.rgailv || 0)
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

  tchart = echarts.init(tpbiao.value)
  const tempOption = {
    title: { text: '未来三天温度趋势', left: 'center' },
    tooltip: { trigger: 'axis' },
    legend: { data: ['最高温度', '最低温度'], bottom: 0 },
    grid: { left: '3%', right: '4%', bottom: '10%', containLabel: true },
    xAxis: { type: 'category', boundaryGap: true, data: days.value },
    yAxis: { type: 'value', name: '温度 (°C)' },
    series: [
      {
        name: '最高温度', type: 'line', data: tmax.value, color: '#ff4d4f',
        symbol: 'circle', symbolSize: 12, label: { show: true, position: 'top', formatter: '{c}°C' }
      },
      {
        name: '最低温度', type: 'line', data: tmin.value, color: '#52c41a',
        symbol: 'circle', symbolSize: 12, label: { show: true, position: 'bottom', formatter: '{c}°C' }
      }
    ]
  }
  tchart.setOption(tempOption)

  rchart = echarts.init(rabiao.value)
  const rainOption = {
    title: { text: '未来三天降雨概率', left: 'center' },
    tooltip: { trigger: 'axis', formatter: '{b}: {c}%' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: days.value },
    yAxis: { type: 'value', name: '降雨概率 (%)', min: 0, max: 100 },
    series: [{
      data: rgailv.value, type: 'bar', barWidth: '40%', color: '#87ceeb',
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
}
.container {
  max-width: 800px;
  width: 100%;
  background: #fff;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
}
h1 {
  text-align: center;
  color: #333;
  margin-bottom: 30px;
}
.loading, .error {
  text-align: center;
  padding: 40px;
  color: #666;
}
.error {
  color: #ff4d4f;
}
.chart-container {
  width: 100%;
  height: 350px;
  margin-bottom: 30px;
}
.analysis-box {
  background-color: #f8f9fa;
  border-left: 5px solid #1890ff;
  padding: 20px;
  border-radius: 0 8px 8px 0;
  margin-top: 20px;
}
.analysis-box h3 {
  margin-top: 0;
  color: #1890ff;
}
.analysis-box ul {
  list-style: none;
  padding: 0;
  margin: 0;
}
.analysis-box li {
  padding: 8px 0;
  border-bottom: 1px dashed #e8e8e8;
  font-size: 16px;
  color: #555;
}
.analysis-box li:last-child {
  border-bottom: none;
}
</style>
