<template>
  <!-- 必须给图表容器指定宽高，否则图表不显示 -->
  <div ref="chartRef" style="width: 100%; height: 400px;"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
// 导入 echarts 核心库
import * as echarts from 'echarts'

// 获取 DOM 元素的引用
const chartRef = ref(null)

// 页面加载完毕时初始化图表
onMounted(() => {
  // 1. 初始化图表实例
  const myChart = echarts.init(chartRef.value)

  // 2. 指定图表的配置项和数据（这里是演示数据）
  // 方案A图表色：#2D9B6C #94A3B8 #D97706 #60A5FA
  const option = {
    color: ['#2D9B6C', '#94A3B8', '#D97706', '#60A5FA'],
    title: { text: 'ECharts 入门示例' },
    tooltip: {},
    xAxis: { data: ['衬衫', '羊毛衫', '雪纺衫', '裤子', '高跟鞋', '袜子'] },
    yAxis: {},
    series: [{
      name: '销量',
      type: 'bar',
      data: [5, 20, 36, 10, 10, 20]
    }]
  }

  // 3. 使用刚指定的配置项和数据显示图表
  myChart.setOption(option)

  // 4. 【重要】监听窗口大小变化，让图表自适应
  const resizeHandler = () => { myChart.resize() }
  window.addEventListener('resize', resizeHandler)

  // 5. 组件销毁时，清理图表实例和监听器（防止内存泄漏）
  onUnmounted(() => {
    window.removeEventListener('resize', resizeHandler)
    myChart.dispose()
  })
})
</script>