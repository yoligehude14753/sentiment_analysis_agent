# 贡献指南

感谢您对多Agent情感分析系统的关注！我们欢迎各种形式的贡献，包括但不限于：

## 🤝 如何贡献

### 1. 报告问题
- 使用 [GitHub Issues](https://github.com/your-username/sentiment-analysis-agent/issues) 报告bug
- 提供详细的问题描述、复现步骤和环境信息
- 如果可能，请提供错误日志和截图

### 2. 提出功能建议
- 在 [GitHub Discussions](https://github.com/your-username/sentiment-analysis-agent/discussions) 中讨论新功能
- 详细描述功能需求和使用场景
- 说明该功能如何改善用户体验

### 3. 代码贡献

#### 开发环境设置
```bash
# 1. Fork 并克隆项目
git clone https://github.com/your-username/sentiment-analysis-agent.git
cd sentiment-analysis-agent

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 开发依赖

# 4. 创建功能分支
git checkout -b feature/your-feature-name
```

#### 代码规范
- 使用 Python PEP 8 代码风格
- 添加适当的类型提示
- 编写清晰的文档字符串
- 保持函数简洁，单一职责
- 添加必要的单元测试

#### 提交规范
使用约定式提交格式：
```
<类型>[可选作用域]: <描述>

[可选正文]

[可选脚注]
```

**类型说明：**
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式化（不影响功能）
- `refactor`: 代码重构
- `test`: 添加或修改测试
- `chore`: 构建过程或辅助工具的变动

**示例：**
```bash
git commit -m "feat(agents): 添加企业信用代码验证功能"
git commit -m "fix(sentiment): 修复情感评分计算错误"
git commit -m "docs: 更新API使用说明"
```

#### Pull Request流程
1. 确保代码通过所有测试
2. 更新相关文档
3. 提交Pull Request到 `develop` 分支
4. 填写PR模板，详细描述更改内容
5. 等待代码审查和反馈
6. 根据反馈修改代码
7. 合并后删除功能分支

## 🧪 测试指南

### 运行测试
```bash
# 运行所有测试
python -m pytest

# 运行特定测试
python -m pytest tests/test_agents.py

# 生成覆盖率报告
python -m pytest --cov=agents tests/
```

### 测试要求
- 新功能必须包含单元测试
- 测试覆盖率应保持在80%以上
- 集成测试确保系统整体功能正常

## 📝 文档贡献

### 文档类型
- API文档：详细的接口说明
- 使用指南：用户操作手册
- 开发文档：技术实现细节
- 示例代码：使用场景演示

### 文档规范
- 使用清晰的中文表达
- 提供代码示例
- 包含必要的图表说明
- 保持文档与代码同步更新

## 🏷️ 标签系统

我们使用以下标签分类Issues和PRs：

### Issue标签
- `bug`: 程序错误
- `enhancement`: 功能增强
- `documentation`: 文档相关
- `good first issue`: 适合新手
- `help wanted`: 需要帮助
- `priority-high`: 高优先级
- `priority-low`: 低优先级

### PR标签
- `feature`: 新功能
- `bugfix`: 错误修复
- `docs`: 文档更新
- `refactor`: 代码重构
- `breaking-change`: 破坏性变更

## 🎯 开发优先级

### 高优先级任务
1. 核心功能bug修复
2. 性能优化
3. 安全漏洞修复
4. 关键文档更新

### 中优先级任务
1. 新功能开发
2. 用户体验改进
3. 代码重构
4. 测试覆盖率提升

### 低优先级任务
1. 代码风格优化
2. 文档美化
3. 示例代码完善
4. 非关键功能增强

## 🔍 代码审查清单

### 功能性检查
- [ ] 功能是否按预期工作
- [ ] 是否处理了边界情况
- [ ] 错误处理是否完善
- [ ] 性能是否可接受

### 代码质量检查
- [ ] 代码风格是否符合规范
- [ ] 变量命名是否清晰
- [ ] 函数是否单一职责
- [ ] 是否有重复代码

### 文档检查
- [ ] 是否更新了相关文档
- [ ] 代码注释是否充分
- [ ] API文档是否准确
- [ ] 示例代码是否正确

## 💡 最佳实践

### 开发建议
1. **小步快跑**：将大功能拆分为小的PR
2. **测试驱动**：先写测试，再实现功能
3. **及时沟通**：有疑问及时在Issue中讨论
4. **持续学习**：关注项目最新动态和技术发展

### 协作建议
1. **尊重他人**：友善对待每一个贡献者
2. **建设性反馈**：提供具体、可操作的建议
3. **耐心指导**：帮助新手快速上手
4. **知识分享**：分享经验和最佳实践

## 📞 联系方式

如有任何问题，欢迎通过以下方式联系我们：
- GitHub Issues: 报告bug和功能请求
- GitHub Discussions: 技术讨论和交流
- 邮箱: [项目邮箱]

## 🙏 致谢

感谢每一位贡献者的付出！您的贡献让这个项目变得更好。

---

再次感谢您的贡献！让我们一起打造更好的多Agent情感分析系统！


