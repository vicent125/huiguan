<template>
<div class="page">
<header class="header">
<div>
<span>
DEVICE COLLABORATION
</span>
<h1>
设备协同
</h1>
<p>
智能农业设备状态监测与远程控制
</p>
</div>
</header>
<section class="container">
<!-- 设备状态 -->
<div class="card">
<div class="card-title">
<span>
DEVICE STATUS
</span>
<h2>
设备状态
</h2>
</div>
<div class="status-list">
<div class="status-item">
<div class="icon">
💧
</div>
<div class="content">
<h3>
水箱液位
</h3>
<strong>
{{ waterLevel }}%
</strong>
<div class="progress">
<div :style="{width: waterLevel + '%'}"></div>
</div>
</div>
</div>
<div class="status-item">
<div class="icon">
🧪
</div>
<div class="content">
<h3>
肥箱液位
</h3>
<strong>
{{ fertilizerLevel }}%
</strong>
<div class="progress">
<div :style="{width: fertilizerLevel + '%'}"></div>
</div>
</div>
</div>
</div>
</div>
<!-- 指令生成 -->
<div class="card">
<div class="card-title">
<span>
COMMAND CONTROL
</span>
<h2>
指令下发
</h2>
</div>
<button class="generate" @click="generateCommand">
生成设备参数
</button>
<div v-if="command" class="command-box">
<div>灌溉参数：<strong>{{command.irrigation}}</strong></div>
<div>施肥参数：<strong>{{command.fertilizer}}</strong></div>
<div>泵运行：
<strong :class="command.pump ? 'running' : ''">
{{command.pump ? '运行中' : '停止'}}
</strong>
</div>
</div>
<button v-if="command" class="send" @click="sendCommand">
确认下发
</button>
<div v-if="message" class="message">
{{message}}
</div>
</div>
</section>
</div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

// 响应式数据
const waterLevel = ref(0)
const fertilizerLevel = ref(0)
const command = ref(null)
const message = ref('')

// 页面加载自动拉取后端设备数据
const loadDeviceData = async () => {
  try {
    const res = await axios.get('/api/xietong/list')
    if (res.data.code === 200 && res.data.data.length > 0) {
      // 取最新一条数据
      const latest = res.data.data[res.data.data.length - 1]
      waterLevel.value = latest.waterLevel
      fertilizerLevel.value = latest.fertilizerLevel
    } else {
      message.value = "暂无设备数据，请下发指令生成记录"
    }
  } catch (err) {
    message.value = "加载设备数据失败，请检查后端服务是否启动"
    console.error('读取列表接口错误：', err)
  }
}

// 本地随机生成水肥参数（纯前端逻辑）
const generateCommand = () => {
  console.log('点击生成参数按钮')
  command.value = {
    irrigation: (Math.random() * 10 + 15).toFixed(1) + ' mm',
    fertilizer: (Math.random() * 5 + 5).toFixed(1) + ' kg/亩',
    pump: true
  }
  message.value = ''
}

// 下发接口：保存数据到后端数据库
const sendCommand = async () => {
  console.log('点击确认下发按钮')
  if (!command.value) {
    message.value = "请先生成设备参数！"
    return
  }
  try {
    const irrNum = parseFloat(command.value.irrigation)
    const fertNum = parseFloat(command.value.fertilizer)
    const submitData = {
      deviceName: "智慧水肥一体机",
      deviceCode: "AG00" + Math.floor(Math.random() * 999),
      status: "在线",
      syncMode: "水肥协同自动调控",
      waterLevel: waterLevel.value,
      fertilizerLevel: fertilizerLevel.value,
      irrigation: irrNum,
      fertilize: fertNum,
      pumpStatus: command.value.pump ? "运行" : "停止"
    }
    const res = await axios.post('/api/xietong/add', submitData)
    if (res.data.code === 200) {
      message.value = "指令下发成功，已保存至数据库！"
      await loadDeviceData()
    }
  } catch (err) {
    message.value = "指令下发失败，接口请求异常"
    console.error('新增数据接口错误：', err)
  }
}

// 页面挂载自动加载数据
onMounted(() => {
  loadDeviceData()
})
</script>

<style scoped>
.page{
min-height:100vh;
padding:35px;
background:#f3f7f3;
}
.header span{
font-size:10px;
letter-spacing:3px;
color:#8b9b91;
}
.header h1{
margin:8px 0;
font-size:32px;
color:#294035;
}
.header p{
color:#8c9991;
font-size:13px;
}
.container{
margin-top:30px;
display:grid;
grid-template-columns:1fr 1fr;
gap:25px;
}
.card{
padding:30px;
border-radius:20px;
background:white;
box-shadow:0 10px 35px rgba(40,80,55,.08);
}
.card-title span{
font-size:9px;
letter-spacing:2px;
color:#93a299;
}
.card-title h2{
margin-top:8px;
font-size:20px;
color:#36483d;
}
.status-list{
margin-top:25px;
display:flex;
flex-direction:column;
gap:25px;
}
.status-item{
display:flex;
gap:20px;
align-items:center;
}
.icon{
width:55px;
height:55px;
display:grid;
place-items:center;
border-radius:16px;
background:#edf5ef;
font-size:25px;
}
.content{
flex:1;
}
.content h3{
margin:0;
font-size:13px;
color:#738178;
}
.content strong{
display:block;
margin:8px 0;
font-size:25px;
color:#315941;
}
.progress{
height:8px;
border-radius:8px;
overflow:hidden;
background:#edf1ed;
}
.progress div{
height:100%;
background:linear-gradient(90deg,#4d956b,#8ac69d);
}
.generate,.send{
width:100%;
height:48px;
margin-top:25px;
border:none;
border-radius:12px;
cursor:pointer;
font-size:14px;
}
.generate{
color:white;
background:linear-gradient(135deg,#619d75,#376b4d);
}
.send{
color:#426b51;
background:#eaf3ed;
}
.command-box{
margin-top:25px;
padding:20px;
border-radius:15px;
background:#f5f8f5;
line-height:2.5;
color:#637269;
}
.command-box strong{
color:#315c42;
}
.running{
color:#3e9b62!important;
}
.message{
margin-top:20px;
padding:12px;
border-radius:10px;
text-align:center;
color:#34724b;
background:#e9f5ec;
font-size:13px;
}
@media(max-width:900px){
.container{
grid-template-columns:1fr;
}
}
</style>