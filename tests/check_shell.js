// 校验 src/ 下的外壳片段能拼成合法程序（片段单独看不是完整 JS）
const fs = require("fs");
const path = require("path");
const dir = path.join(__dirname, "..", "src");
const prologue = fs.readFileSync(path.join(dir, "prologue.js"), "utf8");
const epilogue = fs.readFileSync(path.join(dir, "epilogue.js"), "utf8");
const code = prologue + "/* stub body */\n" + epilogue;
try {
  new Function(code);
  console.log("外壳拼接语法 OK（prologue + body + epilogue）");
} catch (error) {
  console.error("外壳拼接语法错误:", error.message);
  process.exit(1);
}
