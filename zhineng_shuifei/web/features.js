(() => {
  const nav = document.getElementById('daohang');
  const main = document.querySelector('.neirong');
  if (!nav || !main) return;

  const labels = { turang: '土壤分级', bingchonghai: 'YOLO分析' };
  for (const [id, label] of Object.entries(labels)) {
    const button = document.createElement('button');
    button.type = 'button';
    button.dataset.ye = id;
    button.textContent = label;
    nav.appendChild(button);
  }

  main.insertAdjacentHTML('beforeend', `
    <section id="turang" class="ye mianban">
      <article class="mokuai">
        <div class="mokuai-toubu"><div><h2>土壤质地分级</h2><p>支持手动输入和中国土壤栅格点采样；CG-RecNet 结构待土壤标签数据训练。</p></div><span id="soilDataStatus">正在检查栅格数据</span></div>
        <div class="feature-grid">
          <form id="soilGradeForm" class="feature-panel">
            <h3>手动输入</h3>
            <label>砂粒含量 sand (%)<input name="sand_pct" type="number" min="0" max="100" step="0.1" value="40" required></label>
            <label>黏粒含量 clay (%)<input name="clay_pct" type="number" min="0" max="100" step="0.1" value="20" required></label>
            <label>粉粒含量 silt (%)<input name="silt_pct" type="number" min="0" max="100" step="0.1" placeholder="留空时由100-sand-clay计算"></label>
            <button class="zhu-anniu" type="submit">执行质地分级</button>
          </form>
          <form id="soilSampleForm" class="feature-panel">
            <h3>栅格点采样</h3>
            <p class="feature-note">按数据栅格的0起始行、列编号读取单个单元，不会将大栅格整体载入内存。</p>
            <div class="feature-fields"><label>行 row<input name="row" type="number" min="0" step="1" required></label><label>列 col<input name="col" type="number" min="0" step="1" required></label></div>
            <button class="ci-anniu" type="submit">采样并分级</button>
          </form>
          <div id="soilGradeResult" class="feature-panel feature-result" aria-live="polite"><h3>分级结果</h3><p>输入组成或采样栅格点后显示结果。</p></div>
        </div>
      </article>
    </section>
    <section id="bingchonghai" class="ye mianban">
      <article class="mokuai">
        <div class="mokuai-toubu"><div><h2>YOLO分析</h2><p>上传图片后，可分别查看病虫害识别和橄榄果实识别结果。</p></div><span id="pestModelStatus">正在检查模型</span></div>
        <div class="feature-grid pest-grid">
          <form id="pestAnalyzeForm" class="feature-panel">
            <h3>上传图片</h3>
            <label id="pestDrop" class="drop-zone">选择或拖入 PNG / JPG 图片<input id="pestImage" name="image" type="file" accept="image/png,image/jpeg,.png,.jpg,.jpeg" required></label>
            <img id="pestPreview" class="pest-preview" alt="待分析图片预览" hidden>
            <div class="feature-fields">
              <label>气温 (°C，可选)<input name="temperature" type="number" step="0.1" min="-20" max="60"></label>
              <label>空气湿度 (%)<input name="humidity" type="number" step="0.1" min="0" max="100"></label>
              <label>近期降雨量 (mm)<input name="rainfall" type="number" step="0.1" min="0" max="1000"></label>
            </div>
            <button class="zhu-anniu" type="submit">分析图片</button>
          </form>
          <div id="pestResult" class="feature-panel feature-result" aria-live="polite">
            <div class="pest-tabs" role="tablist" aria-label="YOLO分析结果分类">
              <button type="button" class="pest-tab active" data-pest-tab="disease">病虫害识别</button>
              <button type="button" class="pest-tab" data-pest-tab="fruit">果实识别</button>
            </div>
            <section id="pestTabDisease" class="pest-tab-panel active" data-pest-panel="disease"><h3>病虫害识别</h3><p>上传图片后显示病虫害分类结果。</p></section>
            <section id="pestTabFruit" class="pest-tab-panel" data-pest-panel="fruit"><h3>果实识别</h3><p>上传图片后显示果实检测框和置信度。</p></section>
          </div>
        </div>
      </article>
    </section>`);

  const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  async function featureRequest(path, options = {}) {
    const response = await fetch(path, options);
    let body;
    try { body = await response.json(); } catch { throw new Error(`服务返回非JSON响应（HTTP ${response.status}）`); }
    if (!response.ok || body.success === false) throw new Error(body.error || body.message || `请求失败（HTTP ${response.status}）`);
    return body.data ?? body;
  }
  function showPage(id) {
    document.querySelectorAll('.ye').forEach((page) => page.classList.toggle('xuanshi', page.id === id));
    nav.querySelectorAll('button').forEach((button) => button.classList.toggle('xuanzhong', button.dataset.ye === id));
    document.getElementById('mianbao').textContent = '土壤与植保分析';
    document.getElementById('biaoti').textContent = labels[id];
    if (id === 'turang') loadSoilStatus(); else loadPestStatus();
  }
  nav.addEventListener('click', (event) => {
    const button = event.target.closest('button[data-ye]');
    if (button && labels[button.dataset.ye]) showPage(button.dataset.ye);
  });

  function renderSoil(result) {
    document.getElementById('soilGradeResult').innerHTML = `<h3>${escapeHtml(result.texture)}</h3>
      <p>砂粒 ${escapeHtml(result.sand_pct)}% · 粉粒 ${escapeHtml(result.silt_pct)}% · 黏粒 ${escapeHtml(result.clay_pct)}%</p>
      <p>${escapeHtml(result.method || '可解释质地规则')}</p>
      ${result.grid ? `<p>栅格位置：row ${escapeHtml(result.grid.row)}，col ${escapeHtml(result.grid.col)}</p>` : ''}
      <p class="feature-warning">${escapeHtml(result.limitations || '该结果为规则分级，不代表已训练模型精度。')}</p>`;
  }
  async function loadSoilStatus() {
    const el = document.getElementById('soilDataStatus');
    try {
      const status = await featureRequest('/api/turang/data-status');
      el.textContent = status.available ? `栅格可用：${(status.layers || []).join(', ')}` : '未找到本地土壤栅格';
    } catch (error) { el.textContent = error.message; }
  }
  document.getElementById('soilGradeForm').addEventListener('submit', async (event) => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.currentTarget));
    if (data.silt_pct === '') delete data.silt_pct;
    const out = document.getElementById('soilGradeResult'); out.innerHTML = '<p>正在计算…</p>';
    try { renderSoil(await featureRequest('/api/turang/fenji', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) })); }
    catch (error) { out.innerHTML = `<p class="feature-error">${escapeHtml(error.message)}</p>`; }
  });
  document.getElementById('soilSampleForm').addEventListener('submit', async (event) => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.currentTarget));
    const out = document.getElementById('soilGradeResult'); out.innerHTML = '<p>正在读取单个栅格单元…</p>';
    try { renderSoil(await featureRequest('/api/turang/sample', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) })); }
    catch (error) { out.innerHTML = `<p class="feature-error">${escapeHtml(error.message)}</p>`; }
  });

  async function loadPestStatus() {
    try {
      const status = await featureRequest('/api/bingchonghai/model-status');
      const yolo = status.yolo_detail || {};
      document.getElementById('pestModelStatus').textContent = status.mode || yolo.status || '规则降级';
    } catch (error) { document.getElementById('pestModelStatus').textContent = error.message; }
  }
  const imageInput = document.getElementById('pestImage');
  const preview = document.getElementById('pestPreview');
  let previewUrl = null;
  function setFile(file) {
    if (!file) return;
    if (!['image/png', 'image/jpeg'].includes(file.type) && !/\.(png|jpe?g)$/i.test(file.name)) {
      imageInput.value = ''; throw new Error('只支持PNG/JPG/JPEG图片');
    }
    if (file.size > 8 * 1024 * 1024) { imageInput.value = ''; throw new Error('图片不能超过8MB'); }
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    previewUrl = URL.createObjectURL(file); preview.src = previewUrl; preview.hidden = false;
  }
  imageInput.addEventListener('change', () => {
    try { setFile(imageInput.files[0]); } catch (error) { document.getElementById('pestResult').innerHTML = `<p class="feature-error">${escapeHtml(error.message)}</p>`; }
  });
  const drop = document.getElementById('pestDrop');
  ['dragenter', 'dragover'].forEach((name) => drop.addEventListener(name, (event) => { event.preventDefault(); drop.classList.add('dragging'); }));
  ['dragleave', 'drop'].forEach((name) => drop.addEventListener(name, (event) => { event.preventDefault(); drop.classList.remove('dragging'); }));
  drop.addEventListener('drop', (event) => {
    const file = event.dataTransfer.files[0];
    if (!file) return;
    try { setFile(file); const transfer = new DataTransfer(); transfer.items.add(file); imageInput.files = transfer.files; }
    catch (error) { document.getElementById('pestResult').innerHTML = `<p class="feature-error">${escapeHtml(error.message)}</p>`; }
  });
  document.getElementById('pestAnalyzeForm').addEventListener('submit', async (event) => {
    event.preventDefault();
    const file = imageInput.files[0];
    if (!file) return;
    const form = new FormData(event.currentTarget);
    const environment = {};
    for (const key of ['temperature', 'humidity', 'rainfall']) {
      if (form.get(key) !== '') environment[key] = Number(form.get(key));
    }
    form.append('environment', JSON.stringify(environment));
    const out = document.getElementById('pestResult'); out.innerHTML = '<p>正在分析图片…</p>';
    try {
      const result = await featureRequest('/api/bingchonghai/analyze', { method: 'POST', body: form });
      const d = result.diagnosis || {}, visual = result.visual_features || {}, status = result.model_status || {}, assist = result.dual_branch_assist || {};
      const visualRows = Object.entries(visual).filter(([key]) => key.endsWith('_pct')).map(([key, value]) => `<li>${escapeHtml(key)}：${escapeHtml(value)}%</li>`).join('');
      const detectionRows = (result.detections || []).map((item) => {
        const box = Array.isArray(item.box) ? item.box.join(', ') : '未提供';
        return `<li>${escapeHtml(item.label || '未命名类别')} · 置信度 ${escapeHtml((Number(item.confidence || 0) * 100).toFixed(1))}% · 框 [${escapeHtml(box)}]</li>`;
      }).join('');
      const sources = Object.values(result.theory?.sources || {}).map((source) => `<li><a href="${escapeHtml(source.url || '#')}" target="_blank" rel="noreferrer">${escapeHtml(source.name || '模型来源')}</a>：${escapeHtml(source.role || '')}</li>`).join('');
      const trend = result.lstm?.trend?.length ? result.lstm.trend.map(escapeHtml).join(' → ') : '数据不足';
      const yoloDetail = status.yolo_detail || {};
      const dualDetail = status.dual_branch_detail || {};
      out.innerHTML = `<h3>${escapeHtml(d.label || '图像已接收')}</h3>
        <p>环境风险：${escapeHtml(d.risk || '数据不足')}${d.score == null ? '' : `（规则评分 ${escapeHtml(d.score)}）`}</p>
        <h4>图像颜色特征（非病种诊断）</h4><ul>${visualRows || '<li>未提取到可展示的颜色统计</li>'}</ul>
        <h4>YOLO 检测框</h4><ul>${detectionRows || '<li>当前没有真实检测框，可能是模型待部署或未检出目标。</li>'}</ul>
        <h4>模型状态</h4><p>YOLO：${status.yolo ? '已部署' : '规则降级'}（${escapeHtml(yoloDetail.status || '未配置权重')}） · 双分支：${status.dual_branch ? '已部署' : '结构已接入/待油橄榄权重'}（${escapeHtml(dualDetail.status || '待训练')}） · LSTM：${status.lstm ? '已部署' : '规则降级'} · 随机森林：${status.random_forest ? '已部署' : '规则降级'}</p>
        ${result.model_message ? `<p>本次推理：${escapeHtml(result.model_message)}</p>` : ''}
        ${result.model_error ? `<p class="feature-warning">模型提示：${escapeHtml(result.model_error)}</p>` : ''}
        <h4>双分支特征辅助</h4><p>${escapeHtml(assist.status || '未提取')}${assist.prediction ? `：${escapeHtml(assist.prediction)}（${escapeHtml((Number(assist.score || 0) * 100).toFixed(1))}%）` : ''}。${escapeHtml(assist.note || assist.score_note || '')}</p>
        <h4>接入来源</h4><ul>${sources || '<li>当前无模型来源信息</li>'}</ul>
        <h4>风险趋势</h4><p>${trend}</p>
        <p class="feature-warning">${escapeHtml(result.review || '结果需人工复核。')}</p>`;
    } catch (error) { out.innerHTML = `<p class="feature-error">${escapeHtml(error.message)}</p>`; }
  });
})();
// 中文化图像特征字段，保留后端原始键名以兼容已有接口。
const IMAGE_FEATURE_LABELS = {
  green_pixel_pct: '绿色像素占比',
  yellow_brown_pixel_pct: '黄褐色像素占比',
  lesion_pixel_pct: '疑似病斑像素占比',
  brightness_mean: '平均亮度',
  saturation_mean: '平均饱和度',
  contrast_mean: '平均对比度'
};

