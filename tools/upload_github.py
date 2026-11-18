# -*- coding: utf-8 -*-
"""把本地仓库目录通过 GitHub Contents API 上传（无需安装 git）。

用法：
    set GITHUB_TOKEN=ghp_xxx
    set GITHUB_OWNER=your-name
    set GITHUB_REPO=abc-assistant-deepseek
    python tools/upload_github.py --dir D:\\dk\\abc-helper-repo --private 0

行为：
1) 若仓库不存在 → 调 POST /user/repos 创建；
2) 逐个文件 PUT /repos/{owner}/{repo}/contents/{path}（已存在的先取 sha 再覆盖）；
3) 跳过 upstream/、dist/、__pycache__、.git、.token；
4) 结束后打印仓库地址。
"""
import base64
import json
import urllib.parse
import os
import sys
import time
import urllib.error
import urllib.request

TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
OWNER = os.environ.get("GITHUB_OWNER", "").strip()
REPO = os.environ.get("GITHUB_REPO", "abc-assistant-deepseek").strip()
API = "https://api.github.com"
SKIP_DIRS = {"upstream", "dist", "__pycache__", ".git", ".idea", ".vscode"}


def call(method, path, payload=None):
    url = API + path
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "Bearer " + TOKEN)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "abc-assistant-uploader")
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, (json.loads(body) if body else {})
    except urllib.error.HTTPError as err:
        detail = err.read().decode("utf-8", "replace")[:400]
        return err.code, {"error": detail}


def main():
    if not TOKEN or not OWNER:
        print("缺少 GITHUB_TOKEN / GITHUB_OWNER")
        return 2
    root = sys.argv[sys.argv.index("--dir") + 1] if "--dir" in sys.argv else os.getcwd()
    private = "--private" in sys.argv and sys.argv[sys.argv.index("--private") + 1] == "1"

    status, info = call("GET", "/repos/%s/%s" % (OWNER, REPO))
    if status == 404:
        status, info = call("POST", "/user/repos", {
            "name": REPO,
            "description": "把网课助手的付费搜题接口换成自接大模型（补丁器，不含上游代码）",
            "private": private,
            "has_issues": True,
            "has_wiki": False,
        })
        if status not in (200, 201):
            print("创建仓库失败", status, info)
            return 1
        print("已创建仓库:", info.get("html_url"))
        time.sleep(1)
    elif status != 200:
        print("读取仓库失败", status, info)
        return 1
    else:
        print("仓库已存在:", info.get("html_url"))

    files = []
    for cur, dirs, names in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in names:
            full = os.path.join(cur, name)
            rel = os.path.relpath(full, root).replace("\\", "/")
            if rel.split("/")[0] in SKIP_DIRS or name == ".token":
                continue
            files.append((rel, full))
    files.sort()

    ok = 0
    for rel, full in files:
        with open(full, "rb") as fh:
            content = base64.b64encode(fh.read()).decode("ascii")
        path = "/repos/%s/%s/contents/%s" % (OWNER, REPO, urllib.parse.quote(rel))
        payload = {"message": "upload " + rel, "content": content, "branch": "main"}
        status, info = call("GET", path)
        if status == 200 and isinstance(info, dict) and info.get("sha"):
            payload["sha"] = info["sha"]
        status, info = call("PUT", path, payload)
        if status in (200, 201):
            ok += 1
            print("  ok  " + rel)
        else:
            print("  FAIL %s -> %s %s" % (rel, status, info))
    print("\n完成 %d/%d 个文件" % (ok, len(files)))
    print("仓库地址: https://github.com/%s/%s" % (OWNER, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
