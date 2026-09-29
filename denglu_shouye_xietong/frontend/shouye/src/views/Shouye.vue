<template>
  <div class="home-page">
    <!-- 页面顶部 -->
    <header class="home-header">
      <div class="home-header__left">
        <span class="home-header__eyebrow">
          SMART AGRICULTURE MONITORING
        </span>

        <h1>农情监测总览</h1>

        <p>
          实时掌握作物、土壤、气象及智能决策运行情况
        </p>
      </div>

      <div class="home-header__right">
        <div class="header-time">
          <span>{{ currentWeek }}</span>
          <strong>{{ currentDate }}</strong>
        </div>

        <RouterLink
          to="/warnings"
          class="warning-button"
        >
          <span class="warning-button__icon">!</span>
          <span class="warning-button__text">预警消息</span>
          <span class="warning-button__badge">3</span>
        </RouterLink>

        <div class="user-info">
          <div class="user-info__avatar">
            管
          </div>

          <div class="user-info__content">
            <strong>农场管理员</strong>
            <span>智慧农业示范基地</span>
          </div>
        </div>
      </div>
    </header>

    <!-- 顶部统计数据 -->
    <section class="top-statistics">
      <RouterLink
        v-for="item in statistics"
        :key="item.title"
        :to="item.path"
        class="statistic-card"
      >
        <div
          class="statistic-card__icon"
          :class="`statistic-card__icon--${item.theme}`"
        >
          {{ item.icon }}
        </div>

        <div class="statistic-card__content">
          <div class="statistic-card__head">
            <span>{{ item.title }}</span>

            <span
              class="statistic-card__tag"
              :class="`statistic-card__tag--${item.theme}`"
            >
              今日
            </span>
          </div>

          <div class="statistic-card__value">
            {{ item.value }}
            <small>{{ item.unit }}</small>
          </div>

          <div class="statistic-card__footer">
            <span>{{ item.description }}</span>

            <strong
              :class="{
                decrease: item.change < 0
              }"
            >
              {{ item.change > 0 ? '+' : '' }}{{ item.change }}%
            </strong>
          </div>
        </div>
      </RouterLink>
    </section>

    <!-- 当前农情信息 -->
    <section class="home-section">
      <div class="section-title">
        <div>
          <span>CURRENT FARM STATUS</span>
          <h2>当前农情与智能建议</h2>
        </div>

        <div class="data-status">
          <span class="data-status__dot"></span>
          实时数据正常
        </div>
      </div>

      <div class="status-grid">
        <RouterLink
          v-for="item in statusCards"
          :key="item.title"
           :to="item.path"
          class="status-card"
          :class="{
            'status-card--featured': item.featured
          }"
        >
          <div class="status-card__head">
            <div>
              <span>{{ item.englishTitle }}</span>
              <h3>{{ item.title }}</h3>
            </div>

            <div class="status-card__icon">
              {{ item.icon }}
            </div>
          </div>

          <div class="status-card__value">
            {{ item.value }}

            <small v-if="item.unit">
              {{ item.unit }}
            </small>
          </div>

          <p>{{ item.description }}</p>

          <div
            v-if="item.progress !== undefined"
            class="progress-area"
          >
            <div class="progress-area__head">
              <span>{{ item.progressTitle }}</span>
              <strong>{{ item.progress }}%</strong>
            </div>

            <div class="progress-area__track">
              <span
                :style="{ width: `${item.progress}%` }"
              ></span>
            </div>
          </div>

          <div
            v-if="item.tags && item.tags.length"
            class="status-card__tags"
          >
            <span
              v-for="tag in item.tags"
              :key="tag"
            >
              {{ tag }}
            </span>
          </div>
        </RouterLink>
      </div>
    </section>

    <!-- 图表区域 -->
    <section class="home-section">
      <div class="section-title">
        <div>
          <span>DATA TREND ANALYSIS</span>
          <h2>监测数据与决策趋势</h2>
        </div>

        <div class="time-switch">
          <button
            type="button"
            :class="{ active: selectedTime === '7days' }"
            @click="selectedTime = '7days'"
          >
            近7天
          </button>

          <button
            type="button"
            :class="{ active: selectedTime === '30days' }"
            @click="selectedTime = '30days'"
          >
            近30天
          </button>
        </div>
      </div>

      <div class="charts-grid">
        <JichuTubiao
          title="近7天土壤湿度趋势图"
          subtitle="SOIL MOISTURE TREND"
          tag="单位：%"
          :option="soilMoistureOption"
        />

        <JichuTubiao
          title="近7天灌溉量趋势图"
          subtitle="IRRIGATION TREND"
          tag="单位：mm"
          :option="irrigationOption"
        />

        <JichuTubiao
          title="近7天施肥量趋势图"
          subtitle="FERTILIZATION TREND"
          tag="单位：kg/亩"
          :option="fertilizationOption"
        />

        <JichuTubiao
          title="未来3天天气趋势图"
          subtitle="WEATHER FORECAST"
          tag="未来72小时"
          :option="weatherOption"
        />

        <JichuTubiao
          title="历史决策次数统计图"
          subtitle="DECISION STATISTICS"
          tag="本月数据"
          :option="decisionOption"
        />

        <JichuTubiao
          title="预警分布图"
          subtitle="WARNING DISTRIBUTION"
          tag="当前周期"
          :option="warningOption"
        />
      </div>
    </section>

    <footer class="home-footer">
      <span>智慧农情监测与决策管理系统</span>
      <span>最后更新时间：{{ currentTime }}</span>
    </footer>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import JichuTubiao from '../components/JichuTubiao.vue'

