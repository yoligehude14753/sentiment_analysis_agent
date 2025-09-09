# Git版本管理使用指南

## 🎯 概述

本项目已经设置了完整的Git版本管理系统，包含以下特性：
- ✅ 本地Git仓库已初始化
- ✅ 完整的.gitignore配置
- ✅ 第一次提交已完成
- ✅ 自动化部署脚本

## 📁 当前状态

```bash
# 查看当前状态
git status

# 查看提交历史
git log --oneline

# 查看分支
git branch
```

## 🚀 上传到GitHub仓库

### 方法1：使用自动化脚本（推荐）

**Windows用户：**
```cmd
setup_github_repo.bat
```

**Linux/Mac用户：**
```bash
./setup_github_repo.sh
```

### 方法2：手动设置

1. **在GitHub创建新仓库**
   - 访问：https://github.com/new
   - 仓库名：`sentiment-analysis-agent`
   - 描述：`智能情感分析代理系统 - 基于阿里云通义千问的多功能文本分析平台`
   - 不要初始化README、.gitignore或LICENSE

2. **添加远程仓库**
   ```bash
   git remote add origin https://github.com/yourusername/sentiment-analysis-agent.git
   ```

3. **推送到GitHub**
   ```bash
   git branch -M main
   git push -u origin main
   ```

## 📝 日常Git操作

### 基本工作流程

1. **查看当前状态**
   ```bash
   git status
   ```

2. **添加文件到暂存区**
   ```bash
   # 添加所有文件
   git add .
   
   # 添加特定文件
   git add filename.py
   
   # 添加特定目录
   git add agents/
   ```

3. **提交更改**
   ```bash
   git commit -m "描述性的提交信息"
   ```

4. **推送到远程仓库**
   ```bash
   git push
   ```

### 常用提交信息格式

```bash
# 功能开发
git commit -m "feat: 添加新的情感分析功能"

# Bug修复
git commit -m "fix: 修复数据库连接问题"

# 文档更新
git commit -m "docs: 更新API文档"

# 性能优化
git commit -m "perf: 优化批处理性能"

# 重构代码
git commit -m "refactor: 重构数据处理模块"

# 配置更新
git commit -m "config: 更新部署配置"
```

## 🌿 分支管理

### 创建和切换分支

```bash
# 创建新分支
git branch feature/new-analysis

# 切换分支
git checkout feature/new-analysis

# 创建并切换到新分支
git checkout -b feature/new-analysis
```

### 合并分支

```bash
# 切换到主分支
git checkout main

# 合并功能分支
git merge feature/new-analysis

# 删除已合并的分支
git branch -d feature/new-analysis
```

## 🔄 同步远程更改

```bash
# 拉取远程更改
git pull origin main

# 查看远程仓库信息
git remote -v

# 获取远程分支信息
git fetch origin
```

## 📊 查看历史和差异

```bash
# 查看提交历史
git log --oneline --graph

# 查看文件差异
git diff filename.py

# 查看暂存区差异
git diff --cached

# 查看两个提交之间的差异
git diff commit1..commit2
```

## 🛠️ 撤销操作

```bash
# 撤销工作区更改
git checkout -- filename.py

# 撤销暂存区更改
git reset HEAD filename.py

# 撤销最后一次提交（保留更改）
git reset --soft HEAD~1

# 撤销最后一次提交（丢弃更改）
git reset --hard HEAD~1
```

## 🏷️ 标签管理

```bash
# 创建标签
git tag v1.0.0

# 创建带注释的标签
git tag -a v1.0.0 -m "版本1.0.0发布"

# 推送标签
git push origin v1.0.0

# 推送所有标签
git push origin --tags

# 查看所有标签
git tag
```

## 🔍 忽略文件配置

项目已配置完整的`.gitignore`文件，包括：

```gitignore
# Python相关
__pycache__/
*.pyc
*.pyo
venv/

# 数据库文件
*.db
*.sqlite3

# 环境变量
.env

# 日志文件
*.log

# 临时文件
*.tmp
temp/

# IDE文件
.vscode/
.idea/
```

## 🚨 常见问题解决

### 1. 推送失败（需要身份验证）

```bash
# 使用Personal Access Token
git remote set-url origin https://username:token@github.com/username/repo.git
```

### 2. 合并冲突

```bash
# 查看冲突文件
git status

# 手动解决冲突后
git add conflicted-file.py
git commit -m "resolve merge conflict"
```

### 3. 误提交大文件

```bash
# 从历史中移除文件
git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch large-file.db' --prune-empty --tag-name-filter cat -- --all
```

## 📋 最佳实践

1. **提交频率**：小而频繁的提交比大而少的提交更好
2. **提交信息**：使用清晰、描述性的提交信息
3. **分支策略**：为每个功能或修复创建单独的分支
4. **代码审查**：使用Pull Request进行代码审查
5. **定期同步**：定期从远程仓库拉取更新

## 🔗 相关链接

- [Git官方文档](https://git-scm.com/doc)
- [GitHub使用指南](https://docs.github.com/)
- [项目部署指南](deploy_guide.md)
- [贡献指南](CONTRIBUTING.md)

---

**注意**：首次推送到GitHub时，可能需要设置GitHub身份验证。建议使用Personal Access Token进行身份验证。 