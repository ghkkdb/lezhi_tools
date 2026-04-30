# Git 使用指南

本文档记录 Git 常用操作与最佳实践。

---

## 一、Git 安装与配置

### 1.1 安装 Git

**Windows**：
- 下载地址：https://git-scm.com/download/win
- 运行安装程序，一路 Next 即可

**验证安装**：
```bash
git --version
```

### 1.2 配置用户信息

```bash
# 设置用户名
git config --global user.name "你的用户名"

# 设置邮箱
git config --global user.email "你的邮箱"

# 查看配置
git config --global user.name
git config --global user.email
```

### 1.3 配置 SSH 密钥（可选，推荐）

```bash
# 生成 SSH 密钥
ssh-keygen -t ed25519 -C "你的邮箱"

# 查看公钥
cat ~/.ssh/id_ed25519.pub

# 将公钥添加到 GitHub: Settings → SSH and GPG keys → New SSH key
```

---

## 二、仓库操作

### 2.1 初始化仓库

```bash
# 在项目目录初始化
git init

# 克隆远程仓库
git clone https://github.com/用户名/仓库名.git
```

### 2.2 关联远程仓库

```bash
# 添加远程仓库
git remote add origin https://github.com/用户名/仓库名.git

# 查看远程仓库
git remote -v

# 修改远程仓库地址
git remote set-url origin https://github.com/新地址.git

# 删除远程仓库
git remote remove origin
```

---

## 三、文件操作

### 3.1 添加文件

```bash
# 添加单个文件
git add 文件名

# 添加所有文件
git add .

# 添加指定目录
git add 目录名/
```

### 3.2 查看状态

```bash
# 查看工作区状态
git status

# 查看简洁状态
git status -s
```

### 3.3 提交更改

```bash
# 提交暂存区的更改
git commit -m "提交说明"

# 添加并提交（已跟踪文件）
git commit -am "提交说明"

# 修改上次提交信息
git commit --amend -m "新的提交说明"
```

### 3.4 删除文件

```bash
# 删除文件（从工作区和暂存区）
git rm 文件名

# 仅从暂存区删除
git rm --cached 文件名
```

---

## 四、分支操作

### 4.1 创建与切换分支

```bash
# 查看所有分支
git branch -a

# 创建新分支
git branch 分支名

# 切换分支
git checkout 分支名

# 创建并切换分支
git checkout -b 分支名

# 切换到上一个分支
git checkout -
```

### 4.2 合并分支

```bash
# 合并指定分支到当前分支
git merge 分支名

# 合并时禁止快进模式
git merge --no-ff 分支名
```

### 4.3 删除分支

```bash
# 删除本地分支
git branch -d 分支名

# 强制删除
git branch -D 分支名

# 删除远程分支
git push origin --delete 分支名
```

### 4.4 重命名分支

```bash
# 重命名当前分支
git branch -m 新分支名

# 重命名指定分支
git branch -m 旧分支名 新分支名
```

---

## 五、远程操作

### 5.1 推送到远程

```bash
# 推送当前分支到远程
git push

# 首次推送并设置上游分支
git push -u origin main

# 推送所有分支
git push --all

# 强制推送（谨慎使用）
git push -f
```

### 5.2 拉取远程更新

```bash
# 拉取并合并
git pull

# 拉取并变基
git pull --rebase

# 仅获取远程更新（不合并）
git fetch
```

### 5.3 查看远程信息

```bash
# 查看远程仓库详情
git remote show origin

# 查看远程分支
git branch -r
```

---

## 六、撤销操作

### 6.1 撤销工作区修改

```bash
# 撤销单个文件修改
git checkout -- 文件名

# 撤销所有修改
git checkout -- .
```

### 6.2 撤销暂存区

```bash
# 取消暂存
git reset HEAD 文件名

# 取消所有暂存
git reset HEAD .
```

### 6.3 回退提交

```bash
# 回退到上一版本（保留工作区修改）
git reset --soft HEAD^

# 回退到上一版本（保留暂存区修改）
git reset --mixed HEAD^

# 回退到上一版本（丢弃所有修改）
git reset --hard HEAD^

# 回退到指定版本
git reset --hard 版本号
```

### 6.4 撤销已推送的提交

```bash
# 创建新提交来撤销指定提交
git revert 版本号
```

---

## 七、查看历史

### 7.1 查看提交日志

```bash
# 查看提交历史
git log

# 单行显示
git log --oneline

# 图形化显示
git log --graph --oneline

# 查看最近 N 条
git log -n 5

# 查看指定文件历史
git log 文件名
```

### 7.2 查看差异

```bash
# 查看工作区与暂存区差异
git diff

# 查看暂存区与最新提交差异
git diff --cached

# 查看两个版本差异
git diff 版本1 版本2

# 查看分支差异
git diff 分支1 分支2
```

### 7.3 查看文件变更

```bash
# 查看文件每次提交的变更
git log -p 文件名

# 查看谁修改了文件
git blame 文件名
```

---

## 八、暂存工作

### 8.1 使用 stash

```bash
# 暂存当前工作
git stash

# 暂存并添加说明
git stash save "说明"

# 查看暂存列表
git stash list

# 恢复最近的暂存
git stash pop

# 恢复指定暂存
git stash apply stash@{n}

# 删除暂存
git stash drop stash@{n}

# 清空所有暂存
git stash clear
```

