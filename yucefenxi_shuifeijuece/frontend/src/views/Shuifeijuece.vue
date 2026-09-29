<template>
  <div class="page-box">
    <el-row :gutter="20">
      <el-col :span="10">
        <el-card>
          <template #header>
            <div class="card-title">水肥决策输入</div>
          </template>

          <el-form :model="form" label-width="130px">
            <el-form-item label="作物ID">
              <el-input-number v-model="form.crop_id" :min="1" style="width: 100%" />
            </el-form-item>

            <el-form-item label="生育期">
              <el-input v-model="form.growth_stage" />
            </el-form-item>

            <el-form-item label="土壤湿度">
              <el-input-number v-model="form.soil_moisture" :min="0" :max="100" style="width: 100%" />
            </el-form-item>

            <el-form-item label="电导率EC">
              <el-input-number v-model="form.ec" :min="0" :step="0.1" style="width: 100%" />
            </el-form-item>

            <el-form-item label="采用天气数据">
              <el-switch v-model="form.use_weather" />
            </el-form-item>

            <el-form-item label="最高温">
              <el-input-number v-model="form.max_temp" style="width: 100%" />
            </el-form-item>

            <el-form-item label="降雨概率">
              <el-input-number v-model="form.rainfall_prob" :min="0" :max="100" style="width: 100%" />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" :loading="loading" @click="shengcheng_juece">
                生成决策
              </el-button>
              <el-button type="success" :disabled="!jueceResult" @click="queren_xiada">
                手动确认下发
              </el-button>
            </el-form-item>
          </el-form>

          <el-alert
            title="备注：当前页面可以先手动输入数据。团队联调后，可从预测分析模块、监测数据模块和天气分析模块自动带入数据。"
            type="info"
            :closable="false"
            style="margin-top: 15px"
          />
        </el-card>
      </el-col>

      <el-col :span="14">
        <el-card v-if="jueceResult">
          <template #header>
            <div class="card-title">当前决策结果</div>
          </template>

          <el-row :gutter="20">
            <el-col :span="12">
              <div class="small-box">
                <div class="small-title">水分状态评估</div>
                <div class="small-value">{{ jueceResult.water_status }}</div>
              </div>
            </el-col>

            <el-col :span="12">
              <div class="small-box">
                <div class="small-title">肥力状态评估</div>
                <div class="small-value">{{ jueceResult.fertility_status }}</div>
              </div>
            </el-col>
          </el-row>

          <el-row :gutter="20" style="margin-top: 20px">
            <el-col :span="12">
              <div class="small-box">
                <div class="small-title">推荐灌溉量</div>
                <div class="small-value">{{ jueceResult.recommended_irrigation }}</div>
              </div>
            </el-col>

            <el-col :span="12">
              <div class="small-box">
                <div class="small-title">推荐施肥量</div>
                <div class="small-value">{{ jueceResult.recommended_fertilization }}</div>
              </div>
            </el-col>
          </el-row>

          <div class="reason-box">
            <div class="small-title">决策依据说明</div>
            <div>{{ jueceResult.decision_reason }}</div>
          </div>

          <el-table :data="deviceTable" border style="width: 100%; margin-top: 20px">
            <el-table-column prop="name" label="设备参数" />
            <el-table-column prop="value" label="参数值" />
          </el-table>

          <div ref="chartRef" class="chart-box"></div>
        </el-card>

        <el-card v-else>
          <div class="empty-box">请先生成水肥决策</div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { reactive, ref, computed, nextTick, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { shengchengJuece, xiadaZhiling } from '../api/yucejuece'

const loading = ref(false)
const chartRef = ref(null)
let chartObj = null

const form = reactive({
  crop_id: 1,
  growth_stage: '开花期',
  use_weather: true,

  soil_moisture: 26,
  ec: 1.2,

  max_temp: 33,
  rainfall_prob: 20,

  // 备注：
  // 这里后续可以由预测分析模块自动传入
  predicted_water_need: [26.5, 25.3, 24.1],
  predicted_fertilizer_need: [5.2, 5.0, 4.8]
})

const jueceResult = ref(null)

const deviceTable = computed(() => {
  if (!jueceResult.value) {
    return []
  }

  const params = jueceResult.value.device_params

  return [
    {
      name: '灌溉量',
      value: params.irrigation_amount
    },
    {
      name: '施肥量',
      value: params.fertilization_amount
    },
    {
      name: '泵运行时长',
      value: params.pump_run_time
    }
  ]
})

async function shengcheng_juece() {
  loading.value = true

  try {
    const res = await shengchengJuece(form)

    if (res.code === 200) {
      jueceResult.value = res.data
      ElMessage.success('决策生成成功')

      await nextTick()
      huizhi_tubiao()
    } else {
      ElMessage.error(res.message || '生成决策失败')
    }
  } catch (error) {
    ElMessage.error('后端接口连接失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

async function queren_xiada() {
  if (!jueceResult.value) {
    ElMessage.warning('请先生成决策')
    return
  }

  const params = jueceResult.value.device_params

  try {
    const res = await xiadaZhiling({
      device_id: 1,
      irrigation_amount: params.irrigation_amount,
      fertilization_amount: params.fertilization_amount,
      pump_run_time: params.pump_run_time
    })

    if (res.code === 200) {
      ElMessage.success('设备指令已生成，等待硬件执行')
    } else {
      ElMessage.error(res.message || '下发失败')
    }
  } catch (error) {
    ElMessage.error('设备指令接口连接失败')
    console.error(error)
  }
}

function huizhi_tubiao() {
  if (!chartRef.value || !jueceResult.value) {
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
      text: '水肥决策参数对比'
    },
    tooltip: {},
    xAxis: {
      type: 'category',
      data: ['灌溉量', '施肥量', '泵运行时长']
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '设备参数',
        type: 'bar',
        data: [
          jueceResult.value.device_params.irrigation_amount,
          jueceResult.value.device_params.fertilization_amount,
          jueceResult.value.device_params.pump_run_time
        ]
      }
    ]
  })
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
  font-size: 20px;
  font-weight: bold;
  color: #1C1917;
}

.reason-box {
  margin-top: 20px;
  border: 1px solid #E7E5E4;
  border-radius: 8px;
  padding: 15px;
  line-height: 1.8;
  background-color: #FFFFFF;
  box-shadow: 0 2px 8px rgba(28, 25, 23, 0.06);
}

.chart-box {
  width: 100%;
  height: 360px;
  margin-top: 25px;
}

.empty-box {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #78716C;
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

:deep(.el-button--success) {
  background-color: #2D9B6C;
  border-color: #2D9B6C;
}

:deep(.el-button--success:hover) {
  background-color: #288a5f;
  border-color: #288a5f;
}
</style>