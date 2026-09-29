(function () {
  "use strict";

  // 基础信息管理后端（houduan_jichuxinxiguanli.py），监听 5002
const API_BASIC = "";

  // 各页面 -> 后端接口 + 显示字段（字段名与后端返回 JSON 的 key 一致）
  const modules = {
    crop: {
      title: "作物管理",
      endpoint: "/api/zuowuguanli",
      columns: [
        { key: "name", label: "作物名称" },
        { key: "growth_stage", label: "生育期" },
        { key: "water_coeff", label: "需水系数" },
        { key: "fertilizer_coeff", label: "施肥系数" },
        { key: "suitable_soil", label: "适宜土壤" }
      ]
    },
    soil: {
      title: "土壤参数管理",
      endpoint: "/api/turangcanshuguanli",
      columns: [
        { key: "texture", label: "土壤质地" },
        { key: "bulk_density", label: "容重(g/cm³)" },
        { key: "field_capacity", label: "田间持水量(%)" },
        { key: "ec", label: "电导率(dS/m)" },
        { key: "ph", label: "pH" },
        { key: "other_params", label: "其他参数" }
      ]
    },
    device: {
      title: "设备信息",
      endpoint: "/api/shebeixinxiguanli",
      columns: [
        { key: "name", label: "设备名称" },
        { key: "type", label: "设备类型" },
        { key: "status", label: "设备状态" },
        { key: "water_tank_level", label: "水箱液位" },
        { key: "fert_tank_level", label: "肥箱液位" }
      ]
    },
    fertilizer: {
      title: "肥料信息",
      endpoint: "/api/feiliaoxinxiguanli",
      columns: [
        { key: "name", label: "肥料名称" },
        { key: "n_content", label: "氮含量(%)" },
        { key: "p_content", label: "磷含量(%)" },
        { key: "k_content", label: "钾含量(%)" }
      ]
    }
  };

  let currentPage = "crop";
  const searchState = {};
  const cache = {}; // module -> 行数据

  function esc(s) {
    if (s === null || s === undefined) return "";
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function fmt(v) {
    if (v === "" || v === null || v === undefined) return "—";
    return esc(v);
  }

  async function apiGet(url) {
    const res = await fetch(url, { credentials: "omit" });
    if (!res.ok) throw new Error("HTTP " + res.status);
    return res.json();
  }

  async function render() {
    const mod = modules[currentPage];
    document.getElementById("pageTitle").textContent = mod.title;
    const content = document.getElementById("content");
    content.innerHTML =
      '<div class="banner">基础信息由后端数据库维护（当前接口为只读查询）。后端地址：' + API_BASIC + "</div>" +
      '<div class="loading">正在加载数据…</div>';
    try {
      const json = await apiGet(API_BASIC + mod.endpoint);
      if (json.code !== 200) throw new Error(json.msg || "接口返回异常");
      cache[currentPage] = json.data || [];
      content.innerHTML = buildTable(currentPage);
    } catch (e) {
      content.innerHTML =
        '<div class="err-box">加载失败：' + esc(e.message) +
        "<br>请确认后端服务已启动（python houduan_jichuxinxiguanli.py，监听 5002）且已安装 flask-cors。</div>";
    }
    bindContent();
  }

  function buildTable(key) {
    const mod = modules[key];
    let rows = cache[key] || [];
    const q = (searchState[key] || "").trim().toLowerCase();
    if (q) {
      rows = rows.filter(function (r) {
        return mod.columns.some(function (c) {
          return String(r[c.key] === undefined ? "" : r[c.key]).toLowerCase().indexOf(q) > -1;
        });
      });
    }
    const head = "<th>#</th>" + mod.columns.map(function (c) { return "<th>" + esc(c.label) + "</th>"; }).join("");
    let body;
    if (rows.length === 0) {
      body = '<tr><td class="empty" colspan="' + (mod.columns.length + 1) + '">暂无数据</td></tr>';
    } else {
      body = rows
        .map(function (r, i) {
          return (
            "<tr><td>" + (i + 1) + "</td>" +
            mod.columns.map(function (c) { return "<td>" + fmt(r[c.key]) + "</td>"; }).join("") +
            "</tr>"
          );
        })
        .join("");
    }
    return (
      '<div class="toolbar"><div class="left">' +
      '<input class="search" type="text" placeholder="搜索…" data-search="' + key + '" value="' + esc(searchState[key] || "") + '" />' +
      "</div></div>" +
      '<div class="panel"><table><thead><tr>' + head + "</tr></thead><tbody>" + body + "</tbody></table></div>"
    );
  }

  function bindContent() {
    document.querySelectorAll(".nav-item").forEach(function (btn) {
      btn.classList.toggle("active", btn.dataset.page === currentPage);
      btn.onclick = function () { currentPage = btn.dataset.page; render(); };
    });
    document.querySelectorAll("[data-search]").forEach(function (inp) {
      inp.oninput = function () {
        searchState[inp.dataset.search] = inp.value;
        document.getElementById("content").innerHTML = buildTable(inp.dataset.search);
        bindContent();
      };
    });
  }

  render();
})();
