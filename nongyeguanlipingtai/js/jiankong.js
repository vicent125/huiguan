(function () {
  "use strict";

  // 数据录入与监测后端（houduan_shujuluruyujiance.py），监听 5001
const API = "";

  // 表单字段：key 与后端数据库列名一致（英文），label 仅用于显示
  const monitorSchema = [
    { key: "crop_id", label: "作物ID", type: "number", required: true },
    { key: "growth_stage", label: "生育期", type: "text" },
    { key: "soil_moisture", label: "土壤湿度", type: "number", unit: "%" },
    { key: "soil_temp", label: "土壤温度", type: "number", unit: "℃" },
    { key: "air_humidity", label: "空气湿度", type: "number", unit: "%" },
    { key: "light_intensity", label: "光照强度", type: "number", unit: "lux" },
    { key: "ec", label: "电导率", type: "number", unit: "dS/m" }
  ];
  // 历史表格显示列（含后端返回的 record_time）
  const historyColumns = [
    { key: "record_time", label: "记录时间" },
    { key: "crop_id", label: "作物ID" },
    { key: "growth_stage", label: "生育期" },
    { key: "soil_moisture", label: "土壤湿度(%)" },
    { key: "soil_temp", label: "土壤温度(℃)" },
    { key: "air_humidity", label: "空气湿度(%)" },
    { key: "light_intensity", label: "光照强度(lux)" },
    { key: "ec", label: "电导率(dS/m)" }
  ];

  const PAGE_TITLE = { manual: "手动录入", import: "批量导入", history: "历史监测数据" };

  let currentPage = "manual";
  let historyFilter = null; // { start, end, crop }
  let pendingFile = null;   // 待导入的原始文件

  function esc(s) {
    if (s === null || s === undefined) return "";
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function fmt(v, unit) {
    if (v === "" || v === null || v === undefined) return "—";
    return unit ? esc(v) + " " + unit : esc(v);
  }
  function fieldHtml(f, val) {
    const req = f.required ? '<span class="req">*</span>' : "";
    const step = f.step ? ' step="' + f.step + '"' : "";
    const control = '<input type="' + (f.type || "text") + '" name="' + f.key + '" value="' + esc(val) + '"' + step + " />";
    const hint = f.unit ? '<div class="hint">单位：' + esc(f.unit) + "</div>" : "";
    return '<div class="field"><label>' + esc(f.label) + req + "</label>" + control + hint + "</div>";
  }

  async function apiGet(url) {
    const r = await fetch(url, { credentials: "omit" });
    if (!r.ok) throw new Error("HTTP " + r.status);
    return r.json();
  }
  async function apiPostJSON(url, obj) {
    const r = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(obj)
    });
    if (!r.ok) throw new Error("HTTP " + r.status);
    return r.json();
  }
  async function apiPostForm(url, form) {
    const r = await fetch(url, { method: "POST", body: form });
    if (!r.ok) throw new Error("HTTP " + r.status);
    return r.json();
  }

  /* ---------- 渲染 ---------- */
  async function render() {
    document.getElementById("pageTitle").textContent = PAGE_TITLE[currentPage];
    const content = document.getElementById("content");
    if (currentPage === "manual") {
      content.innerHTML = renderManual();
      await loadRecent();
    } else if (currentPage === "import") {
      content.innerHTML = renderImport();
    } else {
      content.innerHTML = renderHistory();
      await loadHistory();
    }
    bindContent();
  }

  // 手动录入
  function renderManual() {
    const form = monitorSchema.map(function (f) { return fieldHtml(f, ""); }).join("");
    return (
      '<div class="form-card"><form id="manualForm">' + form +
      '<div class="msg" id="manualMsg"></div>' +
      '<div class="form-actions">' +
      '<button type="button" class="btn btn-primary" id="manualSave">保存录入</button>' +
      '<button type="button" class="btn btn-ghost" id="manualReset">重置</button>' +
      "</div></form>" +
      '<div class="recent"><h4>最近录入</h4><div id="recentList"><div class="section-title">加载中…</div></div></div></div>'
    );
  }
  async function loadRecent() {
    try {
      const json = await apiGet(API + "/api/lishijiance");
      const rows = (json.data || []).slice(0, 5);
      const el = document.getElementById("recentList");
      if (!el) return;
      if (rows.length === 0) { el.innerHTML = '<div class="section-title">暂无录入记录</div>'; return; }
      el.innerHTML =
        '<ul class="recent-list">' +
        rows
          .map(function (r) {
            return (
              '<li><span class="dot"></span><b>' + esc(r.record_time || "—") + "</b> · 作物 " +
              esc(r.crop_id == null ? "—" : r.crop_id) + " · " + (r.growth_stage ? esc(r.growth_stage) : "生育期未填") +
              " · 湿度 " + (r.soil_moisture != null ? esc(r.soil_moisture) + "%" : "—") + "</li>"
            );
          })
          .join("") +
        "</ul>";
    } catch (e) {
      const el = document.getElementById("recentList");
      if (el) el.innerHTML = '<div class="section-title">加载最近记录失败：' + esc(e.message) + "</div>";
    }
  }

  // 批量导入
  function renderImport() {
    return (
      '<div class="form-card">' +
      '<div class="import-zone">' +
      '<p class="section-title">上传 Excel / CSV，列名需为英文且一致：' +
      monitorSchema.map(function (f) { return f.key; }).join("、") + "（crop_id 为整数）。</p>" +
      '<div class="toolbar"><button type="button" class="btn btn-ghost" id="dlTemplate">下载模板</button>' +
      '<label class="btn btn-primary">选择文件<input type="file" id="fileInput" accept=".xlsx,.xls,.csv" hidden></label></div>' +
      '<div class="msg" id="importMsg"></div>' +
      "</div>" +
      '<div id="importPreview"></div>' +
      "</div>"
    );
  }

  // 历史监测数据
  function renderHistory() {
    const f = historyFilter || {};
    return (
      '<div class="filter-bar">' +
      '<label>起始日期<input type="date" id="fStart" value="' + esc(f.start || "") + '"></label>' +
      '<label>结束日期<input type="date" id="fEnd" value="' + esc(f.end || "") + '"></label>' +
      '<label>作物ID<input type="text" id="fCrop" placeholder="可选（本地筛选）" value="' + esc(f.crop || "") + '"></label>' +
      '<button type="button" class="btn btn-primary" id="fQuery">查询</button>' +
      '<button type="button" class="btn btn-ghost" id="fClear">显示全部</button>' +
      "</div>" +
      '<div id="historyResult"><div class="loading">正在加载…</div></div>'
    );
  }
  async function loadHistory() {
    const el = document.getElementById("historyResult");
    if (!el) return;
    let url = API + "/api/lishijiance";
    if (historyFilter && historyFilter.start && historyFilter.end) {
      url += "?start_date=" + encodeURIComponent(historyFilter.start) + "&end_date=" + encodeURIComponent(historyFilter.end);
    }
    try {
      const json = await apiGet(url);
      let rows = json.data || [];
      if (historyFilter && historyFilter.crop) {
        const c = historyFilter.crop.toLowerCase();
        rows = rows.filter(function (r) { return String(r.crop_id == null ? "" : r.crop_id).toLowerCase().indexOf(c) > -1; });
      }
      if (rows.length === 0) { el.innerHTML = '<div class="panel"><div class="empty">无匹配的历史监测记录</div></div>'; return; }
      const head = "<th>#</th>" + historyColumns.map(function (c) { return "<th>" + esc(c.label) + "</th>"; }).join("");
      const body = rows
        .map(function (r, i) {
          return (
            "<tr><td>" + (i + 1) + "</td>" +
            historyColumns.map(function (c) { return "<td>" + fmt(r[c.key]) + "</td>"; }).join("") +
            "</tr>"
          );
        })
        .join("");
      el.innerHTML =
        '<div class="result-count">共 ' + rows.length + " 条记录</div>" +
        '<div class="panel"><table><thead><tr>' + head + "</tr></thead><tbody>" + body + "</tbody></table></div>";
    } catch (e) {
      el.innerHTML = '<div class="err-box">加载失败：' + esc(e.message) + "<br>请确认后端（监听 5001）已启动且已安装 flask-cors。</div>";
    }
  }

  /* ---------- 文件解析（仅用于上传前预览） ---------- */
  function mapRow(o) {
    const rec = {};
    let has = false;
    monitorSchema.forEach(function (f) {
      let v = o[f.key] !== undefined ? o[f.key] : "";
      v = String(v).trim();
      if (f.type === "number" && v !== "") v = Number(v);
      if (v !== "") has = true;
      rec[f.key] = v;
    });
    return has ? rec : null;
  }
  function splitCSVLine(line) {
    const res = [];
    let cur = "";
    let q = false;
    for (let i = 0; i < line.length; i++) {
      const c = line[i];
      if (c === '"') {
        if (q && line[i + 1] === '"') { cur += '"'; i++; } else { q = !q; }
      } else if (c === "," && !q) { res.push(cur); cur = ""; } else { cur += c; }
    }
    res.push(cur);
    return res;
  }
  function parseCSV(text) {
    const lines = text.split(/\r?\n/).filter(function (l) { return l.trim() !== ""; });
    if (lines.length < 2) throw new Error("文件无数据行");
    const headers = splitCSVLine(lines[0]).map(function (h) { return h.trim(); });
    return lines
      .slice(1)
      .map(function (line) {
        const cells = splitCSVLine(line);
        const o = {};
        headers.forEach(function (h, i) { o[h] = cells[i] !== undefined ? cells[i].trim() : ""; });
        return mapRow(o);
      })
      .filter(function (r) { return r; });
  }
  function previewFile(file) {
    const msg = document.getElementById("importMsg");
    const name = file.name.toLowerCase();
    const reader = new FileReader();
    const onDone = function (rows) {
      pendingFile = file;
      if (!rows || rows.length === 0) {
        msg.className = "msg err";
        msg.textContent = "未解析到有效数据，请检查列名是否为：" + monitorSchema.map(function (f) { return f.key; }).join(", ");
        document.getElementById("importPreview").innerHTML = "";
        return;
      }
      const head = monitorSchema.map(function (f) { return "<th>" + esc(f.label) + "</th>"; }).join("");
      const body = rows.slice(0, 10)
        .map(function (r) { return "<tr>" + monitorSchema.map(function (f) { return "<td>" + fmt(r[f.key]) + "</td>"; }).join("") + "</tr>"; })
        .join("");
      const more = rows.length > 10 ? '<div class="result-count">仅预览前 10 条，共 ' + rows.length + " 条待导入</div>" : "";
      document.getElementById("importPreview").innerHTML =
        more +
        '<div class="panel"><table><thead><tr>' + head + "</tr></thead><tbody>" + body + "</tbody></table></div>" +
        '<div class="form-actions"><button type="button" class="btn btn-primary" id="importConfirm">确认导入 ' + rows.length + " 条</button></div>";
      msg.className = "msg ok";
      msg.textContent = "解析成功，确认后将上传至后端导入数据库。";
    };
    if (name.endsWith(".csv")) {
      reader.onload = function () {
        try { onDone(parseCSV(reader.result)); }
        catch (e) { msg.className = "msg err"; msg.textContent = "解析失败：" + e.message; }
      };
      reader.readAsText(file, "utf-8");
    } else {
      reader.onload = function () {
        try {
          if (!window.XLSX) { msg.className = "msg err"; msg.textContent = "Excel 预览库未加载，请联网后刷新；仍可直接确认导入（后端负责解析）。"; return; }
          const wb = XLSX.read(new Uint8Array(reader.result), { type: "array" });
          const ws = wb.Sheets[wb.SheetNames[0]];
          const json = XLSX.utils.sheet_to_json(ws, { defval: "" });
          onDone(json.map(mapRow).filter(function (r) { return r; }));
        } catch (e) { msg.className = "msg err"; msg.textContent = "解析失败：" + e.message; }
      };
      reader.readAsArrayBuffer(file);
    }
  }
  function downloadTemplate() {
    const headers = monitorSchema.map(function (f) { return f.key; });
    const sample = ["1", "拔节期", "62", "24.5", "78", "35000", "1.8"];
    const csv = [headers.join(","), sample.join(",")].join("\n");
    const blob = new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "监测数据导入模板.csv";
    a.click();
    URL.revokeObjectURL(a.href);
  }

  /* ---------- 事件绑定 ---------- */
  function bindContent() {
    document.querySelectorAll(".nav-item").forEach(function (btn) {
      btn.classList.toggle("active", btn.dataset.page === currentPage);
      btn.onclick = function () { currentPage = btn.dataset.page; render(); };
    });

    // 手动录入
    const manualSave = document.getElementById("manualSave");
    if (manualSave) {
      manualSave.onclick = async function () {
        const form = document.getElementById("manualForm");
        const obj = {};
        let ok = true;
        monitorSchema.forEach(function (f) {
          let v = form.elements[f.key] ? form.elements[f.key].value.trim() : "";
          if (f.type === "number") {
            if (v === "") v = null;
            else {
              v = Number(v);
              if (isNaN(v)) { ok = false; alert("字段「" + f.label + "」必须为数字"); }
            }
          }
          if (f.required && (v === "" || v === null)) { ok = false; alert("请填写必填项：" + f.label); }
          obj[f.key] = v;
        });
        if (!ok) return;
        const msg = document.getElementById("manualMsg");
        msg.className = "msg";
        msg.textContent = "提交中…";
        try {
          const json = await apiPostJSON(API + "/api/shoudongluru", obj);
          if (json.code !== 200) throw new Error(json.msg || "录入失败");
          msg.className = "msg ok";
          msg.textContent = json.msg || "录入成功！";
          form.reset();
          await loadRecent();
        } catch (e) {
          msg.className = "msg err";
          msg.textContent = "录入失败：" + e.message;
        }
      };
    }
    const manualReset = document.getElementById("manualReset");
    if (manualReset) {
      manualReset.onclick = function () {
        document.getElementById("manualForm").reset();
        const msg = document.getElementById("manualMsg");
        if (msg) { msg.textContent = ""; msg.className = "msg"; }
      };
    }

    // 批量导入
    const dl = document.getElementById("dlTemplate");
    if (dl) dl.onclick = downloadTemplate;
    const fileInput = document.getElementById("fileInput");
    if (fileInput) fileInput.onchange = function () { if (this.files[0]) previewFile(this.files[0]); };
    const impConfirm = document.getElementById("importConfirm");
    if (impConfirm) {
      impConfirm.onclick = async function () {
        if (!pendingFile) { alert("请先选择文件"); return; }
        const msg = document.getElementById("importMsg");
        msg.className = "msg";
        msg.textContent = "导入中…";
        try {
          const fd = new FormData();
          fd.append("file", pendingFile);
          const json = await apiPostForm(API + "/api/piliangdaoru", fd);
          if (json.code !== 200) throw new Error(json.msg || "导入失败");
          msg.className = "msg ok";
          msg.textContent = json.msg || "导入成功！";
          pendingFile = null;
          document.getElementById("importPreview").innerHTML = "";
        } catch (e) {
          msg.className = "msg err";
          msg.textContent = "导入失败：" + e.message;
        }
      };
    }

    // 历史筛选
    const fQuery = document.getElementById("fQuery");
    if (fQuery) {
      fQuery.onclick = function () {
        const start = document.getElementById("fStart").value;
        const end = document.getElementById("fEnd").value;
        const crop = document.getElementById("fCrop").value.trim();
        if (start && end && start > end) { alert("起始日期不能晚于结束日期"); return; }
        historyFilter = { start: start, end: end, crop: crop };
        loadHistory();
      };
    }
    const fClear = document.getElementById("fClear");
    if (fClear) {
      fClear.onclick = function () {
        historyFilter = null;
        document.getElementById("fStart").value = "";
        document.getElementById("fEnd").value = "";
        document.getElementById("fCrop").value = "";
        loadHistory();
      };
    }
  }

  render();
})();
