// 引擎单元测试：从生成的脚本里抽出本地AI模块，用桩函数跑一遍关键逻辑
const fs = require("fs");
const file = "D:/dk/ABC网课助手-自接DeepSeek-1.2.2.user.js";
const src = fs.readFileSync(file, "utf8");

const START = "  // ==================== 自接大模型引擎（DeepSeek 改版注入） ====================";
const END = "  // ==================== 自接大模型引擎（注入结束） ====================";
const i = src.indexOf(START);
const j = src.indexOf(END);
if (i < 0 || j < 0) { console.error("FAIL 找不到引擎标记"); process.exit(1); }
const engine = src.slice(i, j + END.length);
console.log("引擎模块长度:", engine.length, "字符");

// ---- 桩：设置 store / sleep / GM_xmlhttpRequest
let settings = { aiEnabled: true, aiProvider: "deepseek", aiApiKey: "test-key", aiModelName: "", aiBaseUrl: "", aiMaxRetry: 1, aiTimeout: 35, reqIntervalTime: 0.001 };
const useSettingStore = () => ({
  config: { basicConfig: Object.fromEntries(Object.entries(settings).map(([k, v]) => [k, { value: v }])) },
});
const sleep = (ms) => new Promise((r) => setTimeout(r, Math.min(ms, 5)));
let captured = null;
let capturedModels = [];
let mode = "429-then-ok";
let rateLimited = false;
let voteCount = 0;
const GM_xmlhttpRequest = (opts) => {
  captured = { url: opts.url, body: JSON.parse(opts.data), headers: opts.headers };
  capturedModels.push(captured.body.model);
  if (mode === "429-then-ok") {
    if (!rateLimited) {
      rateLimited = true;
      opts.onload({ status: 429, responseText: JSON.stringify({ error: { message: "rate limited" } }) });
      return;
    }
    opts.onload({ status: 200, responseText: JSON.stringify({ choices: [{ message: { content: "ACD" } }] }) });
  } else if (mode === "model-not-found") {
    if (captured.body.model === "glm-4.5-flash") {
      opts.onload({ status: 400, responseText: JSON.stringify({ error: { message: "模型不存在" } }) });
    } else {
      opts.onload({ status: 200, responseText: JSON.stringify({ choices: [{ message: { content: "B" } }] }) });
    }
  } else if (mode === "http500") {
    opts.onload({ status: 500, responseText: "internal error" });
  } else if (mode === "zh-judge") {
    opts.onload({ status: 200, responseText: JSON.stringify({ choices: [{ message: { content: "正确" } }] }) });
  } else if (mode === "cot") {
    opts.onload({ status: 200, responseText: JSON.stringify({ choices: [{ message: { content: "分析：A、B、D 都能输入数据。\n答案：ABD" } }] }) });
  } else if (mode === "vote") {
    voteCount += 1;
    const votes = ["A", "A", "B"];
    const content = "分析：略\n答案：" + votes[Math.min(voteCount - 1, 2)];
    opts.onload({ status: 200, responseText: JSON.stringify({ choices: [{ message: { content } }] }) });
  } else if (mode === "letters") {
    opts.onload({ status: 200, responseText: JSON.stringify({ choices: [{ message: { content: "A" } }] }) });
  } else {
    opts.onload({ status: 200, responseText: JSON.stringify({ choices: [{ message: { content: '{"type":"3","options":[],"answer":["正确"],"explain":"显然"}' } }] }) });
  }
};

const factory = new Function("useSettingStore", "sleep", "GM_xmlhttpRequest", "window", engine + `
  return { __abcNormalizeAnswers, __abcLocalAIActive, __abcAIConfig, __abcBuildQuestionMessages, __abcAIAnswer, __abcAIFuzzy, __abcAIChatCompletions, __abcTypeCode, __abcAIPrefetch, __abcAIPickMaxTokens, __abcExamBoostActive, __abcRetryFillWithText, __abcKind, __abcOptionList, __abcLettersToText, __abcAIQuestionKey, __abcAICacheRestore };
`);
const localStorageStub = {
  store: {},
  getItem(k) { return Object.prototype.hasOwnProperty.call(this.store, k) ? this.store[k] : null; },
  setItem(k, v) { this.store[k] = String(v); },
  removeItem(k) { delete this.store[k]; }
};
const windowStub = { localStorage: localStorageStub };
const api = factory(useSettingStore, sleep, GM_xmlhttpRequest, windowStub);

