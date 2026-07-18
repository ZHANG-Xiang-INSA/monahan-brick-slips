/* i18n — zh default, EN toggle. data-i18n="key" on elements; JS strings via T(key). */
(function () {
  "use strict";

  window.I18N = {
    // nav
    nav_summary:   { zh: "项目总览",   en: "Summary" },
    nav_model:     { zh: "三维模型",   en: "3D Model" },
    nav_elev:      { zh: "立面图册",   en: "Elevations" },
    nav_cutting:   { zh: "切割图",     en: "Cutting" },

    // hero
    hero_kicker:   { zh: "施工文档 · 砖片系统", en: "Construction Document · Brick Slip System" },
    hero_sub:      { zh: "英国珀利 · 莫纳汉大道 3 号", en: "Purley, United Kingdom" },
    hero_doc:      { zh: "砖片排布定位与工程量清单", en: "Brick Slip Setting-Out & Quantity Schedule" },
    rev_label:     { zh: "当前修订", en: "Revision" },
    rev_name:      { zh: "黑砖转角平贴", en: "Black Corners Flat" },
    rev_notice:    { zh: "修订说明 — 本版变更", en: "Revision Notice — Changes in this issue" },
    rev_item1:     { zh: "全部转角改为平贴对拼（逐皮交错压边），取消所有 L 型砖片", en: "All corners converted to flat slip pairs (staggered quoin per course); no L-slips anywhere" },
    rev_item2:     { zh: "雨棚山墙原有空隙已全部填补", en: "Gable voids filled" },
    rev_item3:     { zh: "灰缝统一为 10 mm 标准缝", en: "Joints normalized to 10 mm" },
    btn_explore:   { zh: "浏览三维模型", en: "Explore Model" },
    btn_elev:      { zh: "查看立面图", en: "View Elevations" },
    quick_cap:     { zh: "快速入口", en: "Quick Entry" },
    quick_red:     { zh: "红砖", en: "Red" },
    quick_black:   { zh: "黑砖", en: "Black" },
    quick_clips:   { zh: "卡扣", en: "Clips" },
    hero_figcap:   { zh: "西北正立面（入口） · 排砖图摘录", en: "NW front elevation (entrance) · layout extract" },

    // summary
    sum_title:     { zh: "项目总览", en: "Project Summary" },
    sum_en:        { zh: "PROJECT SUMMARY", en: "工程量总览" },
    s_total:       { zh: "砖片总数", en: "Total slips" },
    s_total_sub:   { zh: "红砖 + 黑砖", en: "red + black" },
    s_red:         { zh: "红砖砖片", en: "Red slips" },
    s_red_sub:     { zh: "四面主墙", en: "four main walls" },
    s_black:       { zh: "黑砖砖片", en: "Black slips" },
    s_black_sub:   { zh: "入口雨棚", en: "entrance canopy" },
    s_clips:       { zh: "安装卡扣", en: "Clips" },
    s_clips_sub:   { zh: "10 种规格", en: "10 types" },
    s_screws:      { zh: "螺钉", en: "Screws" },
    s_screws_sub:  { zh: "每孔一钉", en: "one per hole" },
    s_area:        { zh: "铺贴面积", en: "Coverage area" },
    s_area_sub:    { zh: "11 个立面", en: "11 faces" },
    u_pcs:         { zh: "片", en: "pcs" },
    u_ea:          { zh: "件", en: "ea" },

    // 3D viewer
    model_title:   { zh: "三维模型", en: "3D Model" },
    model_en:      { zh: "3D MODEL", en: "三维模型" },
    vb_layers:     { zh: "图层", en: "Layers" },
    layer_red:     { zh: "红砖", en: "Red" },
    layer_black:   { zh: "黑砖", en: "Black" },
    layer_clips:   { zh: "卡扣", en: "Clips" },
    btn_reset:     { zh: "重置视角", en: "Reset View" },
    btn_viewall:   { zh: "整体视图", en: "View All" },
    btn_fs:        { zh: "全屏", en: "Fullscreen" },
    btn_fs_exit:   { zh: "退出全屏", en: "Exit Fullscreen" },
    v_help:        { zh: "左键拖动旋转 · 滚轮缩放 · 右键平移 · 点击墙面跳转对应立面", en: "Drag to orbit · wheel to zoom · right-drag to pan · click a wall to open its elevation" },
    v_loading:     { zh: "正在构建模型几何…", en: "Building model geometry…" },
    v_fail:        { zh: "三维视图不可用（WebGL 或网络受限）。", en: "3D view unavailable (WebGL or network restricted)." },
    v_fail_link:   { zh: "改为查看立面图 →", en: "View the elevations instead →" },
    v_count:       { zh: "构件", en: "entities" },

    // elevation explorer
    elev_title:    { zh: "立面图册", en: "Elevation Explorer" },
    elev_en:       { zh: "ELEVATIONS", en: "立面图册" },
    fl_cap:        { zh: "立面清单 · 11 个面", en: "Face index · 11 faces" },
    seg_bricks:    { zh: "砖面排布", en: "Bricks" },
    seg_clips:     { zh: "卡扣排布", en: "Clips" },
    btn_open_dv:   { zh: "打开图纸查看器", en: "Open Drawing Viewer" },
    fd_hint:      { zh: "点击放大", en: "click to enlarge" },
    st_area:       { zh: "铺贴面积", en: "Area" },
    st_bricks:     { zh: "砖片", en: "Slips" },
    st_corner:     { zh: "转角平贴片", en: "Corner flats" },
    st_clips:      { zh: "卡扣", en: "Clips" },
    st_screws:     { zh: "螺钉", en: "Screws" },
    st_types:      { zh: "砖型数", en: "Brick types" },
    tbl_toggle:    { zh: "工程量明细表", en: "Detail schedule" },
    tbl_bricks:    { zh: "砖片明细", en: "Brick schedule" },
    tbl_clips:     { zh: "卡扣明细", en: "Clip schedule" },
    th_type:       { zh: "类型编号", en: "Type ID" },
    th_size:       { zh: "规格 W×H (mm)", en: "Size W×H (mm)" },
    th_qty:        { zh: "数量", en: "Qty" },
    th_len:        { zh: "长度 (mm)", en: "Length (mm)" },
    th_screws:     { zh: "螺钉", en: "Screws" },
    row_total:     { zh: "合计", en: "Total" },
    kind_brick:    { zh: "砖面排布图", en: "Brick layout drawing" },
    kind_clip:     { zh: "卡扣排布图", en: "Clip layout drawing" },

    // cutting
    cut_title:     { zh: "切割图", en: "Cutting Drawings" },
    cut_en:        { zh: "CUTTING DRAWINGS", en: "切割图" },
    cut_bricks:    { zh: "砖片切割排样图", en: "Brick cutting types sheet" },
    cut_clips:     { zh: "卡扣切割排样图", en: "Clip cutting types sheet" },
    cut_bricks_sub:{ zh: "46 种砖型 · 1:1 轮廓", en: "46 brick types · true outlines" },
    cut_clips_sub: { zh: "10 种卡扣 · 含 40° 斜切", en: "10 clip types · incl. 40° mitres" },
    btn_open:      { zh: "打开", en: "Open" },
    cut_note:      { zh: "注：58 张单型号切割卡片将于第二阶段提供。", en: "Note: the 58 per-type cutting cards follow in Phase 2." },

    // drawing viewer overlay
    dv_reset:      { zh: "重置", en: "Reset" },
    dv_prev:       { zh: "上一张", en: "Prev" },
    dv_next:       { zh: "下一张", en: "Next" },
    dv_download:   { zh: "下载 SVG", en: "Download SVG" },
    dv_close:      { zh: "关闭", en: "Close" },
    dv_help:       { zh: "滚轮缩放 · 拖拽平移 · 双击放大 · Esc 关闭", en: "Wheel zoom · drag to pan · double-click zoom · Esc to close" },

    // misc / footer
    ph2:           { zh: "第二阶段", en: "Phase 2" },
    foot_doc:      { zh: "砖片排布定位与工程量清单 · 第一阶段网页版", en: "Brick Slip Setting-Out & Quantity Schedule · web edition, phase 1" },
    foot_rev:      { zh: "REV 06 — 黑砖转角平贴", en: "REV 06 — Black Corners Flat" }
  };

  var lang = "zh";
  window.LANG = function () { return lang; };
  window.T = function (key) {
    var e = window.I18N[key];
    if (!e) return key;
    return e[lang] || e.zh;
  };

  function applyStatic() {
    document.documentElement.setAttribute("lang", lang === "zh" ? "zh-CN" : "en");
    var nodes = document.querySelectorAll("[data-i18n]");
    for (var i = 0; i < nodes.length; i++) {
      nodes[i].textContent = window.T(nodes[i].getAttribute("data-i18n"));
    }
    var b = document.querySelectorAll(".lang-toggle button");
    for (var j = 0; j < b.length; j++) {
      b[j].classList.toggle("active", b[j].getAttribute("data-lang") === lang);
    }
  }

  window.setLang = function (l) {
    if (l !== "zh" && l !== "en") return;
    lang = l;
    applyStatic();
    document.dispatchEvent(new CustomEvent("langchange"));
  };

  document.addEventListener("DOMContentLoaded", function () {
    var b = document.querySelectorAll(".lang-toggle button");
    for (var j = 0; j < b.length; j++) {
      b[j].addEventListener("click", function () { window.setLang(this.getAttribute("data-lang")); });
    }
    applyStatic();
  });
})();
