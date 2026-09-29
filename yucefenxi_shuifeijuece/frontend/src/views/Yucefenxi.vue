<template>
  <div class="page-box">
    <el-card>
      <template #header>
        <div class="card-title">预测分析</div>
      </template>

      <el-form :model="form" label-width="130px">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="作物ID">
              <el-input-number v-model="form.crop_id" :min="1" style="width: 100%" />
            </el-form-item>
          </el-col>

          <el-col :span="8">
            <el-form-item label="生育期">
              <el-input v-model="form.growth_stage" placeholder="例如：开花期" />
            </el-form-item>
          </el-col>

          <el-col :span="8">
            <el-form-item label="预测范围">
              <el-select v-model="form.days" style="width: 100%">
                <el-option label="未来1天" :value="1" />
                <el-option label="未来2天" :value="2" />
                <el-option label="未来3天" :value="3" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="土壤湿度">
              <el-input-number v-model="form.soil_moisture" :min="0" :max="100" style="width: 100%" />
            </el-form-item>
          </el-col>

          <el-col :span="8">
            <el-form-item label="土壤温度">
              <el-input-number v-model="form.soil_temperature" style="width: 100%" />
            </el-form-item>
          </el-col>

          <el-col :span="8">
            <el-form-item label="空气湿度">
              <el-input-number v-model="form.air_humidity" :min="0" :max="100" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="光照强度">
              <el-input-number v-model="form.light_intensity" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>

          <el-col :span="8">
            <el-form-item label="电导率EC">
              <el-input-number v-model="form.ec" :min="0" :step="0.1" style="width: 100%" />
            </el-form-item>
          </el-col>

          <el-col :span="8">
            <el-form-item label="采用天气数据">
              <el-switch v-model="form.use_weather" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20" v-if="form.use_weather">
          <el-col :span="8">
            <el-form-item label="最高温">
              <el-input-number v-model="form.max_temp" style="width: 100%" />
            </el-form-item>
          </el-col>

          <el-col :span="8">
            <el-form-item label="最低温">
              <el-input-number v-model="form.min_temp" style="width: 100%" />
            </el-form-item>
          </el-col>

          <el-col :span="8">
            <el-form-item label="降雨概率">
              <el-input-number v-model="form.rainfall_prob" :min="0" :max="100" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item>
          <el-button type="primary" :loading="loading" @click="shengcheng_yuce">
            生成预测
          </el-button>
          <el-button @click="chongzhi">
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card v-if="yuceResult" class="result-card">
      <template #header>
        <div class="card-title">预测结果</div>
      </template>

      <el-row :gutter="20">
        <el-col :span="8">
          <div class="small-box">
            <div class="small-title">旱情分析</div>
            <div class="small-value">{{ yuceResult.drought_analysis }}</div>
          </div>
        </el-col>

        <el-col :span="8">
          <div class="small-box">
            <div class="small-title">预测依据</div>
            <div class="small-value">{{ yuceResult.basis }}</div>
          </div>
        </el-col>

        <el-col :span="8">
          <div class="small-box">
            <div class="small-title">记录ID</div>
            <div class="small-value">{{ yuceResult.record_id || '未入库' }}</div>
          </div>
        </el-col>
      </el-row>

      <div ref="chartRef" class="chart-box"></div>

      <el-table :data="tableData" border style="width: 100%; margin-top: 20px">
        <el-table-column prop="date" label="日期" />
        <el-table-column prop="water" label="预测需水量" />
        <el-table-column prop="fertilizer" label="预测需肥量" />
        <el-table-column prop="soil" label="预测土壤湿度" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref, computed, nextTick, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { shengchengYuce } from '../api/yucejuece'

const loading = ref(false)
const chartRef = ref(null)
let chartObj = null