let pass = 0, fail = 0;
const eq = (name, got, want) => {
  const ok = JSON.stringify(got) === JSON.stringify(want);
  if (ok) { pass++; console.log("  ok  " + name); }
  else { fail++; console.log("  FAIL " + name + " -> got " + JSON.stringify(got) + " want " + JSON.stringify(want)); }
};

// 1. 启用判定
settings.aiApiKey = "";
eq("无key时仍算本地模式（会立刻报错，不再回落到付费通道）", api.__abcLocalAIActive(), true);
settings.aiApiKey = "test-key";
eq("有key时 __abcLocalAIActive=true", api.__abcLocalAIActive(), true);
settings.aiEnabled = false;
eq("关闭开关时 false", api.__abcLocalAIActive(), false);
settings.aiEnabled = true;
settings.aiProvider = "ollama";
eq("ollama 无key也可用", api.__abcLocalAIActive(), true);
eq("ollama base", api.__abcAIConfig().base, "http://127.0.0.1:11434/v1");
settings.aiProvider = "deepseek";

// 2. 预设解析
const cfg = api.__abcAIConfig();
eq("preset base", cfg.base, "https://api.deepseek.com/v1");
eq("preset 首个模型", cfg.models[0], "deepseek-chat");
eq("timeout=35s", cfg.timeout, 35000);

// 3. 答案归一化
eq("单选 B", api.__abcNormalizeAnswers("0", "B", []), ["B"]);
eq("单选多字母只取第一个", api.__abcNormalizeAnswers("0", "答案是 B，因为…", []), ["B"]);
eq("多选顿号", api.__abcNormalizeAnswers("1", "A、C、D", []), ["ACD"]);
eq("多选空格", api.__abcNormalizeAnswers("1", "A B D", []), ["ABD"]);
eq("判断题-错误", api.__abcNormalizeAnswers("3", "错误", []), ["错误"]);
eq("判断题-正确", api.__abcNormalizeAnswers("3", "这句话是正确的", []), ["正确"]);
eq("判断题-不对", api.__abcNormalizeAnswers("3", "不对", []), ["错误"]);
eq("填空题 多空", api.__abcNormalizeAnswers("2", "北京===上海", []), ["北京", "上海"]);
eq("填空题 换行", api.__abcNormalizeAnswers("2", "北京\n上海", []), ["北京", "上海"]);
eq("简答题原样", api.__abcNormalizeAnswers("4", "先做A再做B", []), ["先做A再做B"]);

// 4. prompt 构造
const msgs = api.__abcBuildQuestionMessages({ type: "1", title: "以下属于操作系统的是", optionsText: ["Windows", "Linux", "Word", "Excel"] });
eq("prompt 有系统角色", msgs[0].role, "system");
const userMsg = msgs[1].content;
eq("prompt 含选项字母", /A\. Windows[\s\S]*B\. Linux/.test(userMsg), true);
eq("prompt 含多选规则", /多选题/.test(userMsg), true);

// 4.1 智慧树路径传中文题型
eq("中文判断题→3", api.__abcTypeCode("判断题"), "3");
eq("中文多选题→1", api.__abcTypeCode("多选题"), "1");
eq("中文填空题→2", api.__abcTypeCode("填空题"), "2");
eq("数值题型原样", api.__abcTypeCode("0"), "0");
eq("未知题型→空", api.__abcTypeCode("未知题型"), "");
const zhMsgs = api.__abcBuildQuestionMessages({ type: "多选题", title: "以下正确的有", optionsText: ["甲", "乙"] });
eq("中文多选 prompt 走多选规则", /多选题/.test(zhMsgs[1].content), true);
const zhJudgeMsgs = api.__abcBuildQuestionMessages({ type: "判断题", title: "地球是圆的" });
eq("中文判断 prompt 走判断规则", /判断题/.test(zhJudgeMsgs[1].content), true);

