# 参与贡献

## 本地开发

```bash
# 1) 放置上游脚本（不入库）
cp <你的脚本>.txt upstream/original-4.8.3.txt

# 2) 构建
python tools/build.py

# 3) 测试
node tests/test_engine.js
```

## 改代码的约定

- **所有对上游脚本的改动都写在 `tools/build.py` 里**，用 `rep(旧文本, 新文本, "说明")`。
  `rep()` 会断言“命中且只命中一次”，锚点漂移会立刻报错，避免产出半改的文件。
- 引擎代码（`ENGINE` 字符串）只依赖上游提供的 `useSettingStore`、`sleep`、`GM_xmlhttpRequest`、
  `messageStore` 等少数符号，**不要**引用上游的内部类，否则上游一升级就崩。
- 新增设置项只需往 `basicConfig` 加字段：上游的面板是数据驱动渲染，无需改 UI。
- 提交前请确保 `node tests/test_engine.js` 全绿；新增行为请补用例。

## 不要做的事

- 不要提交上游脚本、构建产物、`dist/`、任何 API Key。
- 不要引入需要联网下载依赖的测试。
- 不要为了“多拿分”而伪造答案来源（例如包装付费题库的接口）。
