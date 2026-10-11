const zhuangtai = { zonglan: null, yuce: null, juece: null, baogao: [], shebei: null, diqu_mingcheng: '雅安市雨城区' };
const $ = (id) => document.getElementById(id);
const zhuanyi = (value) => String(value ?? '').replace(/[&<>"']/g, (char) => ({ '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[char]));
const riqi = (value) => String(value ?? '').slice(5, 10);

// 鍓嶇缁熶竴鍦ㄨ繖閲屾帴鍏ュ悗绔嫾闊虫帴鍙ｃ€?
async function qingqiu(path, options = {}) {
  const response = await fetch(path, { headers: { 'Content-Type': 'application/json' }, ...options });
  const body = await response.json();
  if (!response.ok || body.code !== 200) throw new Error(body.message || '璇锋眰澶辫触');
  return body.data;
}
function xiaoxi(message, error = false) { const el = $('tishi'); el.textContent = message; el.style.background = error ? '#B45309' : '#0F766F'; el.style.color = '#fff'; el.classList.add('xianshi'); clearTimeout(window._tishi); window._tishi = setTimeout(() => el.classList.remove('xianshi'), 2800); }
function jinruPingtai() { $('dengluYe').style.display = 'none'; document.querySelector('.app').style.display = ''; }
function tuichuDenglu() { $('dengluYe').style.display = 'grid'; document.querySelector('.app').style.display = 'none'; }

function biao(columns, rows) {
  if (!rows?.length) return '<div class="jieguo-kong">鏆傛棤鏁版嵁</div>';
  return `<table class="biaoge"><thead><tr>${columns.map((x) => `<th>${x[0]}</th>`).join('')}</tr></thead><tbody>${rows.map((row) => `<tr>${columns.map((column) => { const value = typeof column[1] === 'function' ? column[1](row) : row[column[1]]; return `<td>${column[2] ? value : zhuanyi(value)}</td>`; }).join('')}</tr>`).join('')}</tbody></table>`;
}

function zhexian(labels, series) {
  const all = series.flatMap((item) => item.values.filter((value) => value !== null && value !== undefined && value !== '').map(Number).filter(Number.isFinite));
  if (!labels.length || !all.length) return '<div class="jieguo-kong">鏆傛棤瓒嬪娍鏁版嵁</div>';
  const width = 700, height = 220, left = 44, right = 18, top = 18, bottom = 34;
  const min = Math.min(0, ...all), max = Math.max(...all, 1), range = max - min || 1;
  const x = (i) => left + i * ((width - left - right) / Math.max(labels.length - 1, 1));
  const y = (v) => top + (max - v) / range * (height - top - bottom);
  const grids = [0, .5, 1].map((p) => { const gy = top + p * (height - top - bottom); const value = (max - p * range).toFixed(1); return `<line x1="${left}" y1="${gy}" x2="${width-right}" y2="${gy}" stroke="#E7E5E4"/><text x="3" y="${gy+4}" fill="#78716C" font-size="11">${value}</text>`; }).join('');
  const lines = series.map((item) => { const valid=item.values.map((value,i)=>({value,i})).filter((point)=>point.value!==null&&point.value!==undefined&&point.value!==''); const points = valid.map((point) => `${x(point.i)},${y(Number(point.value)||0)}`).join(' '); const dots = valid.map((point) => `<circle cx="${x(point.i)}" cy="${y(Number(point.value)||0)}" r="3.5" fill="#fff" stroke="${item.color}" stroke-width="2"><title>${item.name}锛?{point.value}</title></circle>`).join(''); return `<polyline points="${points}" fill="none" stroke="${item.color}" stroke-width="2.5" stroke-linejoin="round"/>${dots}`; }).join('');
  const xLabels = labels.map((label, i) => `<text x="${x(i)}" y="${height-10}" text-anchor="middle" fill="#78716C" font-size="10">${zhuanyi(label)}</text>`).join('');
  const legend = series.map((item, i) => `<g transform="translate(${left+i*110},8)"><line x1="0" y1="0" x2="18" y2="0" stroke="${item.color}" stroke-width="3"/><text x="23" y="4" fill="#78716C" font-size="10">${zhuanyi(item.name)}</text></g>`).join('');
  return `<svg viewBox="0 0 ${width} ${height}" role="img">${grids}${legend}${lines}${xLabels}</svg>`;
}
function zhuzhuang(labels, values, color = '#2D9B6C') {
  if (!labels.length) return '<div class="jieguo-kong">鏆傛棤缁熻鏁版嵁</div>';
  const width=700,height=220,left=38,right=18,top=18,bottom=34,max=Math.max(...values.map(Number),1), cell=(width-left-right)/labels.length;
  return `<svg viewBox="0 0 ${width} ${height}" role="img"><line x1="${left}" y1="${height-bottom}" x2="${width-right}" y2="${height-bottom}" stroke="#E7E5E4"/>${values.map((value,i)=>{const h=(Number(value)||0)/max*(height-top-bottom),bx=left+i*cell+cell*.22,bw=cell*.56,by=height-bottom-h;return `<rect x="${bx}" y="${by}" width="${bw}" height="${h}" fill="${color}" rx="2"><title>${labels[i]}锛?{value}</title></rect><text x="${bx+bw/2}" y="${by-5}" text-anchor="middle" fill="#1C1917" font-size="10">${value}</text><text x="${bx+bw/2}" y="${height-10}" text-anchor="middle" fill="#78716C" font-size="10">${zhuanyi(labels[i])}</text>`;}).join('')}</svg>`;
}

function xianshiPage(name) {
  document.querySelectorAll('.ye').forEach((el) => el.classList.toggle('xuanshi', el.id === name));
  document.querySelectorAll('#daohang button').forEach((el) => el.classList.toggle('xuanzhong', el.dataset.ye === name));
  const titles = { zonglan:['生产总览','今日田间概况'], jichu:['基础信息','基础信息管理'], jiance:['数据监测','数据录入与监测'], tianqi:['气象服务','雅安市雨城区天气分析'], yuce:['分析中心','未来需求预测'], juece:['决策中心','水肥决策'], baogao:['成果沉淀','报告中心'], shebei:['人工协同','人工操作管理'], xitong:['运行设置','系统管理'] };
  $('mianbao').textContent = titles[name][0]; $('biaoti').textContent = titles[name][1];
  if (name === 'zonglan') jiazaiZonglan(); if (name === 'jichu') jiazaiJichu('zuowu'); if (name === 'jiance') jiazaiLishi(); if (name === 'tianqi') jiazaiTianqi(); if (name === 'baogao') jiazaiBaogao(); if (name === 'shebei') jiazaiShebei(); if (name === 'xitong') jiazaiXitong();
}

async function jiazaiZonglan() {
  try {
    const data = await qingqiu('/api/zonglan'); zhuangtai.zonglan = data;
    $('zhibiao').innerHTML = `<div class="zhibiao"><p>浠婃棩鐩戞祴娆℃暟</p><b>${data.counts.jiance}</b><small>鏉℃湁鏁堣褰?/small></div><div class="zhibiao"><p>浠婃棩棰勮鏁?/p><b>${data.counts.yujing}</b><small>鎸夊綋鍓嶉槇鍊兼鏌?/small></div><div class="zhibiao"><p>浠婃棩鐢熸垚寤鸿鏁?/p><b>${data.counts.juece}</b><small>鏉℃按鑲ュ喅绛?/small></div>`;
    const decision=data.latest_decision||{}, weather=data.tianqi||[], summary=weather.map((x)=>`${riqi(x.yubaoriqi)} ${x.tianqi_leixing}`).join(' / ')||'鏆傛棤澶╂皵';
    $('zhuangtaiKa').innerHTML = '概览加载完成';
    const moisture=data.trends.jiance, irrigation=data.trends.guangai, fertilizer=data.trends.shifei, days=data.trends.tianqi;
    $('shiduTu').innerHTML=zhexian(moisture.map((x)=>riqi(x.jilu_shijian)),[{name:'鍦熷￥婀垮害',values:moisture.map((x)=>x.turang_shidu),color:'#2D9B6C'}]);
    guangaiTu.innerHTML=''; shifeiTu.innerHTML='';
    shifeiTu.innerHTML='';
    zonglanTianqiTu.innerHTML='';
    $('jueceCishuTu').innerHTML=zhuzhuang(data.trends.juece_count.map((x)=>riqi(x.riqi)),data.trends.juece_count.map((x)=>x.shuliang));
    $('yujingFenbuTu').innerHTML=zhuzhuang(data.trends.yujing.map((x)=>x.leixing),data.trends.yujing.map((x)=>x.shuliang),'#D97706');
  } catch (error) { xiaoxi(error.message,true); }
}

async function jiazaiJichu(leixing) {
  try {
    const rows=await qingqiu(`/api/jichu/${leixing}`);
    const configs={zuowu:[['名称','mingcheng'],['当前生育期','shengyujie'],['需水系数','xushui_xishu'],['需肥系数','xufei_xishu'],['适宜土壤','shiyi_turang'],['目标湿度','mubiao_shidu']],turang:[['质地','zhidi'],['容重','rongzhong'],['田间持水量','chitian_chishuiliang'],['电导率','dian_daolv'],['PH','ph'],['相关参数','qita']],feiliao:[['肥料名称','mingcheng'],['氮含量',x=>String(x.dan)+'%'],['磷含量',x=>String(x.lin)+'%'],['钾含量',x=>String(x.jia)+'%']]};
    $('jichuBiao').innerHTML=biao([...configs[leixing],['鎿嶄綔',x=>`<button class="xiao-anniu zhu" data-shanchu-jichu="${leixing}:${x.id}">鍒犻櫎</button>`,true]],rows);
    $('youganlanJieduan').style.display=leixing==='zuowu'?'block':'none';
    if(leixing==='zuowu'){jieduanBiao.innerHTML='';}
  } catch(error){xiaoxi(error.message,true);}
}

async function jiazaiLishi(params='') { try { const rows=await qingqiu('/api/shuju/lishi'+params); lishiBiao.innerHTML=biao([['时间','jilu_shijian'],['作物','zuowu_mingcheng'],['生育期','shengyujie'],['土壤湿度',x=>String(x.turang_shidu)+'%'],['土壤温度',x=>String(x.turang_wendu)+'℃'],['空气湿度',x=>String(x.kongqi_shidu)+'%'],['光照','guangzhao'],['EC','dian_daolv']],rows); } catch(error){xiaoxi(error.message,true);} }

function xianshiHanlao(data){const e=data.hanlao_evaluation||{};const b=document.getElementById('hanlaoPingjia');if(b)b.textContent='旱涝急转评价：'+(e.status==='ok'?((e.events||[]).length?'发现事件':'未发现跨阈值事件'):(e.message||'数据不足'));}
function xianshiTianqi(data){xianshiHanlao(data);const rows=data.forecast_list||[];tianqiXiangqing.innerHTML=rows.map((x)=>'<div><h3>'+zhuanyi(x.yubaoriqi)+'</h3><p>最高/最低温：<b>'+x.zuigao_wendu+' / '+x.zuidi_wendu+'℃</b></p><p>降雨量：<b>'+x.jiangyu_liang+' mm</b></p></div>').join('');}

function xianshiYuce(data){zhuangtai.yuce=data;yuceZhuangtai.textContent='已生成';yuceJieguo.textContent=(data.fenxi||'预测已完成');}

const fengxianYanse={'low':'#2D9B6C','normal':'#2D9B6C','medium':'#D97706','high':'#B45309','unknown':'#78716C'};
const zhuangtaiYanse={'鍋忎綆':'#2D9B6C','姝ｅ父':'#2D9B6C','鍋忛珮':'#B45309','鏈煡':'#78716C'};
function xianshiAiFenxi(data){
  zhuangtai.aiFenxi=data;
  $('aiFenxiQu').style.display='block';
  const jiangji=data.fallback_used;
  $('aiMoxingXinxi').textContent=`妯″瀷锛?{data.model||'鏈煡'} 路 鐗堟湰锛?{data.model_version||'--'} 路 缃俊搴︼細${(data.confidence||0).toFixed(2)} 路 鑰楁椂锛?{data.elapsed_time||0}s 路 ${new Date().toLocaleString('zh-CN',{hour12:false})}`;
  $('aiJiangjiBiaoji').innerHTML=jiangji?`<span class="jiangji-biaoji">瑙勫垯闄嶇骇</span>`:`<span class="zhengchang-biaoji">AI鍒嗘瀽</span>`;
  const ir=data.recommended_irrigation||{},fe=data.recommended_fertilizer||{};
  const forecast=(data.three_day_forecast||[]).map((f)=>`<div class="yuce-ri"><h4>${zhuanyi(f.date||'')}</h4><p>闇€姘磋秼鍔匡細<b style="color:${fengxianYanse.unknown}">${zhuanyi(f.water_demand_trend||'鏈煡')}</b></p><p>闇€鑲ヨ秼鍔匡細<b>${zhuanyi(f.fertilizer_demand_trend||'鏈煡')}</b></p><p>${zhuanyi(f.irrigation_suggestion||'')}</p><p>${zhuanyi(f.fertilizer_suggestion||'')}</p>${f.risk_note?`<p class="fengxian-tishi">鈿?${zhuanyi(f.risk_note)}</p>`:''}</div>`).join('');
  const missing='';
  const warnings='';
  const basis=(data.decision_basis||[]).map((b)=>`<li>${zhuanyi(b)}</li>`).join('');
  aiFenxiJieguo.textContent='AI分析结果已返回，需人工确认后执行。';
}
function xianshiAnquanJiaoyan(jieguo){
  $('anquanJiaoyanQu').style.display='block';
  const statusColor={approved:'#2D9B6C',manual_review:'#D97706',rejected:'#B45309'};
  $('anquanZhuangtai').textContent=`鐘舵€侊細${jieguo.status} 路 閫氳繃锛?{jieguo.passed?'鏄?:'鍚?}`;
  const items=(jieguo.checked_items||[]).map((item)=>`<tr><td>${zhuanyi(item.name)}</td><td style="color:${item.passed?'#2D9B6C':'#B45309'}">${item.passed?'閫氳繃':'鏈€氳繃'}</td><td>${zhuanyi(item.desc)}</td></tr>`).join('');
  const warnings=(jieguo.warnings||[]).map((w)=>`<li>${zhuanyi(w)}</li>`).join('');
  const blocked=(jieguo.blocked_reasons||[]).map((r)=>`<li>${zhuanyi(r)}</li>`).join('');
  $('anquanJiaoyanJieguo').innerHTML=`<div class="anquan-zhuangtai" style="border-left:4px solid ${statusColor[jieguo.status]||'#78716C'};padding:8px 12px;margin-bottom:12px"><b style="color:${statusColor[jieguo.status]||'#78716C'}">${jieguo.status==='approved'?'閫氳繃鍩虹鏍￠獙':jieguo.status==='manual_review'?'闇€浜哄伐澶嶆牳':'绂佹鎵ц'}</b></div><table class="biaoge"><thead><tr><th>鏍￠獙椤?/th><th>缁撴灉</th><th>璇存槑</th></tr></thead><tbody>${items}</tbody></table>${warnings?`<div class="yujing-tishi"><b>璀﹀憡锛?/b><ul>${warnings}</ul></div>`:''}${blocked?`<div class="zuzhi-yuanyin"><b>闃绘鍘熷洜锛?/b><ul>${blocked}</ul></div>`:''}`;
}

function xianshiJuece(data){zhuangtai.juece=data;jueceZhuangtai.textContent='已生成';jueceJieguo.textContent=data.reason||'决策已生成';const c=data.confidence_evaluation||{};const box=kexinduPingjia;if(box)box.innerHTML='<b>决策可信度：'+(c.level||'未知')+'（'+(c.score??'--')+'）</b><br>可靠性 R：'+(c.dimensions?.reliability??'--')+'，安全性 S：'+(c.dimensions?.security??'--')+'，可恢复性 Re：'+(c.dimensions?.recoverability??'--')+'，完整性 I：'+(c.dimensions?.integrity??'--')+'<br><small>'+zhuanyi(c.decision||'')+'；'+zhuanyi(c.method||'')+'</small>';shengchengCanshu.disabled=false;}
function xianshiCanshu(){const d=zhuangtai.juece;if(!d)return;$('zhilingQu').innerHTML=`<div class="juece-xiang"><div><small>鐏屾簤閲?/small><b>${d.recommended_irrigation} L/浜?/b></div><div><small>鏂借偉閲?/small><b>${d.recommended_fertilization} kg/浜?/b></div><div><small>娉佃繍琛?/small><b>${d.pump_runtime} min</b></div></div><p class="juece-yuanyin">璇ュ弬鏁颁笉浼氳嚜鍔ㄥ彂閫佸埌璁惧锛岃鐜板満浜哄憳澶嶆牳銆?/p><button id="shengchengCaozuodan" class="zhu-anniu kuan">鐢熸垚浜哄伐鎿嶄綔鍗?/button>`;$('shengchengCaozuodan').onclick=shengchengCaozuodan;}
async function shengchengCaozuodan(){try{const d=zhuangtai.juece;const result=await qingqiu('/api/zhiling',{method:'POST',body:JSON.stringify({shebei_id:1,guangai_liang:d.recommended_irrigation,shifei_liang:d.recommended_fertilization,beng_yunxing:d.pump_runtime,caozuo_beizhu:'软件生成参数，等待现场人员复核'})});xiaoxi(result.shuoming);jiazaiShebei();}catch(error){xiaoxi(error.message,true);}}

async function jiazaiShebei(){try{const data=await qingqiu('/api/shebei');zhuangtai.shebei=data;xianshiCanshu();$('zhilingBiao').innerHTML=biao([['编号','id'],['灌溉量',x=>`${x.guangai_liang} L/亩`],['施肥量',x=>`${x.shifei_liang} kg/亩`],['泵运行',x=>`${x.beng_yunxing} min`],['操作进度','zhuangtai'],['创建时间','chuangjian_shijian'],['人工操作',x=>`<div class="caozuo-zu">${x.zhuangtai==='待人工执行'?`<button class="xiao-anniu zhu" data-queren="${x.id}">确认已传达</button>`:''}<button class="xiao-anniu" data-fankui="${x.id}">登记执行量</button><button class="xiao-anniu" data-shanchu-zhiling="${x.id}">删除</button></div>`,true]],data.orders);}catch(error){xiaoxi(error.message,true);}}

async function jiazaiBaogao(){try{const rows=await qingqiu('/api/baogao');zhuangtai.baogao=rows;baogaoBiao.innerHTML=biao([['报告标题','biaoti'],['作物','zuowu'],['创建时间','chuangjian_shijian'],['状态','zhuangtai']],rows);}catch(error){xiaoxi(error.message,true);}}
async function chakanBaogao(id){try{const row=await qingqiu(`/api/baogao/${id}`);$('motaiBiaoti').textContent=row.biaoti;const names={basic_info:'鍩虹淇℃伅',monitor_summary:'鐩戞祴鏁版嵁鎽樿',weather_summary:'澶╂皵鎽樿',prediction:'姘磋偉鍒嗘瀽缁撴灉',decision:'鍐崇瓥寤鸿',risk:'椋庨櫓璇存槑',device_suggestion:'浜哄伐鎿嶄綔寤鸿',manual_operation:'浜哄伐鎿嶄綔寤鸿'};$('motaiZhengwen').innerHTML=Object.entries(row.neirong).map(([key,value])=>`<section class="baogao-fenqu"><h3>${zhuanyi(names[key]||key)}</h3><pre>${zhuanyi(JSON.stringify(value,null,2))}</pre></section>`).join('');$('motaikuang').classList.add('xianshi');}catch(error){xiaoxi(error.message,true);}}
async function daochuBaogao(id){try{await qingqiu('/api/baogao/'+id+'/daochu',{method:'POST',body:JSON.stringify({daochuren:'系统管理员'})});jiazaiBaogao();}catch(error){xiaoxi(error.message,true);}}

async function jiazaiXitong(){try{const [thresholds,logs]=await Promise.all([qingqiu('/api/xitong/yujing'),qingqiu('/api/xitong/rizhi')]);yuzhiBiao.innerHTML=biao([['指标','mingcheng'],['最小值','zuixiao'],['最大值','zuida'],['预警等级','dengji']],thresholds);rizhiBiao.innerHTML=biao([['操作时间','caozuo_shijian'],['操作类型','caozuo_leixing'],['操作内容','caozuo_neirong'],['操作人','caozuoren']],logs);}catch(error){xiaoxi(error.message,true);}}

document.querySelectorAll('#daohang button').forEach((el)=>el.onclick=()=>xianshiPage(el.dataset.ye));
document.querySelectorAll('#jichuFenlei button').forEach((el)=>el.onclick=()=>{document.querySelectorAll('#jichuFenlei button').forEach((x)=>x.classList.remove('xuanzhong'));el.classList.add('xuanzhong');jiazaiJichu(el.dataset.leixing);});
document.querySelectorAll('#jianceFenlei button').forEach((el)=>el.onclick=()=>{document.querySelectorAll('#jianceFenlei button').forEach((x)=>x.classList.remove('xuanzhong'));document.querySelectorAll('#jiance .zimian').forEach((x)=>x.classList.remove('xuanshi'));el.classList.add('xuanzhong');$(el.dataset.zimian).classList.add('xuanshi');if(el.dataset.zimian==='lishi')jiazaiLishi();});
$('dengluBiao').onsubmit=async(event)=>{event.preventDefault();const data=Object.fromEntries(new FormData(event.target));try{await qingqiu('/api/denglu',{method:'POST',body:JSON.stringify(data)});if($('jizhuMima').checked)localStorage.setItem('shuiFeiJizhu',JSON.stringify({zhanghao:data.zhanghao,mima:data.mima}));else localStorage.removeItem('shuiFeiJizhu');jinruPingtai();xianshiPage('zonglan');xiaoxi('鐧诲綍鎴愬姛');}catch(error){$('dengluTishi').textContent=error.message;$('dengluTishi').style.color='#b44f42';}};
$('dengluBtn').onclick=tuichuDenglu;
jianceBiao.onsubmit=async(event)=>{event.preventDefault();try{const data=Object.fromEntries(new FormData(event.target));await qingqiu('/api/shuju/luru',{method:'POST',body:JSON.stringify(data)});xiaoxi('监测数据已保存');jiazaiLishi();}catch(error){xiaoxi(error.message,true);}};
$('piliangBiao').onsubmit=async(event)=>{event.preventDefault();const form=new FormData(event.target);try{const response=await fetch('/api/shuju/piliang',{method:'POST',body:form});const body=await response.json();if(!response.ok||body.code!==200)throw new Error(body.message);$('daoruJieguo').innerHTML=`<div class="shuo-ming">鎴愬姛 ${body.data.success} 鏉★紝澶辫触 ${body.data.failed} 鏉°€?/div>`;xiaoxi('鎵归噺瀵煎叆瀹屾垚');}catch(error){xiaoxi(error.message,true);}};
$('lishiShaixuan').onsubmit=(event)=>{event.preventDefault();const data=Object.fromEntries(new FormData(event.target));const query=new URLSearchParams(Object.entries(data).filter((x)=>x[1])).toString();jiazaiLishi(query?`?${query}`:'');};
shuaxinTianqi.onclick=async()=>{try{const data=await qingqiu('/api/tianqi/shuaxin',{method:'POST',body:'{}'});xianshiTianqi(data);xiaoxi('天气更新成功');}catch(error){xiaoxi(error.message,true);}};
document.querySelectorAll('#tianqiDiquFenlei button').forEach((el)=>el.onclick=()=>{document.querySelectorAll('#tianqiDiquFenlei button').forEach((x)=>x.classList.remove('xuanzhong'));el.classList.add('xuanzhong');zhuangtai.tianqi_diqu=el.dataset.diqu;jingweiBiao.style.display=el.dataset.diqu==='zidingyi'?'flex':'none';if(el.dataset.diqu==='yucheng')jiazaiTianqi();});
$('jingweiBiao').onsubmit=async(event)=>{event.preventDefault();const data=Object.fromEntries(new FormData(event.target));try{xianshiTianqi(await qingqiu(`/api/tianqi/jingwei?lat=${data.weidu}&lon=${data.jingdu}&diming=${encodeURIComponent(data.diming||`缁忕含搴?${data.weidu},${data.jingdu})`)}`));xiaoxi('澶╂皵鏌ヨ鎴愬姛');}catch(error){xiaoxi(error.message,true);}};
yuceBiao.onsubmit=async(event)=>{event.preventDefault();try{const data=Object.fromEntries(new FormData(event.target));data.shiyong_tianqi=true;xianshiYuce(await qingqiu('/api/yuce',{method:'POST',body:JSON.stringify(data)}));xiaoxi('预测已生成');}catch(error){xiaoxi(error.message,true);}};
aiFenxiBtn.onclick=async()=>{try{const form=new FormData(yuceBiao);const result=await qingqiu('/api/yucefenxi/ai-analyze',{method:'POST',body:JSON.stringify({crop_id:Number(form.get('zuowu_id')),forecast_range:Number(form.get('tianshu')),weather_enabled:true})});aiFenxiQu.style.display='block';xianshiAiFenxi(result);xiaoxi(result.fallback_used?'AI已降级':'AI分析完成');}catch(error){xiaoxi(error.message,true);}};
document.querySelectorAll('#yuceDiquFenlei button').forEach((el)=>el.onclick=()=>{document.querySelectorAll('#yuceDiquFenlei button').forEach((x)=>x.classList.remove('xuanzhong'));el.classList.add('xuanzhong');yuceJingweiBiao.style.display=el.dataset.diqu==='zidingyi'?'flex':'none';});
jueceBiao.onsubmit=async(event)=>{event.preventDefault();try{const raw=Object.fromEntries(new FormData(event.target));raw.yuce=zhuangtai.yuce;xianshiJuece(await qingqiu('/api/juece',{method:'POST',body:JSON.stringify(raw)}));xiaoxi('决策建议已生成');}catch(error){xiaoxi(error.message,true);}};
jueceAiFenxiBtn.onclick=async()=>{try{const form=new FormData(jueceBiao);const result=await qingqiu('/api/yucefenxi/ai-analyze',{method:'POST',body:JSON.stringify({crop_id:Number(form.get('zuowu_id')),forecast_range:3,weather_enabled:true})});xianshiAiFenxi(result);xiaoxi(result.fallback_used?'AI已降级':'AI分析完成');}catch(error){xiaoxi(error.message,true);}};
$('shengchengCanshu').onclick=()=>{xianshiCanshu();xianshiPage('shebei');};$('shuaxinShebei').onclick=jiazaiShebei;
shengchengBaogao.onclick=async()=>{try{await qingqiu('/api/baogao',{method:'POST',body:JSON.stringify({diqu:zhuangtai.diqu_mingcheng||'雅安市雨城区'})});xiaoxi('报告已生成');jiazaiBaogao();}catch(error){xiaoxi(error.message,true);}};
baogaoBiao.onclick=()=>{};
zhilingBiao.onclick=()=>{};
$('yuzhiBiao').onclick=async(event)=>{const button=event.target.closest('[data-save-yuzhi]');if(!button)return;const id=button.dataset.saveYuzhi;const min=document.querySelector(`[data-id="${id}"][data-field="zuixiao"]`).value,max=document.querySelector(`[data-id="${id}"][data-field="zuida"]`).value;try{await qingqiu(`/api/xitong/yujing/${id}`,{method:'PUT',body:JSON.stringify({zuixiao:Number(min),zuida:Number(max),dengji:button.dataset.dengji,shuoming:button.dataset.shuoming})});xiaoxi('闃堝€煎凡鏇存柊');jiazaiXitong();}catch(error){xiaoxi(error.message,true);}};
$('guanbiMotai').onclick=()=> $('motaikuang').classList.remove('xianshi');$('motaikuang').onclick=(event)=>{if(event.target===$('motaikuang'))$('motaikuang').classList.remove('xianshi');};
jichuBiao.onclick=()=>{};
$('lishiBiao').onclick=async(event)=>{const btn=event.target.closest('[data-shanchu-shuju]');if(!btn)return;if(!confirm('纭鍒犻櫎璇ョ洃娴嬭褰曪紵'))return;try{await qingqiu(`/api/shuju/${btn.dataset.shanchuShuju}`,{method:'DELETE'});xiaoxi('鍒犻櫎鎴愬姛');jiazaiLishi();}catch(e){xiaoxi(e.message,true);}};
setInterval(()=>$('shijian').textContent=new Date().toLocaleString('zh-CN',{hour12:false}),1000);$('shijian').textContent=new Date().toLocaleString('zh-CN',{hour12:false});
document.querySelector('.app').style.display='none';
localStorage.removeItem('shuiFeiDengLu');
try {
  const jizhu = JSON.parse(localStorage.getItem('shuiFeiJizhu') || 'null');
  if (jizhu?.zhanghao && jizhu?.mima) {
    $('dengluBiao').elements.zhanghao.value = jizhu.zhanghao;
    $('dengluBiao').elements.mima.value = jizhu.mima;
    $('jizhuMima').checked = true;
  }
} catch (error) {
  localStorage.removeItem('shuiFeiJizhu');
}