(async () => {
  // 5. 限流后重试成功
  mode = "429-then-ok";
  const res = await api.__abcAIAnswer({ type: "1", title: "以下属于操作系统的是", optionsText: ["Windows", "Linux", "Word", "Excel"] });
  eq("answer payload code", res.code, 1);
  eq("answer 内容", res.data.answer, ["ACD"]);
  eq("remainCount", res.data.remainCount, "自接AI");
  eq("请求 URL", captured.url, "https://api.deepseek.com/v1/chat/completions");
  eq("Authorization 头", captured.headers.Authorization, "Bearer test-key");
  eq("请求 model", captured.body.model, "deepseek-chat");
  eq("stream=false", captured.body.stream, false);
  eq("429 后重试了同一模型", capturedModels, ["deepseek-chat", "deepseek-chat"]);
  settings.aiAccuracyMode = "standard";
  eq("默认标准模式客观题 max_tokens=200", captured.body.max_tokens, 200);
  eq("标准模式单选 max_tokens=200", api.__abcAIPickMaxTokens("0"), 200);
  eq("标准模式简答 max_tokens=560", api.__abcAIPickMaxTokens("4"), 560);
  settings.aiAccuracyMode = "fast";
  eq("极速模式单选 max_tokens=32", api.__abcAIPickMaxTokens("0"), 32);
  eq("极速模式简答 max_tokens=420", api.__abcAIPickMaxTokens("4"), 420);

  // 6. 缓存命中
  const before = captured;
  const res2 = await api.__abcAIAnswer({ type: "1", title: "以下属于操作系统的是", optionsText: ["Windows", "Linux", "Word", "Excel"] });
  eq("缓存复用", res2.data.answer, ["ACD"]);
  eq("缓存未再请求", captured === before, true);

  // 7. 模型不存在时自动换下一个模型（预设链里第一个模型报 400，自动退到第二个）
  mode = "model-not-found";
  capturedModels = [];
  settings.aiProvider = "zhipu";
  const res3 = await api.__abcAIAnswer({ type: "0", title: "1+1 等于几", optionsText: ["A. 1", "B. 2"] });
  eq("换模型后拿到答案", res3.data.answer, ["B"]);
  eq("换模型顺序", capturedModels, ["glm-4.5-flash", "glm-4-flash-250414"]);
  settings.aiProvider = "deepseek";

  // 7.1 推理模型不会被自动降级链选中（避免又慢又贵）
  capturedModels = [];
  api.__abcAIConfig();
  eq("DeepSeek 预设不再含 reasoner", JSON.stringify(api.__abcAIConfig().models), JSON.stringify(["deepseek-chat"]));

  // 7.2 标准模式：模型先分析再给答案，解析器要能只取「答案：」后的内容
  settings.aiAccuracyMode = "standard";
  mode = "cot";
  const cot = await api.__abcAIAnswer({ type: "1", title: "下列属于输入设备的有", optionsText: ["A. 键盘", "B. 鼠标", "C. 硬盘", "D. 扫描仪"] });
  eq("分析+答案格式能正确解析", cot.data.answer, ["ABD"]);
  const cotPrompt = captured.body.messages[1].content;
  eq("标准模式提示词要求分析行", /分析/.test(cotPrompt) && /答案/.test(cotPrompt), true);
  eq("多选提示词含保守规则", /宁可不选|不要凑数/.test(cotPrompt), true);
  eq("判断提示词含绝对化提醒", (() => {
    const msgs = api.__abcBuildQuestionMessages({ type: "3", title: "凡是质变的都是根本质变" });
    return /绝对化|一定/.test(msgs[1].content);
  })(), true);

  // 7.3 高准确模式：两次独立作答一致就提前结束（省钱又准）
  settings.aiAccuracyMode = "high";
  voteCount = 0;
  capturedModels = [];
  mode = "vote";
  const voted = await api.__abcAIAnswer({ type: "1", title: "投票测试题目", optionsText: ["A. 甲", "B. 乙"] });
  eq("高准确模式取多数票", voted.data.answer, ["A"]);
  eq("两次一致即停止投票", capturedModels.length, 2);
  settings.aiAccuracyMode = "standard";

  // 7.5 中文题型（智慧树）走完整链路
  mode = "zh-judge";
  const zhJudge = await api.__abcAIAnswer({ type: "判断题", title: "智慧树中文题型测试题", optionsText: [] });
  eq("中文判断作答", zhJudge.data.answer, ["正确"]);

  // 8. 搜索面板 items 结构
  mode = "json-fuzzy";
  const fuzzy = await api.__abcAIFuzzy("地球是圆的吗");
  eq("fuzzy code", fuzzy.code, 1);
  eq("fuzzy items 长度", fuzzy.data.items.length, 1);
  eq("fuzzy 判断题 type", fuzzy.data.items[0].type, "3");
  eq("fuzzy answer", fuzzy.data.items[0].answer, ["正确"]);

  // 7.6 开答前并发预取 → 逐题轮到时直接命中缓存
  mode = "letters";
  capturedModels = [];
  const batch = [
    { type: "0", title: "预取题一", optionsText: ["A. 甲", "B. 乙"] },
    { type: "0", title: "预取题二", optionsText: ["A. 甲", "B. 乙"] },
    { type: "0", title: "预取题三", optionsText: ["A. 甲", "B. 乙"] }
  ];
  api.__abcAIPrefetch(batch);
  await new Promise((r) => setTimeout(r, 600));
  eq("预取一次发出 3 个并发请求", capturedModels.length, 3);
  const beforeHit = capturedModels.length;
  const tHit = Date.now();
  const cached = await api.__abcAIAnswer(batch[1]);
  const hitCost = Date.now() - tHit;
  eq("预取结果命中缓存", cached.data.answer, ["A"]);
  eq("命中缓存不再发请求", capturedModels.length, beforeHit);
  eq("命中缓存几乎瞬时(<50ms)", hitCost < 50, true);

  // 10.5 答案缓存写入 localStorage，重新加载脚本后依然命中
  mode = "letters";
  localStorageStub.removeItem("__abcAI_answer_cache_v1");
  settings.aiApiKey = "test-key";
  const persisted = await api.__abcAIAnswer({ type: "0", title: "持久化测试题", optionsText: ["A. 甲", "B. 乙"] });
  eq("持久化题已作答", persisted.data.answer, ["A"]);
  const dump = JSON.parse(localStorageStub.getItem("__abcAI_answer_cache_v1") || "{}");
  eq("缓存已写入 localStorage", Object.keys(dump).some((k) => k.indexOf("持久化测试题") >= 0), true);
  const api2 = factory(useSettingStore, sleep, GM_xmlhttpRequest, windowStub);
  api2.__abcAICacheRestore();
  const sentBefore = capturedModels.length;
  const fromDisk = await api2.__abcAIAnswer({ type: "0", title: "持久化测试题", optionsText: ["A. 甲", "B. 乙"] });
  eq("重载后命中磁盘缓存", fromDisk.data.answer, ["A"]);
  eq("重载后未再发请求", capturedModels.length, sentBefore);


  // 13. 题型判定（中文语义优先，修正 名词解释/论述/计算 的错位）
  eq("名词解释→6", api.__abcKind({ type: "名词解释" }), "6");
  eq("论述题→5", api.__abcKind({ type: "论述题" }), "5");
  eq("计算题→4", api.__abcKind({ type: "计算题" }), "4");
  eq("单项选择题→0", api.__abcKind({ type: "单项选择题" }), "0");
  eq("数字题型原样", api.__abcKind({ type: "1" }), "1");

  // 14. 选项来源：没有 optionsText 时从 optionEls 取
  const els = [{ textContent: "甲项" }, { textContent: "乙项" }];
  eq("从 optionEls 提取选项", api.__abcOptionList({ optionEls: els }), ["甲项", "乙项"]);
  eq("字母转选项原文", api.__abcLettersToText(["AC"], ["甲项", "乙项", "丙项"]), ["甲项", "丙项"]);
  eq("字母越界返回 null", api.__abcLettersToText(["D"], ["甲项"]), null);

  // 15. 答卷（DOM 版）拿到的是选项原文，不是字母
  mode = "letters";
  const domQuestion = { type: "单选题", title: "答卷格式测试题", optionEls: els, optionsText: ["甲项", "乙项"] };
  const domAnswer = await api.__abcAIAnswer(domQuestion);
  eq("答卷答案被转成原文", domAnswer.data.answer, ["甲项"]);

  // 16. 两种答卷流的缓存键不能串
  const kvKey = api.__abcAIQuestionKey({ type: "0", title: "同一题干", optionsText: ["甲项", "乙项"] });
  const domKey = api.__abcAIQuestionKey({ type: "0", title: "同一题干", optionsText: ["甲项", "乙项"], optionEls: els });
  eq("dom / kv 缓存键不同", kvKey !== domKey, true);

  // 9. 全失败时返回可读错误而不是抛异常
  mode = "http500";
  const bad = await api.__abcAIAnswer({ type: "4", title: "简述光合作用的意义" });
  eq("失败 code=-1", bad.code, -1);
  eq("失败信息可读", /AI答题失败/.test(bad.data.answer[0]), true);

  // 10. 熔断：网络/5xx 失败后短时间内直接返回，不再逐题重试
  const reqBefore = capturedModels.length;
  const t0 = Date.now();
  const second = await api.__abcAIAnswer({ type: "0", title: "熔断测试题", optionsText: ["A. 甲", "B. 乙"] });
  const cost = Date.now() - t0;
  eq("熔断后仍返回可读错误", /暂停/.test(second.data.answer[0]), true);
  eq("熔断期间未再发请求", capturedModels.length, reqBefore);
  eq("熔断响应很快(<500ms)", cost < 500, true);

  // 11. 没填 key 时立刻报错，不等待、不卡住
  settings.aiApiKey = "";
  const t1 = Date.now();
  const noKey = await api.__abcAIAnswer({ type: "0", title: "未配置密钥测试", optionsText: ["A. 甲", "B. 乙"] });
  const cost2 = Date.now() - t1;
  eq("未配置密钥时 code=-1", noKey.code, -1);
  eq("提示去填密钥", /AI 密钥/.test(noKey.data.answer[0]), true);
  eq("无钥匙响应很快(<300ms)", cost2 < 300, true);
  settings.aiApiKey = "test-key";

  // 12. 考试兜底：字母勾不上时改用选项原文重填
  const q1 = { type: "1", title: "多选题", optionsText: ["甲", "乙", "丙"], answer: { code: 2, answer: ["AC"] } };
  const okFill = api.__abcRetryFillWithText(q1, (item) => item.answer.answer.indexOf("甲") >= 0);
  eq("改用选项原文后填充成功", okFill, true);
  eq("答案被改写成选项原文", JSON.stringify(q1.answer.answer), JSON.stringify(["甲", "丙"]));
  const q2 = { type: "1", optionsText: ["甲"], answer: { answer: ["B"] } };
  const failedFill = api.__abcRetryFillWithText(q2, () => false);
  eq("仍失败时返回 false", failedFill, false);
  eq("仍失败时不篡改原答案", JSON.stringify(q2.answer.answer), JSON.stringify(["B"]));
  eq("无 DOM 环境考试强化不误触发", api.__abcExamBoostActive(), false);

  console.log(`\n结果：${pass} 通过 / ${fail} 失败`);
  process.exit(fail ? 1 : 0);
})();
