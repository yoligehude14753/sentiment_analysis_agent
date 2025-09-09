# Git版本管理设置指南

## 1. 安装Git

### Windows用户
1. 访问 [Git官网](https://git-scm.com/download/win) 下载Git for Windows
2. 运行安装程序，建议使用默认设置
3. 安装完成后重启终端或PowerShell

### 验证安装
```bash
git --version
```

## 2. 配置Git用户信息

```bash
# 设置用户名
git config --global user.name "您的姓名"

# 设置邮箱
git config --global user.email "您的邮箱@example.com"

# 查看配置
git config --list
```

## 3. 初始化本地仓库

在项目根目录执行：
```bash
# 初始化Git仓库
git init

# 添加所有文件到暂存区
git add .

# 进行初始提交
git commit -m "feat: 初始化多Agent情感分析系统项目"
```

## 4. 创建GitHub仓库

### 方法1：通过GitHub网站
1. 登录 [GitHub](https://github.com)
2. 点击右上角的"+"号，选择"New repository"
3. 填写仓库信息：
   - Repository name: `sentiment-analysis-agent`
   - Description: `多Agent情感分析系统 - Multi-Agent Sentiment Analysis System`
   - 选择 Public 或 Private
   - **不要**勾选 "Initialize this repository with a README"
4. 点击"Create repository"

### 方法2：使用GitHub CLI (可选)
```bash
# 安装GitHub CLI后
gh repo create sentiment-analysis-agent --public --description "多Agent情感分析系统"
```

## 5. 连接远程仓库

```bash
# 添加远程仓库
git remote add origin https://github.com/您的用户名/sentiment-analysis-agent.git

# 推送到远程仓库
git branch -M main
git push -u origin main
```

## 6. 分支管理策略

### 推荐的分支结构
```
main          # 主分支，稳定版本
├── develop   # 开发分支，集成新功能
├── feature/* # 功能分支
├── hotfix/*  # 热修复分支
└── release/* # 发布分支
```

### 创建开发分支
```bash
# 创建并切换到开发分支
git checkout -b develop

# 推送开发分支到远程
git push -u origin develop
```

## 7. 常用Git命令

### 日常开发流程
```bash
# 查看状态
git status

# 添加文件
git add 文件名
git add .  # 添加所有文件

# 提交更改
git commit -m "feat: 添加新功能"

# 推送到远程
git push

# 拉取最新代码
git pull
```

### 分支操作
```bash
# 查看所有分支
git branch -a

# 创建新分支
git checkout -b feature/new-feature

# 切换分支
git checkout branch-name

# 合并分支
git merge branch-name

# 删除分支
git branch -d branch-name
```

## 8. 提交信息规范

使用约定式提交格式：
```
<类型>[可选的作用域]: <描述>

[可选的正文]

[可选的脚注]
```

### 常用类型
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式化
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

### 示例
```bash
git commit -m "feat: 添加企业识别Agent功能"
git commit -m "fix: 修复情感分析评分算法bug"
git commit -m "docs: 更新API文档说明"
```

## 9. 文件忽略说明

项目已配置 `.gitignore` 文件，自动忽略：
- Python缓存文件 (`__pycache__/`, `*.pyc`)
- 数据库文件 (`*.db`, `*.sqlite3`)
- 大型数据文件 (`data/*.csv`, `exports/*`)
- 环境配置文件 (`.env`)
- IDE配置文件 (`.vscode/`, `.idea/`)
- 临时文件和日志文件

## 10. 协作开发建议

### Pull Request流程
1. 从 `develop` 分支创建功能分支
2. 开发完成后推送到远程
3. 在GitHub上创建Pull Request
4. 代码审查后合并到 `develop` 分支

### 版本发布流程
1. 从 `develop` 创建 `release/v1.0.0` 分支
2. 进行最终测试和修复
3. 合并到 `main` 分支并打标签
4. 合并回 `develop` 分支

## 故障排除

### 常见问题
1. **推送被拒绝**：先执行 `git pull` 拉取最新代码
2. **合并冲突**：手动解决冲突后提交
3. **忘记提交信息**：使用 `git commit --amend` 修改最后一次提交

### 撤销操作
```bash
# 撤销工作区修改
git checkout -- 文件名

# 撤销暂存区修改
git reset HEAD 文件名

# 撤销最后一次提交
git reset --soft HEAD~1
```

## 下一步

完成Git设置后，建议：
1. 设置持续集成（CI/CD）
2. 配置代码质量检查工具
3. 建立代码审查流程
4. 定期备份重要分支


