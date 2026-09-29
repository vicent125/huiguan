<template>
  <article class="chart-card">
    <header class="chart-card__header">
      <div>
        <span>{{ subtitle }}</span>
        <h3>{{ title }}</h3>
      </div>

      <span class="chart-card__tag">
        {{ tag }}
      </span>
    </header>

    <div
      ref="chartRef"
      class="chart-card__body"
    ></div>
  </article>
</template>

<script setup>
import * as echarts from 'echarts'
import {
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  watch
} from 'vue'

const props = defineProps({
  title: {
    type: String,
    required: true
  },
  subtitle: {
    type: String,
    default: 'DATA ANALYSIS'
  },
  tag: {
    type: String,
    default: '实时数据'
  },
  option: {
    type: Object,
    required: true
  }
})

const chartRef = ref(null)

let chartInstance = null
let resizeObserver = null

const CHART_COLORS = ['#2D9B6C', '#94A3B8', '#D97706', '#60A5FA']

function renderChart() {
  if (!chartRef.value) {
    return
  }

  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }

  const mergedOption = {
    color: CHART_COLORS,
    ...props.option
  }

  chartInstance.setOption(mergedOption, true)
  chartInstance.resize()
}

onMounted(async () => {
  await nextTick()

  renderChart()

  resizeObserver = new ResizeObserver(() => {
    chartInstance?.resize()
  })

  resizeObserver.observe(chartRef.value)
})

watch(
  () => props.option,
  () => {
    renderChart()
  },
  {
    deep: true
  }
)

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  chartInstance?.dispose()

  resizeObserver = null
  chartInstance = null
})
</script>