const selectedTime = ref('7days')

/**
 * 当前日期
 */
const currentDate = computed(() => {
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  }).format(new Date())
})

/**
 * 当前星期
 */
const currentWeek = computed(() => {
  const weekList = [
    '星期日',
    '星期一',
    '星期二',
    '星期三',
    '星期四',
    '星期五',
    '星期六'
  ]

  return weekList[new Date().getDay()]
})

/**
 * 当前时间
 */
const currentTime = computed(() => {
  return new Intl.DateTimeFormat('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  }).format(new Date())
})

/**
 * 顶部统计数据
 */
const statistics = [
  {
    title:'土壤湿度',
    value:'65',
    unit:'%',
    icon:'💧',
    theme:'blue',
    description:'土壤墒情良好',
    change:3,
    path:'/monitoring'
  },

  {
    title:'作物数量',
    value:'12',
    unit:'种',
    icon:'🌱',
    theme:'green',
    description:'当前种植情况',
    change:5,
    path:'/crops'
  },

  {
    title:'灌溉建议',
    value:'正常',
    unit:'',
    icon:'🚿',
    theme:'cyan',
    description:'智能分析完成',
    change:2,
    path:'/irrigation'
  },

  {
    title:'天气状态',
    value:'晴',
    unit:'',
    icon:'☀',
    theme:'orange',
    description:'未来天气稳定',
    change:1,
    path:'/weather'
  }
]

/**
 * 中部农情数据
 */
const statusCards = [
  {
    englishTitle: 'CURRENT CROP',
    title: '当前作物',
    value: '冬小麦',
    description: '一号示范田，当前种植面积为120亩',
    icon: '♧',
    tags: ['长势良好', '一号地块'],
    featured: true,

      path:'/crops'
  },
  {
    englishTitle: 'GROWTH STAGE',
    title: '当前生育期',
    value: '拔节期',
    description: '预计12天后进入孕穗期',
    icon: '↗',
    progress: 68,
    progressTitle: '当前生育期进度',

      path:'/monitoring'
  },
  {
    englishTitle: 'SOIL MOISTURE',
    title: '当前土壤湿度',
    value: 62.8,
    unit: '%',
    description: '适宜范围为60%至75%',
    icon: '◌',
    progress: 63,
    progressTitle: '相对土壤含水量',

    path:'/monitoring'
  },
  {
    englishTitle: 'WEATHER SUMMARY',
    title: '未来天气摘要',
    value: '多云转小雨',
    description: '未来24小时降水概率65%，平均温度19℃',
    icon: '☁',
    tags: ['东南风3级', '预计降水6.8mm'],

    path:'/weather'
  },
  {
    englishTitle: 'IRRIGATION ADVICE',
    title: '当前建议灌溉量',
    value: 18.5,
    unit: 'mm',
    description: '建议明日06:00至09:00执行灌溉',
    icon: '≈',
    tags: ['预计用水2220m³', '建议及时执行'],

    path:'/irrigation'
  },
  {
    englishTitle: 'FERTILIZATION ADVICE',
    title: '当前建议施肥量',
    value: 8.6,
    unit: 'kg/亩',
    description: '推荐使用高氮复合肥，并结合灌溉施用',
    icon: '◇',
    tags: ['氮肥为主', '预计总量1032kg'],

    path:'/warnings'
  }
]

/**
 * ECharts通用提示框样式
 */
const commonTooltip = {
  trigger: 'axis',
  backgroundColor: 'rgba(22, 55, 42, 0.95)',
  borderWidth: 0,
  padding: 12,
  textStyle: {
    color: '#ffffff',
    fontSize: 11
  }
}

/**
 * ECharts通用网格
 */
const commonGrid = {
  top: 32,
  right: 20,
  bottom: 30,
  left: 43
}

/**
 * ECharts通用横轴
 */
const commonXAxis = {
  type: 'category',
  axisTick: {
    show: false
  },
  axisLine: {
    lineStyle: {
      color: 'rgba(64, 101, 80, 0.15)'
    }
  },
  axisLabel: {
    color: '#88958d',
    fontSize: 10
  }
}

/**
 * ECharts通用纵轴
 */
const commonYAxis = {
  type: 'value',
  axisTick: {
    show: false
  },
  axisLine: {
    show: false
  },
  axisLabel: {
    color: '#96a198',
    fontSize: 9
  },
  splitLine: {
    lineStyle: {
      color: 'rgba(64, 101, 80, 0.07)'
    }
  }
}

/**
 * 近7天土壤湿度趋势
 */
const soilMoistureOption = {
  tooltip: {
    ...commonTooltip,
    valueFormatter(value) {
      return `${value}%`
    }
  },

  grid: commonGrid,

  xAxis: {
    ...commonXAxis,
    boundaryGap: false,
    data: [
      '周四',
      '周五',
      '周六',
      '周日',
      '周一',
      '周二',
      '今日'
    ]
  },

  yAxis: {
    ...commonYAxis,
    min: 40,
    max: 80,
    axisLabel: {
      ...commonYAxis.axisLabel,
      formatter: '{value}%'
    }
  },

  series: [
    {
      name: '土壤湿度',
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 7,

      data: [
        56,
        59,
        61,
        58,
        64,
        66,
        62.8
      ],

      lineStyle: {
        width: 2,
        color: '#4f9870'
      },

      itemStyle: {
        color: '#ffffff',
        borderColor: '#4f9870',
        borderWidth: 2
      },

      areaStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            {
              offset: 0,
              color: 'rgba(79, 152, 112, 0.32)'
            },
            {
              offset: 1,
              color: 'rgba(79, 152, 112, 0.01)'
            }
          ]
        }
      },

      markLine: {
        silent: true,
        symbol: 'none',

        lineStyle: {
          type: 'dashed',
          color: 'rgba(185, 132, 80, 0.55)'
        },

        label: {
          color: '#a37854',
          fontSize: 9,
          formatter: '适宜下限'
        },

        data: [
          {
            yAxis: 60
          }
        ]
      }
    }
  ]
}