const form = reactive({
  crop_id: 1,
  growth_stage: '开花期',
  days: 3,
  use_weather: true,

  soil_moisture: 26,
  soil_temperature: 22,
  air_humidity: 65,
  light_intensity: 12000,
  ec: 1.2,

  max_temp: 33,
  min_temp: 25,
  rainfall_prob: 20,
  rainfall: 0
})

const yuceResult = ref(null)

const tableData = computed(() => {
  if (!yuceResult.value) {
    return []
  }

  const list = []

  for (let i = 0; i < yuceResult.value.dates.length; i++) {
    list.push({
      date: yuceResult.value.dates[i],
      water: yuceResult.value.predicted_water_need[i],
      fertilizer: yuceResult.value.predicted_fertilizer_need[i],
      soil: yuceResult.value.predicted_soil_moisture[i]
    })
  }

  return list
})

async function shengcheng_yuce() {
  loading.value = true

  try {
    const res = await shengchengYuce(form)

    if (res.code === 200) {
      yuceResult.value = res.data
      ElMessage.success('预测生成成功')

      await nextTick()
      huizhi_tubiao()
    } else {
      ElMessage.error(res.message || '预测失败')
    }
  } catch (error) {
    ElMessage.error('后端接口连接失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

function huizhi_tubiao() {
  if (!chartRef.value || !yuceResult.value) {
    return
  }

  if (chartObj) {
    chartObj.dispose()
  }

  chartObj = echarts.init(chartRef.value)

  chartObj.setOption({
    // 方案A图表色：#2D9B6C #94A3B8 #D97706 #60A5FA
    color: ['#2D9B6C', '#94A3B8', '#D97706', '#60A5FA'],
    title: {
      text: '未来水肥需求趋势'
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['需水量', '需肥量', '土壤湿度']
    },
    xAxis: {
      type: 'category',
      data: yuceResult.value.dates
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '需水量',
        type: 'line',
        smooth: true,
        data: yuceResult.value.predicted_water_need
      },
      {
        name: '需肥量',
        type: 'line',
        smooth: true,
        data: yuceResult.value.predicted_fertilizer_need
      },
      {
        name: '土壤湿度',
        type: 'line',
        smooth: true,
        data: yuceResult.value.predicted_soil_moisture
      }
    ]
  })
}

function chongzhi() {
  form.crop_id = 1
  form.growth_stage = '开花期'
  form.days = 3
  form.use_weather = true
  form.soil_moisture = 26
  form.soil_temperature = 22
  form.air_humidity = 65
  form.light_intensity = 12000
  form.ec = 1.2
  form.max_temp = 33
  form.min_temp = 25
  form.rainfall_prob = 20
  form.rainfall = 0

  yuceResult.value = null

  if (chartObj) {
    chartObj.dispose()
    chartObj = null
  }
}

onBeforeUnmount(() => {
  if (chartObj) {
    chartObj.dispose()
    chartObj = null
  }
})
</script>

<style scoped>
.page-box {
  padding: 20px;
  background-color: #FAFAF8;
}

.card-title {
  font-size: 18px;
  font-weight: bold;
  color: #1C1917;
}

.result-card {
  margin-top: 20px;
}

.small-box {
  border: 1px solid #E7E5E4;
  border-radius: 8px;
  padding: 15px;
  min-height: 80px;
  background-color: #FFFFFF;
  box-shadow: 0 2px 8px rgba(28, 25, 23, 0.06);
}

.small-title {
  color: #78716C;
  margin-bottom: 10px;
}

.small-value {
  font-size: 16px;
  color: #1C1917;
}

.chart-box {
  width: 100%;
  height: 380px;
  margin-top: 25px;
}

:deep(.el-card) {
  border-radius: 8px;
  border-color: #E7E5E4;
  box-shadow: 0 2px 8px rgba(28, 25, 23, 0.06);
}

:deep(.el-button--primary) {
  background-color: #0F766F;
  border-color: #0F766F;
}

:deep(.el-button--primary:hover) {
  background-color: #0d6a63;
  border-color: #0d6a63;
}
</style>