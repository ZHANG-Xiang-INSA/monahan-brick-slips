/* i18n — zh default, EN toggle. data-i18n="key" for text, data-i18n-ph="key"
   for input placeholders; JS strings via T(key). */
(function () {
  "use strict";

  window.I18N = {
    // nav
    nav_summary:   { zh: "项目总览",   en: "Summary" },
    nav_model:     { zh: "三维模型",   en: "3D Model" },
    nav_elev:      { zh: "立面图册",   en: "Elevations" },
    nav_cutting:   { zh: "切割图",     en: "Cutting" },

    // hero
    btn_explore:   { zh: "浏览三维模型", en: "Explore 3D Model" },
    btn_elev:      { zh: "查看立面图", en: "View Elevations" },

    // summary
    sum_title:     { zh: "项目总览", en: "Project Summary" },
    s_total:       { zh: "总砖片", en: "Total slips" },
    s_total_sub:   { zh: "红砖 + 黑砖", en: "red + black" },
    s_red:         { zh: "红砖", en: "Red slips" },
    s_red_sub:     { zh: "四面主墙", en: "four main walls" },
    s_black:       { zh: "黑砖", en: "Black slips" },
    s_black_sub:   { zh: "入口雨棚", en: "entrance canopy" },
    s_clips:       { zh: "卡扣", en: "Clips" },
    s_clips_sub:   { zh: "10 种规格", en: "10 types" },
    s_screws:      { zh: "螺钉", en: "Screws" },
    s_screws_sub:  { zh: "每孔一钉", en: "one per hole" },
    s_area:        { zh: "铺贴面积", en: "Coverage area" },
    s_area_sub:    { zh: "11 个立面", en: "11 faces" },
    u_pcs:         { zh: "片", en: "pcs" },
    u_ea:          { zh: "件", en: "ea" },

    // 3D viewer
    model_title:   { zh: "三维模型", en: "3D Model" },
    model_sub:     { zh: "7,697 砖片 + 2,215 卡扣 · 逐片建模，可交互查看", en: "7,697 slips + 2,215 clips · modelled piece by piece, fully interactive" },
    seg_all:       { zh: "全部", en: "All" },
    layer_red:     { zh: "红砖", en: "Red" },
    layer_black:   { zh: "黑砖", en: "Black" },
    layer_clips:   { zh: "卡扣", en: "Clips" },
    btn_reset:     { zh: "重置", en: "Reset" },
    btn_fit:       { zh: "适应窗口", en: "Fit View" },
    btn_fs:        { zh: "全屏", en: "Fullscreen" },
    btn_fs_exit:   { zh: "退出全屏", en: "Exit Fullscreen" },
    v_labels:      { zh: "标注", en: "Labels" },
    v_help:        { zh: "左键拖动旋转 · 滚轮缩放 · 右键平移 · 点击墙面跳转对应立面", en: "Drag to orbit · wheel to zoom · right-drag to pan · click a wall to open its elevation" },
    v_loading:     { zh: "正在构建模型几何…", en: "Building model geometry…" },
    v_fail:        { zh: "三维视图不可用（WebGL 或网络受限），已显示静态预览。", en: "3D view unavailable (WebGL or network restricted) — showing a static preview." },
    v_fail_link:   { zh: "查看立面图", en: "View Elevations" },
    v_static_cap:  { zh: "RED-03 · 西北正立面（入口）· 静态预览", en: "RED-03 · NW front elevation (entrance) · static preview" },
    v_count:       { zh: "构件", en: "entities" },

    // elevation workbench
    elev_title:    { zh: "立面图册", en: "Elevation Explorer" },
    elev_sub:      { zh: "11 个立面 · 排砖图与卡扣图", en: "11 faces · brick & clip layout drawings" },
    search_ph:     { zh: "搜索立面…", en: "Search faces…" },
    flt_all:       { zh: "全部", en: "All" },
    flt_red:       { zh: "红砖", en: "Red" },
    flt_black:     { zh: "黑砖", en: "Black" },
    fl_empty:      { zh: "无匹配立面", en: "No matching faces" },
    seg_bricks:    { zh: "砖面排布", en: "Bricks" },
    seg_clips:     { zh: "卡扣排布", en: "Clips" },
    btn_fit_view:  { zh: "适应", en: "Fit" },
    fd_hint:       { zh: "滚轮缩放 · 拖拽平移 · 双击放大", en: "Wheel zoom · drag to pan · double-click" },
    rail_cap:      { zh: "本立面参数", en: "Face data" },
    st_area:       { zh: "铺贴面积", en: "Area" },
    st_bricks:     { zh: "砖片数量", en: "Slips" },
    st_corner:     { zh: "转角平贴片", en: "Corner flats" },
    st_clips:      { zh: "卡扣", en: "Clips" },
    st_screws:     { zh: "螺钉", en: "Screws" },
    st_types:      { zh: "砖型数量", en: "Brick types" },
    btn_schedule:  { zh: "打开工程量明细表", en: "Open Quantity Schedule" },
    btn_collapse:  { zh: "收起", en: "Collapse" },
    tbl_cap:       { zh: "工程量明细表", en: "Quantity schedule" },
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
    cut_sub:       { zh: "1:1 切割排样 · SVG 矢量文件", en: "1:1 cutting layouts · SVG vector files" },
    cut_bricks:    { zh: "砖片切割排样图", en: "Brick Cutting Schedule" },
    cut_clips:     { zh: "卡扣成型与切割图", en: "Guiding-Rail Clip — Forming & Cutting" },
    cut_bricks_sub:{ zh: "46 种砖型 · 1:1 真实轮廓", en: "46 brick types · true 1:1 outlines" },
    cut_clips_sub: { zh: "10 型 · M 形成型钢 · 展开料 118 · 含 40° 斜切", en: "10 types · formed M-section · 118 blank · incl. 40° mitres" },
    ct_types:      { zh: "型号数", en: "Types" },
    ct_scale:      { zh: "比例", en: "Scale" },
    nts:           { zh: "示意 NTS", en: "NTS" },
    ct_format:     { zh: "格式", en: "Format" },
    btn_open_dwg:  { zh: "打开图纸", en: "Open Drawing" },
    btn_download:  { zh: "下载 SVG", en: "Download SVG" },
    cut_note:      { zh: "注：卡扣为成型钢导轨（M 形断面：底面 68 + 腿 15 + 内钩唇 10，向上开口 62.5，展开料 118，t=0.25），非平钢片；各型号开孔位置见上图。", en: "Note: clips are formed steel guiding rails (M-section: 68 base + 15 legs + 10 inward lips, 62.5 upward opening, 118 developed blank, t=0.25) — not flat strips. Hole positions per type above." },

    // drawing viewer overlay
    dv_reset:      { zh: "重置", en: "Reset" },
    dv_prev:       { zh: "上一张", en: "Prev" },
    dv_next:       { zh: "下一张", en: "Next" },
    dv_download:   { zh: "下载 SVG", en: "Download SVG" },
    dv_close:      { zh: "关闭", en: "Close" },
    dv_help:       { zh: "滚轮缩放 · 拖拽平移 · 双击放大 · Esc 关闭", en: "Wheel zoom · drag to pan · double-click zoom · Esc to close" },

    // footer
    foot_doc:      { zh: "砖片排布定位与工程量清单", en: "Brick Slip Setting-Out & Quantity Schedule" }
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
    var phs = document.querySelectorAll("[data-i18n-ph]");
    for (var p = 0; p < phs.length; p++) {
      phs[p].setAttribute("placeholder", window.T(phs[p].getAttribute("data-i18n-ph")));
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