---

## 九、标签管理

### 9.1 创建标签

```bash
# 创建轻量标签
git tag 标签名

# 创建附注标签
git tag -a 标签名 -m "说明"

# 给指定提交打标签
git tag -a 标签名 版本号
```

### 9.2 管理标签

```bash
# 查看所有标签
git tag

# 查看标签信息
git show 标签名

# 删除本地标签
git tag -d 标签名

# 推送标签到远程
git push origin 标签名

# 推送所有标签
git push --tags

# 删除远程标签
git push origin --delete 标签名
```

---

## 十、.gitignore 配置

### 10.1 常用模板

```gitignore
# Python
__pycache__/
*.py[cod]
*.so
.Python
venv/
.venv/
*.egg-info/

# IDE
.idea/
.vscode/
*.swp

# 系统文件
.DS_Store
Thumbs.db

# 日志
*.log

# 编译产物
dist/
build/
*.exe
```

### 10.2 语法规则

| 语法 | 说明 |
|------|------|
| `#` | 注释 |
| `*.log` | 忽略所有 .log 文件 |
| `/dir/` | 忽略根目录下的 dir 目录 |
| `dir/` | 忽略所有 dir 目录 |
| `!file.txt` | 不忽略 file.txt |
| `**/foo` | 忽略所有 foo 目录 |

---

## 十一、常见问题解决

### 11.1 推送被拒绝

```bash
# 拉取远程更新并变基
git pull --rebase

# 再次推送
git push
```

### 11.2 合并冲突

```bash
# 查看冲突文件
git status

# 手动编辑冲突文件，解决冲突标记：
# <<<<<<< HEAD
# 本地修改
# =======
# 远程修改
# >>>>>>> branch-name

# 添加解决后的文件
git add .

# 提交合并结果
git commit -m "解决合并冲突"
```

### 11.3 忘记切换分支就修改了代码

```bash
# 暂存当前修改
git stash

# 切换到正确分支
git checkout 正确分支名

# 恢复修改
git stash pop
```

### 11.4 撤销已推送的错误提交

```bash
# 方法一：revert（推荐，不改变历史）
git revert 错误提交的版本号
git push

# 方法二：reset + 强制推送（谨慎使用）
git reset --hard 上一个正确版本号
git push -f
```

### 11.5 清理未跟踪的文件

```bash
# 查看将被删除的文件
git clean -n

# 删除未跟踪的文件
git clean -f

# 删除未跟踪的文件和目录
git clean -fd
```

---

## 十二、GitHub 常用操作

### 12.1 创建仓库

1. 登录 GitHub
2. 点击右上角 **+** → **New repository**
3. 填写仓库名称和描述
4. 选择 Public 或 Private
5. 点击 **Create repository**

### 12.2 Fork 项目

1. 打开目标仓库
2. 点击右上角 **Fork**
3. 选择你的账号

### 12.3 Pull Request

1. Fork 目标仓库
2. 创建新分支进行修改
3. 推送到你的 Fork
4. 点击 **Compare & pull request**
5. 填写 PR 说明，提交

### 12.4 配置 Personal Access Token

1. GitHub → Settings → Developer settings
2. Personal access tokens → Tokens (classic)
3. Generate new token
4. 勾选 `repo` 权限
5. 生成并保存 token
6. 推送时用 token 代替密码

---

## 十三、工作流程

### 13.1 日常开发流程

```
┌─────────────────────────────────────────────────────────┐
│                    日常开发流程                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   1. 拉取最新代码                                        │
│      git pull                                           │
│            │                                            │
│            ▼                                            │
│   2. 创建功能分支                                        │
│      git checkout -b feature/xxx                        │
│            │                                            │
│            ▼                                            │
│   3. 编写代码                                            │
│      ...                                                │
│            │                                            │
│            ▼                                            │
│   4. 提交更改                                            │
│      git add .                                          │
│      git commit -m "xxx"                                │
│            │                                            │
│            ▼                                            │
│   5. 推送分支                                            │
│      git push -u origin feature/xxx                     │
│            │                                            │
│            ▼                                            │
│   6. 创建 Pull Request                                   │
│      在 GitHub 上操作                                    │
│            │                                            │
│            ▼                                            │
│   7. 合并后删除分支                                       │
│      git checkout main                                  │
│      git pull                                           │
│      git branch -d feature/xxx                          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 13.2 快速提交流程

```bash
# 修改代码后快速提交
git add .
git commit -m "更新说明"
git push
```

---

## 十四、命令速查表

| 操作 | 命令 |
|------|------|
| 初始化仓库 | `git init` |
| 克隆仓库 | `git clone URL` |
| 查看状态 | `git status` |
| 添加文件 | `git add .` |
| 提交更改 | `git commit -m "msg"` |
| 推送远程 | `git push` |
| 拉取更新 | `git pull` |
| 查看日志 | `git log --oneline` |
| 创建分支 | `git checkout -b 分支名` |
| 切换分支 | `git checkout 分支名` |
| 合并分支 | `git merge 分支名` |
| 暂存工作 | `git stash` |
| 恢复暂存 | `git stash pop` |
| 回退版本 | `git reset --hard 版本号` |
| 查看差异 | `git diff` |

---

**文档版本**：v1.0  
**创建日期**：2026-02-27  
**最后更新**：2026-02-27
