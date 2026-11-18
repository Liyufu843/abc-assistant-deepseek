# 🐮 ABC 网课助手 · 自接大模型版（DeepSeek）

把学习通 / 智慧树网课助手的**搜题、AI 答题**两处付费接口，换成你自己接的大模型（默认 DeepSeek）；同时**删掉原作者的 AI 对话面板与刷课队列页**，界面精简为 5 个标签。
不需要原作者的“爱充电”密钥，只花你自己的 API 费用（一道客观题约 ¥0.0005~0.002）。

> ⚠️ **本项目不含任何原作者的代码**。它是一个**补丁工具**：你自己提供上游脚本，本地生成改造后的版本。
> 详见下方 [版权与免责](#版权与免责)。

---

## 它做了什么

上游脚本靠三个签名接口工作：`/question/accurateSearch`、`/question/fuzzySearch`、`/ai/answer`，全部要求付费 `token`。
本项目在构建时把这三处替换成「自接大模型引擎」，返回**同样的数据结构**，因此下游的答题、填充、判分逻辑一行都不用改。

| 能力 | 说明 |
|---|---|
| 兼容多引擎 | DeepSeek（默认）/ 智谱 GLM / 硅基流动 / 阿里百炼 / Gemini / 本地 Ollama / 任意 OpenAI 兼容接口 |
| 并发预取 | 开答前 6 路并发预取最多 24 题，命中缓存直接填充；同一批 30 秒内只预取一次 |
| 持久化缓存 | 答案存进浏览器本地，重开浏览器同题秒答 |
| 三档精度 | 极速（直出）/ 标准（先分析再作答）/ 高准确（3 次独立作答投票） |
| 考试强化 | 识别考试页自动切「高准确 + 最强模型」；字母勾不上时改用选项原文重填 |
| 界面精简 | 移除原作者的「AI 对话」（硬编码 `she.aichathelper.top`）与「刷课队列」两个页面，只留 **首页 / 日志 / 答题 / 搜题 / 设置** |
| 稳定性 | 定时刷新默认关闭、视频失败最多重刷 1 次、连续失败 45 秒熔断、多面板告警 |
| 依赖自检 | CDN 拉不到 Vue/antd 等库时，从 jsdelivr → unpkg → staticfile 补拉，全失败弹可见提示框（不再静默无面板） |

完整说明见 [docs/安装与配置.md](docs/安装与配置.md)。

---

## 快速开始

### 1. 准备上游脚本

本仓库**不包含**上游脚本。请自行获取 `🐮ABC超星学习通｜智慧树网课助手-4.8.3`（`.txt` 或 `.user.js`），放到：

```
upstream/original-4.8.3.txt
```

（也可用环境变量 `ABC_UPSTREAM` 指定任意路径。）

### 2. 构建

```bash
python tools/build.py
```

产物：`dist/ABC-assistant-DeepSeek-v1.3.0.user.js`
构建脚本会校验每一处替换锚点，**命中数不为 1 就报错退出**，不会产出“半改”的文件。

### 3. 安装

1. 浏览器装 [Tampermonkey](https://www.tampermonkey.net/)；
2. 把 `dist/` 里的 `.user.js` 拖进浏览器窗口 → 安装；
3. 打开课程页 → 面板「设置」：
   - **AI 引擎**：DeepSeek（默认）
   - **AI 密钥**：填你自己的 Key（[platform.deepseek.com](https://platform.deepseek.com) 创建，充 10 元够刷一两万题）
   - 其余保持默认即可

### 4. 测试

```bash
node tests/test_engine.js
```

会从 `dist/` 里抽出引擎模块，用桩件跑 **88 项**断言（题型归一化、答案投票、缓存命中、限流重试、熔断、答卷格式转换……）。
没有构建产物时脚本会直接跳过并返回 0，方便 CI。

---

## 目录结构

```
.
├─ tools/build.py                  # 补丁构建器（唯一真相源：替换锚点 + 注入的引擎）
├─ src/prologue.js                 # 外壳：依赖自检 + 多 CDN 补拉 + 失败提示框
├─ src/epilogue.js                 # 外壳收尾
├─ tests/test_engine.js            # 引擎单元测试（88 项，无产物时自动跳过）
├─ docs/安装与配置.md                # 面向使用者的完整说明
├─ docs/界面说明.md                 # 5 个标签页 + 设置项 + 日志解读
├─ docs/CHANGELOG.md
├─ docs/CONTRIBUTING.md
├─ docs/免责声明.md
├─ .github/workflows/ci.yml        # 语法检查 + 构建 + 单测
├─ .github/ISSUE_TEMPLATE/         # bug 模板（要求带日志截图）
├─ .github/PULL_REQUEST_TEMPLATE.md
├─ LICENSE / NOTICE                # 仅覆盖本项目自写部分；声明与上游的关系
└─ upstream/ , dist/               # 本地放上游脚本与产物（.gitignore 忽略）
```

---

## 原理解析（想改的人看这里）

上游脚本是 Vue3 + pinia + ant-design-vue 的**编译产物**，界面是数据驱动的：往 `basicConfig` 里加字段就自动出现设置项。
所以本项目只做三件事：

0. **删界面**：把 `contentMap` 里的「AI」与「队列」两项摘掉，再整段删除 AI 对话组件（它里面硬编码了 `she.aichathelper.top`）；
1. **加设置**：在 `basicConfig` 注入 `aiEnabled / aiProvider / aiApiKey / aiModelName / aiBaseUrl / aiMaxRetry / aiTimeout / aiAccuracyMode / aiExamBoost / aiDebug`；
2. **改三个函数**：`getAccurateAnswer` 在自接模式下直接返回 `code:-1004`（“题库没搜到”），让原流程自然落入 AI 分支；`getAIAnswer` / `fetchFuzzySearch` 前置本地实现；
3. **打几个补丁**：答题门槛放行、纯题库模式也走 AI、开答前的并发预取、字母→选项原文（答卷流）、稳定性开关。

`tools/build.py` 里的每个 `rep(...)` 都带一句中文说明，改起来很直观。

---

## 版权与免责

- 上游脚本版权归原作者 **oolikeABC**，其许可证为 **Proprietary**。本仓库**不包含、不重新分发**上游代码；构建时才从你本地读取。
- 因此本仓库只对**自己编写的部分**（补丁器、引擎、测试、文档）授权：**MIT**，见 [LICENSE](LICENSE)。
- 二次分发“构建产物”（即改版后的完整脚本）属于对上游代码的再分发，**风险由你自行承担**，请先确认上游许可与当地法规。
- 本项目仅供**学习与技术研究**：请勿用于违反学校考试纪律、平台服务条款的用途。因此产生的后果由使用者自负。
- 与原作者、学习通、智慧树均无关联，也未获其授权或背书。

---

## 致谢

- 上游脚本作者 oolikeABC：提供了完整可读的构建产物，才有这种“外科手术式改造”的可能；
- DeepSeek / 智谱 / 硅基流动 等提供 OpenAI 兼容接口，让自接模型成为十行代码的事。
