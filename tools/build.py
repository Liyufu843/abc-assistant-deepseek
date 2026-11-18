# -*- coding: utf-8 -*-
"""把「🐮ABC超星学习通｜智慧树网课助手 4.8.3」的三处付费接口替换成自接大模型，并精简界面。

用法：
    python tools/build.py            # 读取 upstream/original-4.8.3.txt
    ABC_UPSTREAM=/path/to/x.txt python tools/build.py

产出：dist/ABC-assistant-DeepSeek-v<VERSION>.user.js
本文件是本项目唯一的“改造真相源”：每处替换都用 rep() 断言命中且唯一。
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSION = "1.3.0"
SRC_CANDIDATES = [
    os.environ.get("ABC_UPSTREAM", ""),
    os.path.join(ROOT, "upstream", "original-4.8.3.txt"),
    os.path.join(ROOT, "upstream", "原版源脚本-4.8.3.txt"),
]
SRC = next((p for p in SRC_CANDIDATES if os.path.exists(p)), SRC_CANDIDATES[0])
OUT = os.path.join(ROOT, "dist", "ABC-assistant-DeepSeek-v%s.user.js" % VERSION)

with io.open(SRC, "r", encoding="utf-8") as f:
    src = f.read()

edits = []


def rep(old, new, label):
    global src
    n = src.count(old)
    if n != 1:
        raise SystemExit("[FAIL] %s：期望命中 1 次，实际 %d 次\n---\n%s" % (label, n, old[:200]))
    src = src.replace(old, new, 1)
    edits.append(label)


# ---------------------------------------------------------------- 1. 元数据
rep(
    "// @connect      chaoxing.com\n",
    "// @connect      chaoxing.com\n"
    "// @connect      open.bigmodel.cn\n"
    "// @connect      api.siliconflow.cn\n"
    "// @connect      dashscope.aliyuncs.com\n"
    "// @connect      generativelanguage.googleapis.com\n"
    "// @connect      api.deepseek.com\n"
    "// @connect      127.0.0.1\n"
    "// @connect      localhost\n",
    "header: @connect",
)

rep(
    "// @antifeature  payment  使用第三方题库需付费\n",
    "",
    "header: 移除 antifeature payment",
)


def rep_regex(pattern, new, label, flags=0):
    global src
    out, n = re.subn(pattern, new, src, count=1, flags=flags)
    if n != 1:
        raise SystemExit("[FAIL] %s：正则未命中" % label)
    src = out
    edits.append(label)


rep_regex(r"^// @version\s+4\.8\.3\s*$", "// @version      1.3.0", "header: version", re.M)
rep_regex(r"^// @name[^\n]*$", "// @name         🐮ABC学习通｜智慧树助手·自接DeepSeek版", "header: name", re.M)
rep_regex(r"^// @namespace[^\n]*$", "// @namespace    dsh.abc.deepseek", "header: namespace", re.M)
rep_regex(r"^// @description\s+", "// @description  【自接大模型版·无需付费密钥·基于原版 4.8.3 改造】", "header: description", re.M)
rep_regex(r"^// @antifeature.*$", "", "noop", re.M) if False else None

# ---------------------------------------------------------------- 2. 设置项
SETTINGS_OLD = """          basicConfig: {
            token: {
              text: "密钥","""
SETTINGS_NEW = """          basicConfig: {
            aiEnabled: {
              text: "启用自接大模型",
              value: true,
              type: "switch",
              tips: "开启后搜题/答题全部走你自己的免费大模型，不再需要付费密钥；关闭则恢复原来的密钥通道"
            },
            aiProvider: {
              text: "AI 引擎",
              value: "deepseek",
              type: "select",
              tips: "答题引擎。默认 DeepSeek（deepseek-chat）：答题准确率第一梯队、响应快、每道题成本约 0.001 元；其他免费引擎已内置，可随时切换",
              options: [
                { value: "deepseek", label: "DeepSeek 官方（推荐）" },
                { value: "zhipu", label: "智谱 GLM-4.5-Flash（免费备用）" },
                { value: "siliconflow", label: "硅基流动 Qwen3-8B" },
                { value: "dashscope", label: "阿里百炼 qwen-flash" },
                { value: "gemini", label: "Gemini Flash" },
                { value: "ollama", label: "本地 Ollama" },
                { value: "custom", label: "自定义 OpenAI 兼容" }
              ]
            },
            aiApiKey: {
              text: "AI 密钥",
              value: "",
              type: "input",
              tips: "DeepSeek 的 Key 在 platform.deepseek.com 创建（按量付费，充 10 元能用很久）；换免费引擎时填对应平台的 Key。只保存在你本地浏览器",
              placeholder: "粘贴你自己的 API Key"
            },
            aiModelName: {
              text: "模型名",
              value: "",
              type: "input",
              tips: "留空用所选引擎的默认模型；填了则优先用你填的（失败时会自动回退到默认模型）",
              placeholder: "如 deepseek-chat"
            },
            aiBaseUrl: {
              text: "自定义接口",
              value: "",
              type: "input",
              tips: "仅“自定义 OpenAI 兼容”时需要，填到 /v1 为止；本地 Ollama 默认 http://127.0.0.1:11434/v1",
              placeholder: "https://xxx/v1"
            },
            aiAccuracyMode: {
              text: "答题精度模式",
              value: "standard",
              type: "select",
              tips: "标准：让模型先简短分析再给答案，正确率明显高于极速；高准确：同一题独立作答 3 次投票，最准但每题慢 2~3 秒",
              options: [
                { value: "fast", label: "极速（最快，准确率最低）" },
                { value: "standard", label: "标准（推荐）" },
                { value: "high", label: "高准确（多次投票）" }
              ]
            },
            aiExamBoost: {
              text: "考试模式强化",
              value: true,
              type: "switch",
              tips: "识别到考试页时自动切「高准确 + 最强模型」，正确率更高但每题慢 3~10 秒；平时作业、刷课不受影响"
            },
            aiMaxRetry: {
              text: "AI 重试次数",
              value: 1,
              type: "input-number",
              min: 0,
              max: 4,
              tips: "单题请求失败后的重试次数。调大更稳但更慢；免费接口偶发限流时才建议加"
            },
            aiTimeout: {
              text: "AI 超时(秒)",
              value: 12,
              type: "input-number",
              min: 8,
              max: 60,
              tips: "单次模型请求的超时时间，默认 15 秒；整体还有 45 秒预算，超了就换模型/直接报错"
            },
            aiDebug: {
              text: "AI 调试日志",
              value: false,
              type: "switch",
              tips: "开启后每次请求的模型/耗时/错误都会打印到浏览器控制台（F12），排查卡住时用"
            },
            token: {
              text: "密钥","""
rep(SETTINGS_OLD, SETTINGS_NEW, "settings: 新增本地AI配置项")

# ---------------------------------------------------------------- 3. 引擎模块
ENGINE = r'''  // ==================== 自接大模型引擎（DeepSeek 改版注入） ====================
  const __ABC_AI_PRESETS = {
    deepseek: { label: "DeepSeek", base: "https://api.deepseek.com/v1", models: ["deepseek-chat"] },
    zhipu: { label: "智谱 GLM", base: "https://open.bigmodel.cn/api/paas/v4", models: ["glm-4.5-flash", "glm-4-flash-250414", "glm-4-flash"] },
    zhipuAir: { label: "智谱 GLM-4-Flash", base: "https://open.bigmodel.cn/api/paas/v4", models: ["glm-4-flash-250414", "glm-4-flash", "glm-4.5-flash"] },
    siliconflow: { label: "硅基流动", base: "https://api.siliconflow.cn/v1", models: ["Qwen/Qwen3-8B", "Qwen/Qwen2.5-7B-Instruct", "THUDM/GLM-4-9B-0414"] },
    dashscope: { label: "阿里百炼", base: "https://dashscope.aliyuncs.com/compatible-mode/v1", models: ["qwen-flash", "qwen-turbo"] },
    gemini: { label: "Gemini", base: "https://generativelanguage.googleapis.com/v1beta/openai", models: ["gemini-2.5-flash", "gemini-2.0-flash"] },
    ollama: { label: "本地 Ollama", base: "http://127.0.0.1:11434/v1", models: ["qwen2.5:7b", "glm4:9b", "qwen3:8b"] },
    custom: { label: "自定义接口", base: "", models: [] }
  };
  const __ABC_AI_CACHE = new Map();
  const __ABC_AI_CACHE_KEY = "__abcAI_answer_cache_v1";
  let __abcAICacheRestored = false;
  function __abcAICacheRestore() {
    if (__abcAICacheRestored) return;
    __abcAICacheRestored = true;
    try {
      const raw = window.localStorage.getItem(__ABC_AI_CACHE_KEY);
      if (!raw) return;
      const saved = JSON.parse(raw);
      if (!saved || typeof saved !== "object") return;
      for (const key of Object.keys(saved)) {
        if (__ABC_AI_CACHE.size >= __ABC_AI_CACHE_MAX) break;
        const item = saved[key];
        if (item && item.code === 1) __ABC_AI_CACHE.set(key, item);
      }
    } catch (e) {}
  }
  function __abcAICachePersist() {
    try {
      const out = {};
      let count = 0;
      __ABC_AI_CACHE.forEach((value, key) => {
        if (count >= 300) return;
        out[key] = value;
        count += 1;
      });
      window.localStorage.setItem(__ABC_AI_CACHE_KEY, JSON.stringify(out));
    } catch (e) {}
  }
  const __ABC_AI_CACHE_MAX = 500;
  const __ABC_AI_BUDGET = 30e3;
  const __ABC_AI_BREAK_MS = 45e3;
  const __ABC_AI_MAX_ATTEMPTS = 3;
  const __ABC_AI_CONCURRENCY = 6;
  const __ABC_AI_PREFETCH_MAX = 24;
  let __ABC_AI_ACTIVE = 0;
  const __ABC_AI_QUEUE = [];
  let __ABC_AI_BREAKER = { until: 0, message: "" };
  const __ABC_AI_TYPE_NAMES = { "0": "单选题", "1": "多选题", "2": "填空题", "3": "判断题", "4": "简答题", "5": "论述题", "6": "名词解释" };
  const __ABC_AI_TYPE_CODES = {
    "单选题": "0", "单选": "0",
    "多选题": "1", "多选": "1", "不定项选择题": "1",
    "填空题": "2", "填空": "2",
    "判断题": "3", "判断": "3", "是非题": "3", "是非": "3",
    "简答题": "4", "简答": "4", "计算题": "4", "其他": "4", "问答题": "4",
    "论述题": "5", "论述": "5",
    "名词解释": "6", "名词解释题": "6"
  };
  function __abcKind(question) {
    const raw = String(question && question.type == null ? "" : question.type).trim();
    if (/判断|是非/.test(raw)) return "3";
    if (/多选|多项|不定项/.test(raw)) return "1";
    if (/单选|单项/.test(raw)) return "0";
    if (/名词解释|名词/.test(raw)) return "6";
    if (/论述/.test(raw)) return "5";
    if (/填空/.test(raw)) return "2";
    if (/简答|问答|计算|分析|案例/.test(raw)) return "4";
    return __abcTypeCode(raw);
  }
  function __abcOptionList(question) {
    const direct = Array.isArray(question && question.optionsText) ? question.optionsText.filter(Boolean).map((item) => String(item).trim()) : [];
    if (direct.length) return direct;
    try {
      const els = question && question.optionEls;
      if (els && els.length) {
        const out = Array.prototype.map.call(els, (el) => String(el.textContent || "").trim()).filter(Boolean);
        if (out.length) return out;
      }
    } catch (e) {}
    try {
      const root = question && question.element;
      if (root && root.querySelectorAll) {
        const nodes = root.querySelectorAll("[role='radio'], [role='checkbox'], .optionUl label, .radio-view li, label");
        const out = Array.prototype.map.call(nodes, (el) => String(el.textContent || "").trim()).filter(Boolean);
        if (out.length) return out;
      }
    } catch (e) {}
    return [];
  }
  function __abcIsFillableType(type) {
    return /填空|简答|问答|名词解释|论述|计算|分析|案例/.test(String(type || ""));
  }
  function __abcLettersToText(answer, optionList) {
    const out = [];
    for (const item of answer) {
      const raw = String(item == null ? "" : item).trim();
      if (/^[A-H]{1,8}$/i.test(raw)) {
        for (const ch of raw.toUpperCase()) {
          const text = optionList[ch.charCodeAt(0) - 65];
          if (!text) return null;
          out.push(String(text).trim());
        }
      } else {
        out.push(raw);
      }
    }
    return out;
  }
  function __abcTypeCode(type) {
    const raw = type == null ? "" : String(type).trim();
    if (/^[0-9]+$/.test(raw)) return raw;
    return __ABC_AI_TYPE_CODES[raw] || "";
  }
  function __abcAISetting(key, fallback) {
    try {
      const item = useSettingStore().config.basicConfig[key];
      const value = item && typeof item === "object" ? item.value : item;
      if (value === void 0 || value === null || value === "") return fallback;
      return value;
    } catch (e) {
      return fallback;
    }
  }
  function __abcAIConfig() {
    const provider = String(__abcAISetting("aiProvider", "deepseek"));
    const preset = __ABC_AI_PRESETS[provider] || __ABC_AI_PRESETS.deepseek;
    const base = String(__abcAISetting("aiBaseUrl", "") || preset.base || "").replace(/\/+$/, "");
    const fixedModel = String(__abcAISetting("aiModelName", "")).trim();
    const models = fixedModel ? [fixedModel].concat(preset.models.filter((m) => m !== fixedModel)) : preset.models.slice();
    const retry = Math.max(0, Math.min(5, Number(__abcAISetting("aiMaxRetry", 2)) || 0));
    const timeoutSec = Math.max(8, Math.min(120, Number(__abcAISetting("aiTimeout", 35)) || 35));
    return {
      enabled: __abcAISetting("aiEnabled", true) !== false,
      provider,
      label: preset.label,
      key: String(__abcAISetting("aiApiKey", "")).trim(),
      base,
      models,
      retry,
      timeout: timeoutSec * 1e3
    };
  }
  function __abcAIDebug() {
    try {
      if (__abcAISetting("aiDebug", false) !== true) return;
      const args = Array.prototype.slice.call(arguments);
      console.info.apply(console, ["[自接AI]"].concat(args));
    } catch (e) {}
  }
  let __abcAILogHook = null;
  function __abcAILogPush(message, level) {
    const text = String(message == null ? "" : message);
    try {
      if (typeof __abcAILogHook === "function") {
        __abcAILogHook(text, level || "info");
        return;
      }
    } catch (e) {}
    try {
      if (typeof messageStore !== "undefined" && messageStore && messageStore.insertMessage) {
        messageStore.insertMessage(text, level === "warning" ? "warning" : "info");
      }
    } catch (e) {}
  }
  function __abcAIEnsureUsable(cfg) {
    if (cfg.key && /deepseek/i.test(cfg.base) && !/^sk-[0-9a-z]{20,}$/i.test(cfg.key)) {
      __abcAILogPush("AI 密钥格式不太对（DeepSeek 的 Key 形如 sk-xxxxxxxx），如果一直失败请重新复制一次", "warning");
    }
    if (!cfg.base) {
      const error = new Error("未配置 AI 接口地址，请到“设置 → 自定义接口”填写");
      error.fatal = true;
      throw error;
    }
    if (cfg.provider !== "ollama" && cfg.provider !== "custom" && !cfg.key) {
      const error = new Error("未填写 AI 密钥，请到“设置 → AI 密钥”粘贴你在 " + cfg.label + " 申请的 Key");
      error.fatal = true;
      throw error;
    }
    if (!cfg.models.length) {
      const error = new Error("未配置模型名，请到“设置 → 模型名”填写，或把“AI 引擎”换成内置引擎");
      error.fatal = true;
      throw error;
    }
  }
  function __abcLocalAIActive() {
    try {
      const cfg = __abcAIConfig();
      return Boolean(cfg.enabled && cfg.base);
    } catch (e) {
      return false;
    }
  }
  function __abcAIPost(url2, headers, body, timeout) {
    return new Promise((resolve, reject) => {
      GM_xmlhttpRequest({
        url: url2,
        method: "POST",
        headers,
        data: JSON.stringify(body),
        timeout,
        onload: (response) => {
          let json = null;
          try {
            json = JSON.parse(response.responseText);
          } catch (e) {}
          if (response.status >= 200 && response.status < 300 && json) return resolve(json);
          let detail = "";
          if (json && json.error) detail = typeof json.error === "string" ? json.error : json.error.message || JSON.stringify(json.error);
          else if (json && json.message) detail = String(json.message);
          else detail = String(response.responseText || "").slice(0, 200);
          const err = new Error("HTTP " + response.status + " " + detail);
          err.status = response.status;
          reject(err);
        },
        onerror: () => reject(new Error("网络错误，无法连接 " + url2)),
        ontimeout: () => reject(new Error("请求超时 " + url2))
      });
    });
  }
  async function __abcAIChatCompletions(messages, opts) {
    const options = opts || {};
    const cfg = __abcAIConfig();
    __abcAIEnsureUsable(cfg);
    const now = Date.now();
    if (__ABC_AI_BREAKER.until > now) {
      throw new Error("AI 接口刚刚连续失败，已暂停 " + Math.ceil((__ABC_AI_BREAKER.until - now) / 1e3) + " 秒：" + __ABC_AI_BREAKER.message);
    }
    const explicitModel = String(__abcAISetting("aiModelName", "") || "").trim();
    const preferred = __abcExamBoostActive() ? ["deepseek-reasoner"].concat(cfg.models) : cfg.models;
    const models = (options.models || preferred).filter((name) => {
      if (!name) return false;
      if (explicitModel && name === explicitModel) return true;
      if (__abcExamBoostActive()) return true;
      return !/reasoner|thinking|-r1$/i.test(name);
    }).slice(0, 2);
    const headers = { "Content-Type": "application/json" };
    if (cfg.key) headers.Authorization = "Bearer " + cfg.key;
    const startedAt = Date.now();
    const tried = [];
    let lastError = null;
    let attempts = 0;
    let aborted = false;
    loops: for (const model of models) {
      for (let attempt = 0; attempt <= cfg.retry; attempt++) {
        if (attempts >= __ABC_AI_MAX_ATTEMPTS) break loops;
        if (Date.now() - startedAt > __ABC_AI_BUDGET) {
          aborted = true;
          break loops;
        }
        attempts += 1;
        const attemptStarted = Date.now();
        __abcAILogPush("AI 请求 " + model + "（第 " + attempts + "/" + __ABC_AI_MAX_ATTEMPTS + " 次）");
        try {
          const data = await __abcAIPost(cfg.base + "/chat/completions", headers, {
            model,
            messages,
            temperature: options.temperature == null ? 0.2 : options.temperature,
            max_tokens: options.maxTokens || 900,
            stream: false
          }, cfg.timeout);
          const choice = data && data.choices && data.choices[0];
          const content = choice && choice.message ? String(choice.message.content || "") : "";
          if (!content.trim()) throw new Error("模型返回空内容");
          __abcAIDebug("ok", model, (Date.now() - attemptStarted) + "ms", "第" + attempts + "次");
          return { content: content.trim(), model, raw: data };
        } catch (err) {
          lastError = err;
          tried.push(model + "：" + (err && err.message || err));
          __abcAIDebug("fail", model, (Date.now() - attemptStarted) + "ms", String(err && err.message || err));
          const status = err && err.status;
          if (status === 401 || status === 403) break;
          if (status === 400 && /model|模型|不存在|not found|invalid|unsupported/i.test(String(err && err.message || ""))) break;
          if (attempt < cfg.retry) await sleep(1e3 * (attempt + 1));
        }
      }
    }
    const usedMs = Date.now() - startedAt;
    const error = new Error((aborted ? "AI 响应超时（已等 " + Math.round(usedMs / 1e3) + "s）" : "AI 请求失败") + "：" + (tried.slice(-2).join(" ｜ ") || "未发出请求"));
    error.cause = lastError;
    const status = lastError && lastError.status;
    if (aborted || !status || status === 429 || status >= 500) {
      __ABC_AI_BREAKER = { until: Date.now() + __ABC_AI_BREAK_MS, message: error.message };
      __abcAILogPush("AI 连续失败，已暂停 " + Math.round(__ABC_AI_BREAK_MS / 1e3) + " 秒：" + error.message, "warning");
    }
    __abcAIDebug("all-fail", usedMs + "ms", error.message);
    throw error;
  }
  function __abcIsExamPage() {
    try {
      const href = String(location && location.href || "");
      if (!/\/exam|exam-ans|reVersionTestStartNew|\/test\//i.test(href)) return false;
      return Boolean(document && (document.querySelector(".questionLi") || document.querySelector(".TiMu")));
    } catch (e) {
      return false;
    }
  }
  function __abcExamBoostActive() {
    try {
      return __abcAISetting("aiExamBoost", true) === true && __abcIsExamPage();
    } catch (e) {
      return false;
    }
  }
  function __abcRetryFillWithText(question, fill) {
    try {
      const answers = question && question.answer && question.answer.answer;
      const optionsText = Array.isArray(question && question.optionsText) ? question.optionsText : [];
      if (!Array.isArray(answers) || !answers.length || !optionsText.length) return false;
      const texts = [];
      for (const item of answers) {
        const letters = String(item || "").toUpperCase().match(/[A-H]/g) || [];
        if (!letters.length) return false;
        for (const letter of letters) {
          const text = optionsText[letter.charCodeAt(0) - 65];
          if (!text) return false;
          texts.push(String(text));
        }
      }
      if (!texts.length) return false;
      const backup = question.answer.answer;
      question.answer.answer = texts;
      const ok = Boolean(fill(question));
      if (!ok) question.answer.answer = backup;
      __abcAILogPush("字母没勾上，改用选项原文重试：" + (ok ? "成功" : "仍失败"), ok ? "info" : "warning");
      return ok;
    } catch (e) {
      return false;
    }
  }
  function __abcAccuracyMode() {
    const mode = String(__abcAISetting("aiAccuracyMode", "standard") || "standard");
    const normalized = mode === "fast" || mode === "high" ? mode : "standard";
    if (normalized !== "fast" && __abcExamBoostActive()) return "high";
    return normalized;
  }
  function __abcExtractAnswerText(content) {
    const text = String(content || "");
    const hits = text.match(/答\s*案\s*[:：][^\n]*/g);
    if (hits && hits.length) return hits[hits.length - 1].replace(/^答\s*案\s*[:：]/, "").trim();
    return text.replace(/分\s*析\s*[:：][^\n]*/g, "").trim();
  }
  function __abcBuildQuestionMessages(question) {
    const accuracy = __abcAccuracyMode();
    const type = __abcKind(question);
    const typeName = __ABC_AI_TYPE_NAMES[type] || String(question && question.type || "题目");
    const options = __abcOptionList(question);
    const optionLines = options.map((text, index) => String.fromCharCode(65 + index) + ". " + text).join("\n");
    const rules = {
      "0": "这是单选题，答案是唯一的一个选项字母（A-H）。",
      "1": "这是多选题，答案是若干正确选项的字母，连写（例如 ABD）。",
      "3": "这是判断题，答案是「正确」或「错误」。",
      "2": "这是填空题，按空的顺序给答案，多个空之间用 === 分隔。",
      "4": "这是简答题，给出简洁规范的答案要点，不超过 180 字。",
      "5": "这是论述题，给出条理清晰的论述要点，不超过 220 字。",
      "6": "这是名词解释，用一个完整短句解释该名词，不超过 120 字。"
    };
    const caution = {
      "0": "先逐项排除，排除理由要落到选项文字上，不要凭印象。",
      "1": "多选题全选对才得分：只选你能说出依据的选项，完全没把握的宁可不选，不要凑数。",
      "3": "判断题：含「都、一定、必须、只有、全部、唯一」等绝对化表述的通常是错误；含「可能、一般、通常、部分」的通常正确；但若题干是教材原句则按原句判。",
      "2": "填空题必须写教材里的标准术语或公式，不要写解释性句子。"
    }[type] || "";
    const outFormat = accuracy === "fast"
      ? "只输出答案本身，不要任何解释、标点或多余文字。"
      : "先写一行「分析：」说明依据（不超过 40 字），再另起一行写「答案：」，其后只写答案本身，不要再写任何文字。";
    const rule = (rules[type] || "给出正确答案。") + " " + outFormat;
    const userContent = [
      "题型：" + typeName,
      "题目：" + String(question && question.title || ""),
      optionLines ? "选项：\n" + optionLines : "",
      rule,
      caution,
      "如果题目信息不足，请依据该课程最常见教材的表述给出最可能的答案，格式保持不变。"
    ].filter(Boolean).join("\n");
    const system = accuracy === "fast"
      ? "你是一名严谨的中国高校课程答题助手，擅长超星学习通、智慧树的客观题与主观题。只输出答案本身，不解释、不复述题目。"
      : "你是一名严谨的中国高校课程答题助手，擅长超星学习通、智慧树的客观题与主观题。你会先简短说明依据再给答案，依据必须落在题干或选项文字上，不臆造。";
    return [
      { role: "system", content: system },
      { role: "user", content: userContent }
    ];
  }
  function __abcNormalizeAnswers(type, content, optionsText) {
    const raw = String(__abcExtractAnswerText(content) || "").trim().replace(/^[`"'“”‘’\s]+/, "").replace(/[`"'“”‘’\s]+$/, "").trim();
    if (!raw) return [];
    if (type === "3") {
      if (/错误|不对|不正确|错误项|×|✗|false|no\b/i.test(raw)) return ["错误"];
      if (/正确|√|✓|true|yes\b/i.test(raw)) return ["正确"];
      return [/错/.test(raw) ? "错误" : "正确"];
    }
    if (type === "0" || type === "1") {
      const letters = [];
      const seen = {};
      const upper = raw.toUpperCase();
      for (const ch of upper) {
        if (ch >= "A" && ch <= "H" && !seen[ch]) {
          seen[ch] = true;
          letters.push(ch);
        }
      }
      if (letters.length) {
        if (type === "0") return [letters[0]];
        return [letters.join("")];
      }
      return [raw];
    }
    if (type === "2") {
      const parts = raw.split(/===+#?|#|；|;|\r?\n/).map((item) => item.trim()).filter(Boolean);
      return parts.length ? parts : [raw];
    }
    return [raw];
  }
  function __abcAIPickMaxTokens(type) {
    const accuracy = __abcAccuracyMode();
    const objective = type === "0" || type === "1" || type === "3";
    if (accuracy === "fast") {
      if (objective) return 32;
      if (type === "2") return 220;
      return 420;
    }
    if (objective) return 200;
    if (type === "2") return 320;
    return 560;
  }
  function __abcAIPumpQueue() {
    while (__ABC_AI_ACTIVE < __ABC_AI_CONCURRENCY && __ABC_AI_QUEUE.length) {
      const job = __ABC_AI_QUEUE.shift();
      __ABC_AI_ACTIVE += 1;
      Promise.resolve()
        .then(job.task)
        .then((value) => job.resolve(value), (err) => job.reject(err))
        .then(() => {
          __ABC_AI_ACTIVE -= 1;
          __abcAIPumpQueue();
        });
    }
  }
  function __abcAILimit(task, priority) {
    return new Promise((resolve, reject) => {
      const job = { task, resolve, reject };
      if (priority) __ABC_AI_QUEUE.unshift(job);
      else __ABC_AI_QUEUE.push(job);
      __abcAIPumpQueue();
    });
  }
  async function __abcAskOnce(question, type, optionsText, temperature) {
    const result = await __abcAIChatCompletions(__abcBuildQuestionMessages(question), {
      maxTokens: __abcAIPickMaxTokens(type),
      temperature
    });
    const answer = __abcNormalizeAnswers(type, result.content, optionsText);
    if (!answer.length) throw new Error("模型未给出可用答案");
    return answer;
  }
  async function __abcCollectAnswer(question, type, optionsText) {
    const accuracy = __abcAccuracyMode();
    if (accuracy === "fast") return await __abcAskOnce(question, type, optionsText, 0.1);
    const temperatures = accuracy === "high" ? [0.1, 0.55, 0.85] : [0.2];
    const samples = [];
    for (const temperature of temperatures) {
      try {
        samples.push(await __abcAskOnce(question, type, optionsText, temperature));
      } catch (error) {
        if (!samples.length) throw error;
      }
      if (samples.length >= 2 && JSON.stringify(samples[0]) === JSON.stringify(samples[1])) break;
    }
    if (samples.length === 1) return samples[0];
    const tally = new Map();
    for (const sample of samples) {
      const key = JSON.stringify(sample);
      const entry = tally.get(key) || { sample, count: 0 };
      entry.count += 1;
      tally.set(key, entry);
    }
    let best = samples[0];
    let bestCount = 0;
    tally.forEach((entry) => {
      if (entry.count > bestCount) {
        best = entry.sample;
        bestCount = entry.count;
      } else if (entry.count === bestCount && type === "1" && entry.sample.length < best.length) {
        best = entry.sample;
      }
    });
    if (samples.length > 1) {
      __abcAILogPush("AI 独立作答 " + samples.map((sample) => sample.join("")).join(" / ") + " → 取 " + best.join(""));
    }
    return best;
  }
  async function __abcAIAnswerRaw(question) {
    const type = __abcKind(question);
    const title = String(question && question.title || "").trim();
    const optionsText = __abcOptionList(question);
    const cacheKey = __abcAIQuestionKey(question);
    try {
      __abcAIDebug("ask", type, title.slice(0, 30));
      let answer = await __abcCollectAnswer(question, type, optionsText);
      if (question && question.optionEls && question.optionEls.length && optionsText.length) {
        const asText = __abcLettersToText(answer, optionsText);
        if (asText && asText.length) answer = asText;
      }
      __abcAILogPush("AI 作答：" + answer.join(" ") + "（" + __ABC_AI_TYPE_NAMES[type] + "）");
      const payload = { code: 1, data: { answer, remainCount: "自接AI", num: "", usenum: "" }, msg: "" };
      if (__ABC_AI_CACHE.size > __ABC_AI_CACHE_MAX) __ABC_AI_CACHE.clear();
      __ABC_AI_CACHE.set(cacheKey, payload);
      __abcAICachePersist();
      __abcAIDebug("answer", JSON.stringify(answer));
      return payload;
    } catch (error) {
      __abcAIDebug("error", String(error && error.message || error));
      __abcAILogPush("AI 作答失败：" + String(error && error.message || error), "warning");
      return { code: -1, data: { answer: ["AI答题失败：" + (error && error.message || error)], remainCount: "自接AI" }, msg: String(error && error.message || error) };
    }
  }
  function __abcAIQuestionKey(question) {
    const type = __abcKind(question);
    const flow = question && question.optionEls && question.optionEls.length ? "dom" : "kv";
    return flow + "::" + type + "::" + String(question && question.title || "").trim() + "::" + __abcOptionList(question).join("|");
  }
  let __abcAILastPrefetch = { key: "", at: 0 };
  let __abcADuplicateWarned = false;
  function __abcWarnDuplicates() {
    if (__abcADuplicateWarned) return;
    __abcADuplicateWarned = true;
    try {
      const panels = document.querySelectorAll(".main-wrap").length;
      if (panels > 1) {
        __abcAILogPush("检测到 " + panels + " 个助手面板在同时运行（多半是同时装了原版和自接版），请到 Tampermonkey 里只保留一个，否则会互相抢答题进度", "warning");
      }
    } catch (e) {}
  }
  function __abcAIPrefetch(questions) {
    try {
      if (!__abcLocalAIActive()) return;
      if (!Array.isArray(questions) || questions.length < 2) return;
      __abcWarnDuplicates();
      __abcAIEnsureUsable(__abcAIConfig());
      const jobs = [];
      for (const question of questions) {
        if (!question || !String(question.title || "").trim()) continue;
        if (__ABC_AI_CACHE.has(__abcAIQuestionKey(question))) continue;
        jobs.push(question);
        if (jobs.length >= __ABC_AI_PREFETCH_MAX) break;
      }
      if (!jobs.length) return;
      const batchKey = jobs.length + "|" + String(jobs[0] && jobs[0].title || "");
      const nowTs = Date.now();
      if (__abcAILastPrefetch.key === batchKey && nowTs - __abcAILastPrefetch.at < 3e4) {
        __abcAIDebug("prefetch-skip", batchKey);
        return;
      }
      __abcAILastPrefetch = { key: batchKey, at: nowTs };
      __abcAIDebug("prefetch", jobs.length + "/" + questions.length);
      __abcAILogPush("AI 已开始并发预取 " + jobs.length + " 道题（并发 " + __ABC_AI_CONCURRENCY + "）");
      jobs.forEach((question) => {
        __abcAILimit(() => __abcAIAnswerRaw(question), false).then(() => {}, () => {});
      });
    } catch (e) {}
  }
  async function __abcAIAnswer(question) {
    const title = String(question && question.title || "").trim();
    if (!title) return { code: -1, data: { answer: ["题目为空，无法作答"], remainCount: "自接AI" }, msg: "题目为空" };
    const cacheKey = __abcAIQuestionKey(question);
    if (__ABC_AI_CACHE.has(cacheKey)) {
      __abcAIDebug("cache-hit", title.slice(0, 20));
      return __ABC_AI_CACHE.get(cacheKey);
    }
    try {
      __abcAIEnsureUsable(__abcAIConfig());
    } catch (error) {
      return { code: -1, data: { answer: ["AI 未配置好：" + (error && error.message || error)], remainCount: "自接AI" }, msg: String(error && error.message || error) };
    }
    return await __abcAILimit(() => __abcAIAnswerRaw(question), true);
  }
  async function __abcAIFuzzy(query) {
    const text = String(query || "").trim();
    if (!text) return { code: 1, data: { items: [] }, msg: "" };
    try {
      const result = await __abcAIChatCompletions([
        {
          role: "system",
          content: "你是课程题库助手。判断用户给出题目的题型并作答，只输出一行紧凑 JSON，不要 markdown 代码块，不要任何解释。"
        },
        {
          role: "user",
          content: "题目：" + text + "\n\n只输出这个 JSON：{\"type\":\"0\",\"options\":[\"选项原文\"],\"answer\":[\"答案\"],\"explain\":\"60字内解析\"}\n" +
            "type 取值：0=单选 1=多选 2=填空 3=判断 4=简答/其他。选择题的 answer 用选项字母或选项原文；判断题 answer 只能是「正确」或「错误」；填空题每个空的答案作为数组的一个元素。"
        }
      ], { maxTokens: 600, temperature: 0.2 });
      let parsed = null;
      const match = String(result.content || "").match(/\{[\s\S]*\}/);
      if (match) {
        try {
          parsed = JSON.parse(match[0]);
        } catch (e) {}
      }
      let item;
      if (parsed) {
        const rawAnswer = Array.isArray(parsed.answer) ? parsed.answer : [parsed.answer];
        item = {
          type: String(parsed.type == null ? "4" : parsed.type),
          title: text,
          options: Array.isArray(parsed.options) ? parsed.options.map((o) => String(o)) : [],
          answer: rawAnswer.map((a) => String(a == null ? "" : a)).filter(Boolean)
        };
      } else {
        item = { type: "4", title: text, options: [], answer: [String(result.content || "").trim()] };
      }
      if (!item.answer.length) item.answer = ["（模型未给出答案）"];
      return { code: 1, data: { items: [item] }, msg: "" };
    } catch (error) {
      return { code: 10003, data: { items: [] }, msg: "AI 搜题失败：" + (error && error.message || error) };
    }
  }
  // ==================== 自接大模型引擎（注入结束） ====================
'''

ACCURATE_OLD = """  const getAccurateAnswer = async (question) => {
    var _a;"""
ACCURATE_NEW = """  const getAccurateAnswer = async (question) => {
    if (__abcLocalAIActive()) {
      return { code: -1004, data: { answer: [], num: "", usenum: "" }, msg: "自接AI模式：跳过付费题库" };
    }
    var _a;"""
rep(ACCURATE_OLD, ACCURATE_NEW, "patch: getAccurateAnswer 跳过付费题库")

FUZZY_OLD = """  const fetchFuzzySearch = async (question) => {
    const url2 = getApiBaseUrl() + "/question/fuzzySearch";"""
FUZZY_NEW = """  const fetchFuzzySearch = async (question) => {
    if (__abcLocalAIActive()) return await __abcAIFuzzy(question);
    const url2 = getApiBaseUrl() + "/question/fuzzySearch";"""
rep(FUZZY_OLD, FUZZY_NEW, "patch: fetchFuzzySearch 走本地AI")

AI_OLD = """  const getAIAnswer = async (question) => {
    const url2 = getApiBaseUrl() + "/ai/answer";"""
AI_NEW = """  const getAIAnswer = async (question) => {
    if (__abcLocalAIActive()) return await __abcAIAnswer(question);
    const url2 = getApiBaseUrl() + "/ai/answer";"""
rep(AI_OLD, AI_NEW, "patch: getAIAnswer 走本地AI")

ENGINE_OLD = "  const getAccurateAnswer = async (question) => {"
rep(ENGINE_OLD, ENGINE + ENGINE_OLD, "inject: 本地AI引擎模块")

# ---------------------------------------------------------------- 4. 门槛 / 剩余次数
rep(
    """        e.preventDefault();
        if (!setting.config.basicConfig.token.value) {""",
    """        e.preventDefault();
        if (!setting.config.basicConfig.token.value && !__abcLocalAIActive()) {""",
    "gate: 在线搜题",
)

rep(
    """        if (!input.value.trim()) return;
        if (!setting.config.basicConfig.token.value) {""",
    """        if (!input.value.trim()) return;
        if (!setting.config.basicConfig.token.value && !__abcLocalAIActive()) {""",
    "gate: AI 对话",
)

rep(
    """          if (!setting.config.basicConfig.token.value) {
            messageStore.insertMessage(
              "检测到未配置密钥，无法使用自动答题功能，请前往 “设置” 模块配置",""",
    """          if (!setting.config.basicConfig.token.value && !__abcLocalAIActive()) {
            messageStore.insertMessage(
              "检测到未配置密钥，也未配置自接AI，自动答题将无法获取答案，请前往 “设置” 模块配置",""",
    "gate: 自动答题提示",
)

rep(
    """    const token = setting.config.basicConfig.token.value;
    const url2 = getApiBaseUrl() + `/info/remains?token=${token}`;""",
    """    if (__abcLocalAIActive()) {
      return { code: 1, data: { count: 0, usedCount: 0 }, msg: "自接AI" };
    }
    const token = setting.config.basicConfig.token.value;
    const url2 = getApiBaseUrl() + `/info/remains?token=${token}`;""",
    "patch: getTokenInfo 本地模式免请求",
)

rep(
    """      const updateTokenInfo = () => {
        if (setting.config.basicConfig.token.value) {""",
    """      const updateTokenInfo = () => {
        if (__abcLocalAIActive()) {
          setting.userInfo.remainCount = "自接AI";
          return;
        }
        if (setting.config.basicConfig.token.value) {""",
    "patch: updateTokenInfo 显示本地免费",
)

# ---------------------------------------------------------------- 5. AI 对话面板
CHAT_OLD = """        scrollToBottom();
        try {
          const requestData = {
            content: inputValue,"""
CHAT_NEW = """        scrollToBottom();
        if (__abcLocalAIActive()) {
          isLoading.value = true;
          try {
            const history = messages.value.slice(0, -1).filter((item) => item.content && item.content !== THINKING).map((item) => ({
              role: item.role === "user" ? "user" : "assistant",
              content: String(item.content)
            }));
            while (history.length && history[0].role !== "user") history.shift();
            const reply = await __abcAIChatCompletions(history, { maxTokens: 1500, temperature: 0.6 });
            messages.value[messages.value.length - 1].content = reply.content;
          } catch (error) {
            messages.value[messages.value.length - 1].content = "AI 请求失败：" + (error && error.message || error);
          }
          isLoading.value = false;
          scrollToBottom();
          return;
        }
        try {
          const requestData = {
            content: inputValue,"""
rep(CHAT_OLD, CHAT_NEW, "patch: AI 对话面板走本地模型")

# ---------------------------------------------------------------- 6. 在线搜题面板静态提示文案
rep(
    '_cache[5] || (_cache[5] = vue.createTextVNode(" 使用在线搜题前，请先前往 "))',
    '_cache[5] || (_cache[5] = vue.createTextVNode(" 使用在线搜题前，请先在 "))',
    "text: 在线搜题提示（前段）",
)
rep(
    '_cache[4] || (_cache[4] = vue.createTextVNode("配置密钥 "))',
    '_cache[4] || (_cache[4] = vue.createTextVNode("设置中填写模型密钥 "))',
    "text: 在线搜题提示（按钮）",
)
rep(
    '_cache[6] || (_cache[6] = vue.createElementVNode("li", null, "如需手动答题，建议关闭自动切换功能，防止操作冲突", -1))',
    '_cache[6] || (_cache[6] = vue.createElementVNode("li", null, "自接AI模式不限次数，答案来自大模型，请自行核对后再提交", -1))',
    "text: 在线搜题提示（第三行）",
)

# ---------------------------------------------------------------- 7. 纯题库模式下也放行本地AI
rep(
    '              if (mode === "questionBank" || answerData.code !== -1004) {',
    '              if (!__abcLocalAIActive() && (mode === "questionBank" || answerData.code !== -1004)) {',
    "flow: 纯题库模式放行本地AI（超星）",
)
rep(
    '              } else if (mode === "questionBank" || answerData.code !== -1004) {',
    '              } else if (!__abcLocalAIActive() && (mode === "questionBank" || answerData.code !== -1004)) {',
    "flow: 纯题库模式放行本地AI（智慧树）",
)
rep(
    '''          handled = true;
        } else if (mode === "questionBank" || answerData.code !== -1004) {''',
    '''          handled = true;
        } else if (!__abcLocalAIActive() && (mode === "questionBank" || answerData.code !== -1004)) {''',
    "flow: 纯题库模式放行本地AI（第三处）",
)

# ---------------------------------------------------------------- 8. 开答前预取（并发提前取答案）
rep(
    '''          const mode = answerMode.value;
          for (const [index, question] of this.questions.entries()) {
            this.questionStore.currentQuestionIndex = index;
            if (mode !== "ai") {''',
    '''          const mode = answerMode.value;
          __abcAILogHook = (msg, level) => {
            try {
              this.log.insertLog(msg, level === "warning" ? "warning" : "info");
            } catch (e) {}
          };
          __abcAICacheRestore();
          __abcAIPrefetch(this.questions);
          for (const [index, question] of this.questions.entries()) {
            this.questionStore.currentQuestionIndex = index;
            if (mode !== "ai") {''',
    "speed: 超星开答前预取",
)
rep(
    '''          const mode = answerMode.value;
          for (const [index, question] of this.questions.entries()) {
            this.questionStore.currentQuestionIndex = index;
            let fillFailed = false;''',
    '''          const mode = answerMode.value;
          __abcAILogHook = (msg, level) => {
            try {
              this.log.insertLog(msg, level === "warning" ? "warning" : "info");
            } catch (e) {}
          };
          __abcAICacheRestore();
          __abcAIPrefetch(this.questions);
          for (const [index, question] of this.questions.entries()) {
            this.questionStore.currentQuestionIndex = index;
            let fillFailed = false;''',
    "speed: 智慧树开答前预取",
)

# ---------------------------------------------------------------- 10. 考试答题兜底（字母没勾上就改用选项原文）
FILL_CX_OLD = '''                  source: "ai"
                });
                const fillSuccess = this.fillQuestion(question);
                if (!fillSuccess) {
                  question.answer.code = 0;
                  continue;
                }'''
FILL_CX_NEW = '''                  source: "ai"
                });
                let fillSuccess = this.fillQuestion(question);
                if (!fillSuccess) fillSuccess = __abcRetryFillWithText(question, (item) => this.fillQuestion(item));
                if (!fillSuccess) {
                  question.answer.code = 0;
                  continue;
                }'''
rep(FILL_CX_OLD, FILL_CX_NEW, "exam: 超星字母填充失败改用原文重试")

FILL_ZHS_OLD = '''                  source: "ai"
                  });
                  const errorStatus = !this.fillQuestion(question, index);'''
FILL_ZHS_NEW = '''                  source: "ai"
                  });
                  let errorStatus = !this.fillQuestion(question, index);
                  if (errorStatus) errorStatus = !__abcRetryFillWithText(question, (item) => this.fillQuestion(item, index));'''
rep(FILL_ZHS_OLD, FILL_ZHS_NEW, "exam: 智慧树字母填充失败改用原文重试")

EXAM_GATE_OLD = "        if (isChoiceType(question.type)) {\n          const aiAnswerData = await getAIAnswer(apiQuestion);"
EXAM_GATE_NEW = "        if (isChoiceType(question.type) || __abcIsFillableType(question.type)) {\n          const aiAnswerData = await getAIAnswer(apiQuestion);"
rep(EXAM_GATE_OLD, EXAM_GATE_NEW, "exam: 填空/简答也交给 AI 作答")

# ---------------------------------------------------------------- 8.5 界面精简（删掉原作者的 AI 对话面板与刷课队列页）
AI_TAB_OLD = """        ...(currentPlatform == null ? void 0 : currentPlatform.showAi) ? [{
          key: "4",
          tab: "AI",
          icon: RobotOutlined,
          color: "#eb2f96",
          component: _sfc_main$5
        }] : [],
"""
rep(AI_TAB_OLD, "", "ui: 移除 AI 对话标签页（原作者的 aichathelper 接口）")

rep("// @connect      aichathelper.top\n", "", "ui: 移除 aichathelper 域名授权")

QUEUE_TAB_OLD = """        ...(currentPlatform == null ? void 0 : currentPlatform.queueAdapter) ? [{
          key: "queue",
          tab: "\u961f\u5217",
          icon: OrderedListOutlined,
          color: "#fa8c16",
          component: _sfc_main$3
        }] : [],
"""
rep(QUEUE_TAB_OLD, "", "ui: 移除刷课队列标签页")

# 删除 AI 对话组件本体（其中硬编码了原作者的 she.aichathelper.top/ai/ds 接口）
AI_BLOCK_START = 'const _hoisted_1$4 = { class: "ai-wrapper" };'
AI_BLOCK_END = 'const _hoisted_1$3 = { class: "record-wrap" };'
if src.count(AI_BLOCK_START) == 1 and src.count(AI_BLOCK_END) == 1:
    _ai_i = src.index(AI_BLOCK_START)
    _ai_j = src.index(AI_BLOCK_END)
    if 0 < _ai_i < _ai_j:
        src = src[:_ai_i] + src[_ai_j:]
        edits.append("ui: 删除 AI 对话组件（含 aichathelper 接口）")

# ---------------------------------------------------------------- 9. 稳定性
rep(
    '''              text: "定时刷新（防卡死）",
              value: true,
              type: "switch",
              tips: "（建议开启）每30分钟刷新页面，防止脚本卡死"''',
    '''              text: "定时刷新（防卡死）",
              value: false,
              type: "switch",
              tips: "默认关闭：开启后每 30 分钟会强制刷新整个页面（面板会重启一次）。只有长时间挂机卡死才需要打开"''',
    "stability: 定时刷新默认关",
)

rep(
    "      if (reloadCount >= 3) {",
    "      if (reloadCount >= 1) {",
    "stability: 视频失败刷新次数 3->1",
)

rep(
    "      setTimeout(() => {\n        location.reload();\n      }, 3e3);",
    "      setTimeout(() => {\n        location.reload();\n      }, 1e4);",
    "stability: 视频失败刷新延迟 3s->10s",
)

rep(
    '''      vue.watch(
        () => setting.config.basicConfig.token,
        (newVal) => {
          window.location.reload();
        },
        {
          deep: true
        }
      );''',
    '''      vue.watch(
        () => setting.config.basicConfig.token,
        () => {
          console.info("[自接AI] 密钥变动已忽略（本版不需要付费密钥，也不会刷新页面）");
        },
        {
          deep: true
        }
      );''',
    "stability: 改密钥不再整页刷新",
)

# ---------------------------------------------------------------- 11. 依赖自检外壳（CDN 拉不到库时给可见提示）
PROLOGUE_PATH = os.path.join(ROOT, "src", "prologue.js")
EPILOGUE_PATH = os.path.join(ROOT, "src", "epilogue.js")

# ---------------------------------------------------------------- 输出
src = src.replace("\r\n", "\n") if "\r\n" in src else src
if os.path.exists(PROLOGUE_PATH) and os.path.exists(EPILOGUE_PATH):
    prologue = io.open(PROLOGUE_PATH, "r", encoding="utf-8").read()
    epilogue = io.open(EPILOGUE_PATH, "r", encoding="utf-8").read()
    marker = "// ==/UserScript=="
    cut = src.index(marker) + len(marker)
    src = src[:cut] + "\n\n" + prologue + src[cut:] + epilogue
    edits.append("wrap: 依赖自检外壳")
with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write(src)

print("OK 共应用 %d 处修改" % len(edits))
for item in edits:
    print("  - " + item)
print("输出：%s（%.1f KB）" % (OUT, os.path.getsize(OUT) / 1024.0))