(function translateImageFeatureLabels() {
  if (typeof document === 'undefined') return;
  const replacements = Object.entries(IMAGE_FEATURE_LABELS);
  const translate = (root) => {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    let node;
    while ((node = walker.nextNode())) nodes.push(node);
    nodes.forEach((textNode) => {
      let value = textNode.nodeValue;
      replacements.forEach(([key, label]) => {
        value = value.replace(new RegExp(key, 'g'), label);
      });
      if (value !== textNode.nodeValue) textNode.nodeValue = value;
    });
  };
  const start = () => {
    translate(document.body);
    if (typeof MutationObserver !== 'undefined' && document.body) {
      const observer = new MutationObserver((records) => {
        records.forEach((record) => {
          record.addedNodes.forEach((node) => {
            if (node.nodeType === Node.TEXT_NODE) {
              let value = node.nodeValue;
              replacements.forEach(([key, label]) => {
                value = value.replace(new RegExp(key, 'g'), label);
              });
              node.nodeValue = value;
            } else if (node.nodeType === Node.ELEMENT_NODE) {
              translate(node);
            }
          });
        });
      });
      observer.observe(document.body, { childList: true, subtree: true });
    }
  };
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start, { once: true });
  } else {
    start();
  }
})();

// 隐藏不参与业务判断的说明性提示，保留对应分析结果和操作控件。
(function removeUnwantedAdvisoryText() {
  if (typeof document === 'undefined') return;
  const patterns = [
    '风险趋势',
    '数据不足',
    '图片颜色统计和环境规则分值不能确认病虫害。请由植保人员复核；其他作物论文类别和精度不能外推到油橄榄。',
    '图片颜色统计和环境规则分值不能确认病虫害',
    '请由植保人员复核',
    '其他作物论文类别和精度不能外推到油橄榄',
    '该结果为规则分级，不代表已训练模型精度。',
    '该结果为规则分级',
    '人工协同模式',
    '本软件不连接水肥一体化机。页面只生成参数，由人员传达并登记实际执行量。',
    '本软件不连接水肥一体化机',
    '页面只生成参数，由人员传达并登记实际执行量'
  ];
  const matches = (value) => patterns.some((pattern) => String(value || '').includes(pattern));
  const removeMatches = (root) => {
    if (!root || root.nodeType !== Node.ELEMENT_NODE) return;
    const elements = [root, ...root.querySelectorAll('*')];
    // Remove the smallest matching element so a wrapper containing the
    // advisory text cannot leave the old sentence visible.
    elements.reverse().forEach((element) => {
      const text = element.textContent || '';
      if (!matches(text)) return;
      const childMatches = [...element.children].some((child) => matches(child.textContent || ''));
      if (!childMatches && element !== document.body) element.remove();
    });
  };
  const start = () => {
    removeMatches(document.body);
    if (typeof MutationObserver !== 'undefined' && document.body) {
      const observer = new MutationObserver((records) => {
        records.forEach((record) => record.addedNodes.forEach((node) => {
          if (node.nodeType === Node.ELEMENT_NODE) removeMatches(node);
        }));
      });
      observer.observe(document.body, { childList: true, subtree: true });
    }
  };
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start, { once: true });
  } else {
    start();
  }
})();

// 清理旧版静态节点（部分页面使用 data-label/title 或模板字符串生成标题）。
(function removeLegacyLabels() {
  if (typeof document === 'undefined') return;
  const labels = new Set(['风险趋势', '数据不足', '人工协同模式']);
  const clean = () => {
    document.querySelectorAll('[data-label], [title], [aria-label]').forEach((el) => {
      ['data-label', 'title', 'aria-label'].forEach((attr) => {
        if (labels.has(el.getAttribute(attr))) el.removeAttribute(attr);
      });
    });
    document.querySelectorAll('h1,h2,h3,h4,h5,h6,p,li,span,div,small,strong,label').forEach((el) => {
      if (labels.has((el.textContent || '').trim())) el.remove();
    });
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', clean, { once: true });
  else clean();
})();
