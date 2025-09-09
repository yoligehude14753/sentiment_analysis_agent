# GitHub仓库创建和配置指南

## 🎯 概述
本指南将帮助您在GitHub上创建仓库并配置完整的版本管理系统。

## 📋 准备工作

### 1. 确保Git已安装
```bash
# 检查Git版本
git --version

# 如果未安装，请访问：https://git-scm.com/download
```

### 2. 配置Git用户信息
```bash
# 设置全局用户名和邮箱
git config --global user.name "您的姓名"
git config --global user.email "您的邮箱@example.com"

# 验证配置
git config --list
```

## 🚀 创建GitHub仓库

### 方法1：通过GitHub网站（推荐）

1. **登录GitHub**
   - 访问 [github.com](https://github.com)
   - 使用您的账户登录

2. **创建新仓库**
   - 点击右上角的 "+" 按钮
   - 选择 "New repository"

3. **配置仓库信息**
   ```
   Repository name: sentiment-analysis-agent
   Description: 多Agent情感分析系统 - 基于规则的智能舆情分析平台
   
   ✅ Public (推荐，便于开源协作)
   ❌ 不要勾选 "Add a README file"
   ❌ 不要勾选 "Add .gitignore"
   ❌ 不要勾选 "Choose a license"
   ```
   > 注意：我们已经在本地准备了这些文件，不需要GitHub自动生成

4. **点击 "Create repository"**

### 方法2：使用GitHub CLI

```bash
# 安装GitHub CLI (可选)
# Windows: winget install GitHub.cli
# Mac: brew install gh
# Linux: 参考 https://cli.github.com/

# 登录GitHub
gh auth login

# 创建仓库
gh repo create sentiment-analysis-agent --public --description "多Agent情感分析系统"
```

## 🔗 连接本地仓库到GitHub

### 1. 运行自动化设置脚本

**Windows用户：**
```bash
# 双击运行或在PowerShell中执行
.\setup_git.bat
```

**Linux/Mac用户：**
```bash
# 在终端中执行
./setup_git.sh
```

### 2. 手动设置步骤（如果不使用自动化脚本）

```bash
# 1. 初始化Git仓库
git init

# 2. 添加所有文件
git add .

# 3. 进行初始提交
git commit -m "feat: 初始化多Agent情感分析系统项目"

# 4. 添加远程仓库
git remote add origin https://github.com/您的用户名/sentiment-analysis-agent.git

# 5. 推送到远程仓库
git branch -M main
git push -u origin main

# 6. 创建并推送develop分支
git checkout -b develop
git push -u origin develop
git checkout main
```

## 🌟 GitHub仓库配置优化

### 1. 启用GitHub Pages（可选）
1. 进入仓库设置 (Settings)
2. 滚动到 "Pages" 部分
3. 选择源分支（通常是main分支的docs文件夹）
4. 保存设置

### 2. 配置分支保护规则
1. 进入 Settings → Branches
2. 点击 "Add rule"
3. 配置main分支保护：
   ```
   Branch name pattern: main
   ✅ Require pull request reviews before merging
   ✅ Require status checks to pass before merging
   ✅ Require branches to be up to date before merging
   ✅ Include administrators
   ```

### 3. 设置Issue和PR模板

创建 `.github/ISSUE_TEMPLATE/` 目录结构：
```
.github/
├── ISSUE_TEMPLATE/
│   ├── bug_report.md
│   ├── feature_request.md
│   └── question.md
└── PULL_REQUEST_TEMPLATE.md
```

### 4. 配置仓库标签
建议添加以下标签：
- `bug` (红色) - 程序错误
- `enhancement` (蓝色) - 功能增强
- `documentation` (绿色) - 文档相关
- `good first issue` (紫色) - 适合新手
- `help wanted` (黄色) - 需要帮助
- `priority-high` (橙色) - 高优先级
- `priority-low` (灰色) - 低优先级

## 📊 设置持续集成

项目已包含GitHub Actions配置：
- `.github/workflows/ci.yml` - 持续集成
- `.github/workflows/release.yml` - 自动发布

### 启用Actions
1. 进入仓库的 "Actions" 标签页
2. 如果看到工作流，点击 "Enable" 启用
3. 推送代码后，Actions将自动运行

## 🔐 安全配置

### 1. 启用安全警报
1. 进入 Settings → Security & analysis
2. 启用以下选项：
   - Dependency graph
   - Dependabot alerts
   - Dependabot security updates

### 2. 配置Secrets（如果需要）
如果项目需要API密钥等敏感信息：
1. 进入 Settings → Secrets and variables → Actions
2. 添加必要的secrets

## 👥 协作配置

### 1. 添加协作者
1. 进入 Settings → Manage access
2. 点击 "Invite a collaborator"
3. 输入用户名或邮箱

### 2. 设置团队权限
如果是组织仓库，可以配置团队权限：
- Read：只读访问
- Triage：可以管理issues和PR
- Write：可以推送代码
- Maintain：可以管理仓库设置
- Admin：完全访问权限

## 📈 仓库统计和徽章

在README.md中已添加常用徽章：
- Python版本徽章
- 许可证徽章
- 构建状态徽章

可以添加更多徽章：
```markdown
[![GitHub stars](https://img.shields.io/github/stars/your-username/sentiment-analysis-agent.svg)](https://github.com/your-username/sentiment-analysis-agent/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/your-username/sentiment-analysis-agent.svg)](https://github.com/your-username/sentiment-analysis-agent/network)
[![GitHub issues](https://img.shields.io/github/issues/your-username/sentiment-analysis-agent.svg)](https://github.com/your-username/sentiment-analysis-agent/issues)
```

## 🎉 完成验证

创建完成后，验证以下内容：

1. **仓库内容**
   - [ ] 所有文件已正确上传
   - [ ] README.md显示正常
   - [ ] .gitignore生效

2. **分支结构**
   - [ ] main分支存在
   - [ ] develop分支存在
   - [ ] 分支保护规则已设置

3. **Actions状态**
   - [ ] CI工作流运行正常
   - [ ] 所有检查通过

4. **文档完整性**
   - [ ] 项目介绍清晰
   - [ ] 安装说明详细
   - [ ] 贡献指南完整

## 🚨 常见问题

### 问题1：推送被拒绝
```bash
# 解决方案：先拉取远程更改
git pull origin main --allow-unrelated-histories
git push origin main
```

### 问题2：认证失败
```bash
# 使用Personal Access Token
# 1. GitHub Settings → Developer settings → Personal access tokens
# 2. 生成新token
# 3. 使用token作为密码
```

### 问题3：大文件上传失败
```bash
# 使用Git LFS处理大文件
git lfs install
git lfs track "*.db"
git add .gitattributes
git commit -m "chore: 配置Git LFS"
```

## 📞 获取帮助

如果遇到问题，可以：
1. 查看GitHub官方文档：https://docs.github.com
2. 在项目Issues中提问
3. 参考Git官方文档：https://git-scm.com/doc

---

🎊 恭喜！您已成功设置了完整的GitHub版本管理系统！