/**
 * 近7天灌溉量趋势
 */
const irrigationOption = {
  tooltip: {
    ...commonTooltip,
    valueFormatter(value) {
      return `${value} mm`
    }
  },

  grid: commonGrid,

  xAxis: {
    ...commonXAxis,
    boundaryGap: true,

    data: [
      '周四',
      '周五',
      '周六',
      '周日',
      '周一',
      '周二',
      '今日'
    ]
  },

  yAxis: {
    ...commonYAxis,
    min: 0,
    max: 25
  },

  series: [
    {
      name: '灌溉量',
      type: 'bar',
      barWidth: 18,

      data: [
        12,
        0,
        8,
        15,
        0,
        10,
        18.5
      ],

      itemStyle: {
        borderRadius: [
          5,
          5,
          1,
          1
        ],

        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,

          colorStops: [
            {
              offset: 0,
              color: '#5d9e7a'
            },
            {
              offset: 1,
              color: '#b8d8c4'
            }
          ]
        }
      }
    }
  ]
}

/**
 * 近7天施肥量趋势
 */
const fertilizationOption = {
  tooltip: {
    ...commonTooltip,
    valueFormatter(value) {
      return `${value} kg/亩`
    }
  },

  grid: commonGrid,

  xAxis: {
    ...commonXAxis,
    boundaryGap: false,

    data: [
      '周四',
      '周五',
      '周六',
      '周日',
      '周一',
      '周二',
      '今日'
    ]
  },

  yAxis: {
    ...commonYAxis,
    min: 0,
    max: 12
  },

  series: [
    {
      name: '施肥量',
      type: 'line',
      smooth: true,
      symbol: 'emptyCircle',
      symbolSize: 7,

      data: [
        5.2,
        6.1,
        4.8,
        7.4,
        6.6,
        8.1,
        8.6
      ],

      lineStyle: {
        width: 2,
        color: '#b58958'
      },

      itemStyle: {
        color: '#ffffff',
        borderColor: '#b58958',
        borderWidth: 2
      }
    }
  ]
}

