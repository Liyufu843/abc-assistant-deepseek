(function () {
  "use strict";
  // ==== 依赖自检：有的电脑 CDN 拉不到 Vue/antd，脚本会静默不显示面板 ====
  var __abcNeed = [
    { name: "Vue", test: function () { return typeof Vue !== "undefined"; }, urls: [
      "https://cdn.jsdelivr.net/npm/vue@3.4.31/dist/vue.global.prod.js",
      "https://unpkg.com/vue@3.4.31/dist/vue.global.prod.js",
      "https://cdn.staticfile.org/vue/3.4.31/vue.global.prod.js"
    ] },
    { name: "antd", test: function () { return typeof antd !== "undefined"; }, urls: [
      "https://cdn.jsdelivr.net/npm/ant-design-vue@4.2.6/dist/antd.min.js",
      "https://unpkg.com/ant-design-vue@4.2.6/dist/antd.min.js",
      "https://cdn.staticfile.org/ant-design-vue/4.2.6/antd.min.js"
    ] },
    { name: "Pinia", test: function () { return typeof Pinia !== "undefined"; }, urls: [
      "https://cdn.jsdelivr.net/npm/pinia@2.1.7/dist/pinia.iife.min.js",
      "https://unpkg.com/pinia@2.1.7/dist/pinia.iife.min.js",
      "https://cdn.staticfile.org/pinia/2.1.7/pinia.iife.min.js"
    ] },
    { name: "dayjs", test: function () { return typeof dayjs !== "undefined"; }, urls: [
      "https://cdn.jsdelivr.net/npm/dayjs@1.11.10/dayjs.min.js",
      "https://unpkg.com/dayjs@1.11.10/dayjs.min.js",
      "https://cdn.staticfile.org/dayjs/1.11.10/dayjs.min.js"
    ] },
    { name: "DOMPurify", test: function () { return typeof DOMPurify !== "undefined"; }, urls: [
      "https://cdn.jsdelivr.net/npm/dompurify@3.1.6/dist/purify.min.js",
      "https://unpkg.com/dompurify@3.1.6/dist/purify.min.js",
      "https://cdn.staticfile.org/dompurify/3.1.6/purify.min.js"
    ] },
    { name: "marked", test: function () { return typeof marked !== "undefined"; }, urls: [
      "https://cdn.jsdelivr.net/npm/marked@16.1.1/lib/marked.umd.min.js",
      "https://unpkg.com/marked@16.1.1/lib/marked.umd.min.js",
      "https://cdn.staticfile.org/marked/16.1.1/marked.umd.min.js"
    ] },
    { name: "rxjs", test: function () { return typeof rxjs !== "undefined"; }, urls: [
      "https://cdn.jsdelivr.net/npm/rxjs@7.8.1/dist/bundles/rxjs.umd.min.js",
      "https://unpkg.com/rxjs@7.8.1/dist/bundles/rxjs.umd.min.js",
      "https://cdn.staticfile.org/rxjs/7.8.1/rxjs.umd.min.js"
    ] },
    { name: "md5", test: function () { return typeof md5 !== "undefined"; }, urls: [
      "https://cdn.jsdelivr.net/npm/blueimp-md5@2.19.0/js/md5.min.js",
      "https://unpkg.com/blueimp-md5@2.19.0/js/md5.min.js",
      "https://cdn.staticfile.org/blueimp-md5/2.19.0/js/md5.min.js"
    ] }
  ];
  function __abcMissing() {
    var out = [];
    for (var i = 0; i < __abcNeed.length; i++) {
      try {
        if (!__abcNeed[i].test()) out.push(__abcNeed[i]);
      } catch (e) {
        out.push(__abcNeed[i]);
      }
    }
    return out;
  }
  function __abcLoadScript(url, timeout) {
    return new Promise(function (resolve) {
      var done = false;
      var timer = setTimeout(function () {
        if (!done) {
          done = true;
          resolve(false);
        }
      }, timeout || 8000);
      function finish(ok) {
        if (done) return;
        done = true;
        clearTimeout(timer);
        resolve(ok);
      }
      try {
        var script = document.createElement("script");
        script.src = url;
        script.onload = function () { finish(true); };
        script.onerror = function () { finish(false); };
        (document.head || document.documentElement).appendChild(script);
      } catch (e) {
        finish(false);
      }
    });
  }
  function __abcBanner(lines) {
    try {
      if (document.getElementById("__abcDepBanner")) return;
      var box = document.createElement("div");
      box.id = "__abcDepBanner";
      box.style.cssText = "position:fixed;left:12px;top:12px;z-index:2147483647;max-width:440px;padding:12px 14px;border-radius:10px;background:#1f2430;color:#f5f6f8;font:13px/1.7 -apple-system,'Microsoft YaHei',sans-serif;box-shadow:0 8px 24px rgba(0,0,0,.35);";
      box.innerHTML = lines.join("");
      var close = document.createElement("button");
      close.textContent = "知道了";
      close.style.cssText = "margin-top:8px;padding:4px 12px;border:0;border-radius:6px;background:#3b82f6;color:#fff;cursor:pointer;font-size:12px;";
      close.onclick = function () { box.remove(); };
      box.appendChild(close);
      (document.body || document.documentElement).appendChild(box);
    } catch (e) {}
  }
  function __abcStart() {
    var missing = __abcMissing();
    if (!missing.length) {
      try {
        __abcBoot();
      } catch (error) {
        __abcBanner(["<b>🐮 自接DeepSeek版启动失败</b><br>", "错误：" + String((error && error.message) || error)]);
      }
      return;
    }
    var chains = missing.map(function (lib) {
      var idx = 0;
      function attempt() {
        if (idx >= lib.urls.length) return Promise.resolve(false);
        var url = lib.urls[idx++];
        return __abcLoadScript(url, 6000).then(function (ok) {
          if (ok && lib.test()) return true;
          return attempt();
        });
      }
      return attempt();
    });
    Promise.all(chains).then(function () {
      var still = __abcMissing();
      if (!still.length) {
        __abcBoot();
        return;
      }
      var names = still.map(function (item) { return item.name; }).join("、");
      __abcBanner([
        "<b>🐮 自接DeepSeek版：面板没出来</b><br>",
        "原因：脚本依赖的基础库没加载成功（缺少 <b>" + names + "</b>）<br>",
        "本站点：" + String(location.hostname || "") + "<br>",
        "按顺序试这几条：<br>",
        "1. 校园网/代理拦了 CDN → 换手机热点或别的网络，再刷新；<br>",
        "2. 浏览器装了广告拦截/隐私类插件 → 对本页临时关闭，再刷新；<br>",
        "3. Tampermonkey 里本脚本的「设置 → 用户包括/站点权限」改成始终允许；<br>",
        "4. Chromium 系浏览器要在扩展管理页打开「开发者模式」；<br>",
        "5. 都不行就把这个提示截图发我，我按你的网络换 CDN。"
      ]);
    });
  }
  function __abcBoot() {