/**
 * 未来3天天气趋势
 */
const weatherOption = {
  tooltip: {
    ...commonTooltip
  },

  legend: {
    top: 0,
    right: 6,
    itemWidth: 12,
    itemHeight: 7,

    textStyle: {
      color: '#7f8d84',
      fontSize: 9
    }
  },

  grid: {
    top: 43,
    right: 42,
    bottom: 30,
    left: 42
  },

  xAxis: {
    ...commonXAxis,

    data: [
      '明天',
      '后天',
      '第三天'
    ]
  },

  yAxis: [
    {
      ...commonYAxis,
      name: '℃',

      nameTextStyle: {
        color: '#96a198',
        fontSize: 9
      }
    },
    {
      ...commonYAxis,
      name: 'mm',

      splitLine: {
        show: false
      },

      nameTextStyle: {
        color: '#96a198',
        fontSize: 9
      }
    }
  ],

  series: [
    {
      name: '最高温度',
      type: 'line',
      smooth: true,

      data: [
        23,
        21,
        25
      ],

      lineStyle: {
        color: '#c48b5a',
        width: 2
      },

      itemStyle: {
        color: '#c48b5a'
      }
    },
    {
      name: '最低温度',
      type: 'line',
      smooth: true,

      data: [
        15,
        14,
        16
      ],

      lineStyle: {
        color: '#6794aa',
        width: 2
      },

      itemStyle: {
        color: '#6794aa'
      }
    },
    {
      name: '降水量',
      type: 'bar',
      yAxisIndex: 1,
      barWidth: 14,

      data: [
        6.8,
        2.5,
        0
      ],

      itemStyle: {
        color: 'rgba(89, 139, 169, 0.48)',

        borderRadius: [
          4,
          4,
          0,
          0
        ]
      }
    }
  ]
}

/**
 * 历史决策次数
 */
const decisionOption = {
  tooltip: {
    ...commonTooltip,
    axisPointer: {
      type: 'shadow'
    }
  },

  grid: {
    top: 20,
    right: 28,
    bottom: 25,
    left: 85
  },

  xAxis: {
    ...commonYAxis,
    type: 'value'
  },

  yAxis: {
    type: 'category',
    inverse: true,

    data: [
      '灌溉决策',
      '施肥决策',
      '预警处理',
      '病虫害防治',
      '农事建议'
    ],

    axisLine: {
      show: false
    },

    axisTick: {
      show: false
    },

    axisLabel: {
      color: '#7e8d84',
      fontSize: 10
    }
  },

  series: [
    {
      name: '决策次数',
      type: 'bar',
      barWidth: 13,

      data: [
        42,
        31,
        26,
        18,
        35
      ],

      label: {
        show: true,
        position: 'right',
        color: '#6d7a72',
        fontSize: 10
      },

      itemStyle: {
        borderRadius: [
          0,
          6,
          6,
          0
        ],

        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 1,
          y2: 0,

          colorStops: [
            {
              offset: 0,
              color: '#5a9b74'
            },
            {
              offset: 1,
              color: '#9bcaaa'
            }
          ]
        }
      }
    }
  ]
}

/**
 * 预警分布
 */
const warningOption = {
  tooltip: {
    trigger: 'item',
    backgroundColor: 'rgba(22, 55, 42, 0.95)',
    borderWidth: 0,

    textStyle: {
      color: '#ffffff',
      fontSize: 11
    },

    formatter: '{b}<br />{c} 条，占比 {d}%'
  },

  legend: {
    orient: 'vertical',
    right: 8,
    top: 'center',
    itemWidth: 9,
    itemHeight: 9,

    textStyle: {
      color: '#748179',
      fontSize: 10
    }
  },

  series: [
    {
      name: '预警分布',
      type: 'pie',
      radius: [
        '42%',
        '66%'
      ],

      center: [
        '37%',
        '54%'
      ],

      label: {
        show: false
      },

      itemStyle: {
        borderColor: '#ffffff',
        borderWidth: 3,
        borderRadius: 5
      },

      data: [
        {
          value: 12,
          name: '土壤墒情',
          itemStyle: {
            color: '#5f9a76'
          }
        },
        {
          value: 8,
          name: '病虫害',
          itemStyle: {
            color: '#c58563'
          }
        },
        {
          value: 6,
          name: '极端天气',
          itemStyle: {
            color: '#668da5'
          }
        },
        {
          value: 4,
          name: '设备异常',
          itemStyle: {
            color: '#b4a06c'
          }
        }
      ]
    }
  ],

  graphic: [
    {
      type: 'text',
      left: '31%',
      top: '44%',

      style: {
        text: '30',
        fill: '#33483b',
        fontSize: 25,
        fontWeight: 700,
        fontFamily: 'Georgia'
      }
    },
    {
      type: 'text',
      left: '29%',
      top: '58%',

      style: {
        text: '累计预警',
        fill: '#95a098',
        fontSize: 9
      }
    }
  ]
}
</script>

<style scoped>
.home-page {
  min-height: 100vh;
  padding: 0 32px 24px;
}

/* =========================
   页面顶部
========================= */

.home-header {
  min-height: 116px;
  padding: 25px 0 22px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}

.home-header__eyebrow {
  color: #90a096;
  font-size: 9px;
  letter-spacing: 2px;
}

.home-header h1 {
  margin: 7px 0 5px;
  color: #273a2f;
  font-family: Georgia, "Times New Roman", serif;
  font-size: 27px;
  font-weight: 700;
  letter-spacing: 1px;
}

.home-header p {
  margin: 0;
  color: #98a39c;
  font-size: 11px;
}

.home-header__right {
  display: flex;
  align-items: center;
  gap: 17px;
}

.header-time {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.header-time span {
  color: #93a097;
  font-size: 10px;
}

.header-time strong {
  margin-top: 4px;
  color: #536159;
  font-size: 12px;
  font-weight: 500;
}

.warning-button {
  position: relative;
  min-height: 39px;
  padding: 0 12px;
  display: flex;
  align-items: center;
  gap: 7px;
  border: 1px solid rgba(65, 105, 83, 0.11);
  border-radius: 11px;
  color: #64736a;
  background: rgba(255, 255, 255, 0.76);
  text-decoration: none;
}

.warning-button__icon {
  width: 19px;
  height: 19px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  color: white;
  background: #c8796d;
  font-size: 11px;
}

.warning-button__text {
  font-size: 10px;
}

.warning-button__badge {
  position: absolute;
  top: -6px;
  right: -5px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  display: grid;
  place-items: center;
  border: 2px solid #f2f6f2;
  border-radius: 10px;
  color: white;
  background: #c96f64;
  font-size: 8px;
}

.user-info {
  padding-left: 17px;
  display: flex;
  align-items: center;
  gap: 10px;
  border-left: 1px solid rgba(64, 97, 79, 0.1);
}

.user-info__avatar {
  width: 39px;
  height: 39px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  color: white;
  background: linear-gradient(
    145deg,
    #6fa784,
    #3f7958
  );
  font-size: 13px;
}

.user-info__content {
  display: flex;
  flex-direction: column;
}

.user-info__content strong {
  color: #4d5e54;
  font-size: 11px;
  font-weight: 600;
}

.user-info__content span {
  margin-top: 4px;
  color: #9ba49e;
  font-size: 9px;
}

/* =========================
   顶部统计卡片
========================= */

.top-statistics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.statistic-card {
  min-height: 130px;
  padding: 22px;
  display: flex;
  gap: 17px;
  border: 1px solid rgba(70, 115, 91, 0.11);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.84);
  box-shadow: 0 12px 36px rgba(34, 72, 51, 0.05);
  transition:
    transform 0.25s ease,
    box-shadow 0.25s ease;
}

.statistic-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 16px 42px rgba(34, 72, 51, 0.09);
}

.statistic-card__icon {
  width: 49px;
  height: 49px;
  flex: 0 0 auto;
  display: grid;
  place-items: center;
  border-radius: 14px;
  font-size: 22px;
}

.statistic-card__icon--green {
  color: #3e8c63;
  background: rgba(91, 166, 122, 0.13);
}

.statistic-card__icon--orange {
  color: #b7783f;
  background: rgba(210, 151, 86, 0.14);
}

.statistic-card__icon--blue {
  color: #4f7fa6;
  background: rgba(86, 139, 181, 0.13);
}

.statistic-card__content {
  min-width: 0;
  flex: 1;
}

.statistic-card__head,
.statistic-card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.statistic-card__head > span:first-child {
  color: #728077;
  font-size: 13px;
}

.statistic-card__tag {
  padding: 3px 8px;
  border-radius: 8px;
  font-size: 10px;
}

.statistic-card__tag--green {
  color: #3e8c63;
  background: rgba(91, 166, 122, 0.1);
}

.statistic-card__tag--orange {
  color: #ad6f38;
  background: rgba(210, 151, 86, 0.12);
}

.statistic-card__tag--blue {
  color: #497798;
  background: rgba(86, 139, 181, 0.12);
}

.statistic-card__value {
  margin: 11px 0 10px;
  color: #25362c;
  font-family: Georgia, serif;
  font-size: 31px;
  font-weight: 700;
}

.statistic-card__value small {
  margin-left: 5px;
  color: #7a877f;
  font-size: 12px;
  font-weight: 400;
}

.statistic-card__footer {
  color: #96a098;
  font-size: 10px;
}

.statistic-card__footer strong {
  color: #4b9b6c;
  font-size: 11px;
}

.statistic-card__footer strong.decrease {
  color: #c77168;
}

/* =========================
   区域标题
========================= */

.home-section {
  margin-top: 30px;
}

.section-title {
  margin-bottom: 16px;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 18px;
}

.section-title > div:first-child > span {
  color: #90a096;
  font-size: 9px;
  letter-spacing: 2px;
}

.section-title h2 {
  margin: 5px 0 0;
  color: #405148;
  font-family: Georgia, "Times New Roman", serif;
  font-size: 17px;
}

.data-status {
  display: flex;
  align-items: center;
  gap: 7px;
  color: #89968e;
  font-size: 10px;
}

.data-status__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #62ad7d;
  box-shadow: 0 0 8px rgba(98, 173, 125, 0.65);
}

/* =========================
   当前农情卡片
========================= */

.status-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 14px;
}

.status-card {
  min-width: 0;
  min-height: 195px;
  padding: 21px;
  display: flex;
  flex-direction: column;
  border: 1px solid rgba(64, 102, 81, 0.1);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.8);
  box-shadow: 0 12px 36px rgba(35, 76, 53, 0.045);
  transition:
    transform 0.25s ease,
    border-color 0.25s ease;
}

.status-card:hover {
  transform: translateY(-3px);
  border-color: rgba(80, 145, 108, 0.22);
}

.status-card--featured {
  color: white;
  border-color: transparent;
  background:
    linear-gradient(
      145deg,
      rgba(55, 113, 79, 0.97),
      rgba(31, 74, 55, 0.99)
    );
  box-shadow: 0 15px 36px rgba(41, 93, 64, 0.2);
}

.status-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.status-card__head span {
  color: #8d9a91;
  font-size: 8px;
  letter-spacing: 1.4px;
}

.status-card--featured .status-card__head span {
  color: rgba(255, 255, 255, 0.52);
}

.status-card__head h3 {
  margin: 5px 0 0;
  color: #536159;
  font-size: 12px;
  font-weight: 500;
}

.status-card--featured .status-card__head h3 {
  color: rgba(255, 255, 255, 0.8);
}

.status-card__icon {
  width: 34px;
  height: 34px;
  flex: 0 0 auto;
  display: grid;
  place-items: center;
  border-radius: 10px;
  color: #56866a;
  background: rgba(74, 137, 99, 0.09);
}

.status-card--featured .status-card__icon {
  color: white;
  background: rgba(255, 255, 255, 0.12);
}

.status-card__value {
  margin-top: 23px;
  overflow: hidden;
  color: #24362c;
  font-family: Georgia, serif;
  font-size: 25px;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status-card--featured .status-card__value {
  color: white;
}

.status-card__value small {
  margin-left: 4px;
  color: #77857b;
  font-size: 11px;
  font-weight: 400;
}

.status-card--featured .status-card__value small {
  color: rgba(255, 255, 255, 0.63);
}

.status-card > p {
  min-height: 32px;
  margin: 9px 0 0;
  color: #9aa49d;
  font-size: 10px;
  line-height: 1.6;
}

.status-card--featured > p {
  color: rgba(255, 255, 255, 0.58);
}

.progress-area {
  margin-top: auto;
  padding-top: 15px;
}

.progress-area__head {
  margin-bottom: 8px;
  display: flex;
  justify-content: space-between;
  color: #8c988f;
  font-size: 9px;
}

.progress-area__track {
  height: 4px;
  overflow: hidden;
  border-radius: 4px;
  background: rgba(59, 90, 72, 0.09);
}

.progress-area__track span {
  height: 100%;
  display: block;
  border-radius: inherit;
  background:
    linear-gradient(
      90deg,
      #559a6f,
      #8bcaa2
    );
}

.status-card__tags {
  margin-top: auto;
  padding-top: 15px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.status-card__tags span {
  padding: 4px 8px;
  border-radius: 8px;
  color: #66806e;
  background: rgba(72, 128, 93, 0.08);
  font-size: 9px;
}

.status-card--featured .status-card__tags span {
  color: rgba(255, 255, 255, 0.79);
  background: rgba(255, 255, 255, 0.11);
}

/* =========================
   图表区域
========================= */

.charts-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.time-switch {
  padding: 3px;
  display: flex;
  border-radius: 9px;
  background: rgba(69, 105, 85, 0.06);
}

.time-switch button {
  padding: 6px 12px;
  border: none;
  border-radius: 7px;
  color: #8c9890;
  background: transparent;
  cursor: pointer;
  font-size: 9px;
}

.time-switch button.active {
  color: #4d775e;
  background: white;
  box-shadow: 0 3px 10px rgba(54, 91, 69, 0.08);
}

/* =========================
   页脚
========================= */

.home-footer {
  margin-top: 30px;
  padding: 18px 0 2px;
  display: flex;
  justify-content: space-between;
  border-top: 1px solid rgba(64, 100, 80, 0.08);
  color: #a5ada8;
  font-size: 9px;
}

/* =========================
   响应式
========================= */

@media (max-width: 1500px) {
  .status-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .charts-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 1100px) {
  .top-statistics {
    grid-template-columns: 1fr;
  }

  .header-time {
    display: none;
  }
}

@media (max-width: 850px) {
  .home-page {
    padding: 0 18px 22px;
  }

  .home-header {
    align-items: flex-start;
  }

  .user-info__content {
    display: none;
  }

  .status-grid,
  .charts-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 600px) {
  .home-header {
    min-height: auto;
    padding: 22px 0;
    flex-direction: column;
  }

  .home-header__right {
    width: 100%;
    justify-content: flex-end;
  }

  .home-header h1 {
    font-size: 23px;
  }

  .warning-button__text {
    display: none;
  }

  .user-info {
    padding-left: 8px;
  }

  .section-title {
    align-items: flex-start;
    flex-direction: column;
  }

  .home-footer {
    flex-direction: column;
    gap: 7px;
  }
}
</style>