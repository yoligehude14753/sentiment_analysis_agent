// 配置页脚本

async function loadConfig() {
    try {
        const res = await fetch('/api/config');
        const cfg = await res.json();
        if (!res.ok) throw new Error(cfg.detail || '加载配置失败');

        document.getElementById('aliModelName').value = cfg.ALI_MODEL_NAME || '';
        document.getElementById('aliBaseUrl').value = cfg.ALI_BASE_URL || '';
        document.getElementById('host').value = cfg.HOST || '';
        document.getElementById('port').value = cfg.PORT || 8000;
        document.getElementById('debug').value = cfg.DEBUG ? 'true' : 'false';
        document.getElementById('maxContentLength').value = cfg.MAX_CONTENT_LENGTH || 2000;
        document.getElementById('batchSize').value = cfg.BATCH_SIZE || 100;

        // API密钥已在启动时配置，无需在此处处理

        // 加载Agent提示词
        if (cfg.AGENT_PROMPTS) {
            Object.keys(cfg.AGENT_PROMPTS).forEach(tagName => {
                const textarea = document.getElementById(`prompt-${tagName}`);
                if (textarea) {
                    textarea.value = cfg.AGENT_PROMPTS[tagName] || '';
                }
            });
        }
    } catch (e) {
        showMessage(e.message || '加载配置失败');
    }
}

// API密钥相关函数已移除，因为密钥在启动时配置

async function saveConfig() {
    // API密钥已在启动时配置，此处仅保存其他配置
    
    const payload = {
        ALI_MODEL_NAME: document.getElementById('aliModelName').value || undefined,
        ALI_BASE_URL: document.getElementById('aliBaseUrl').value || undefined,
        HOST: document.getElementById('host').value || undefined,
        PORT: document.getElementById('port').value || undefined,
        DEBUG: document.getElementById('debug').value,
        MAX_CONTENT_LENGTH: document.getElementById('maxContentLength').value || undefined,
        BATCH_SIZE: document.getElementById('batchSize').value || undefined,
    };

    try {
        const res = await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await res.json();
        if (!res.ok) throw new Error(result.detail || '保存失败');
        showMessage('配置已更新');
        await loadConfig();
    } catch (e) {
        showMessage(e.message || '保存失败');
    }
}

// API密钥相关函数已移除，因为密钥在启动时配置

function showMessage(msg) {
    const el = document.getElementById('configMessage');
    el.textContent = msg;
    el.classList.remove('hidden');
    setTimeout(() => el.classList.add('hidden'), 3000);
}

document.addEventListener('DOMContentLoaded', () => {
    const backBtn = document.getElementById('backBtn');
    if (backBtn) backBtn.addEventListener('click', () => window.location.href = '/');

    const saveBtn = document.getElementById('saveBtn');
    const reloadBtn = document.getElementById('reloadBtn');
    if (saveBtn) saveBtn.addEventListener('click', saveConfig);
    if (reloadBtn) reloadBtn.addEventListener('click', loadConfig);

    // Agent提示词相关事件监听器
    const toggleAllBtn = document.getElementById('toggleAllAgents');
    const saveAllAgentPromptsBtn = document.getElementById('saveAllAgentPrompts');
    const resetAllAgentPromptsBtn = document.getElementById('resetAllAgentPrompts');

    if (toggleAllBtn) toggleAllBtn.addEventListener('click', toggleAllAgents);
    if (saveAllAgentPromptsBtn) saveAllAgentPromptsBtn.addEventListener('click', saveAllAgentPrompts);
    if (resetAllAgentPromptsBtn) resetAllAgentPromptsBtn.addEventListener('click', resetAllAgentPrompts);

    loadConfig();
});

// Agent提示词相关功能
function toggleAgentPrompt(tagName) {
    const header = document.querySelector(`#content-${tagName}`).previousElementSibling;
    const content = document.getElementById(`content-${tagName}`);
    const icon = header.querySelector('i');
    const toggleText = header.querySelector('.agent-prompt-toggle');

    if (content.classList.contains('expanded')) {
        content.classList.remove('expanded');
        icon.style.transform = 'rotate(0deg)';
        toggleText.textContent = '点击展开';
    } else {
        content.classList.add('expanded');
        icon.style.transform = 'rotate(90deg)';
        toggleText.textContent = '点击折叠';
    }
}

function toggleAllAgents() {
    const allContents = document.querySelectorAll('.agent-prompt-content');
    const allIcons = document.querySelectorAll('.agent-prompt-header i');
    const allToggleTexts = document.querySelectorAll('.agent-prompt-toggle');
    const toggleAllBtn = document.getElementById('toggleAllAgents');
    const icon = toggleAllBtn.querySelector('i');

    const isAllExpanded = Array.from(allContents).every(content => content.classList.contains('expanded'));

    if (isAllExpanded) {
        // 折叠所有
        allContents.forEach(content => content.classList.remove('expanded'));
        allIcons.forEach(icon => icon.style.transform = 'rotate(0deg)');
        allToggleTexts.forEach(text => text.textContent = '点击展开');
        icon.style.transform = 'rotate(0deg)';
    } else {
        // 展开所有
        allContents.forEach(content => content.classList.add('expanded'));
        allIcons.forEach(icon => icon.style.transform = 'rotate(90deg)');
        allToggleTexts.forEach(text => text.textContent = '点击折叠');
        icon.style.transform = 'rotate(180deg)';
    }
}

async function saveSingleAgentPrompt(tagName) {
    const promptValue = document.getElementById(`prompt-${tagName}`).value;
    const payload = {
        AGENT_PROMPTS: {
            [tagName]: promptValue
        }
    };

    try {
        const res = await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await res.json();
        if (!res.ok) throw new Error(result.detail || '保存失败');
        showMessage(`${tagName}提示词已保存`);
    } catch (e) {
        showMessage(e.message || '保存失败');
    }
}

async function saveAllAgentPrompts() {
    const agentPrompts = {};
    const agentNames = [
        '情感分析', '企业识别',
        '同业竞争', '股权与控制权', '关联交易', '历史沿革与股东核查', '重大违法违规',
        '收入与成本', '财务内控不规范', '客户与供应商', '资产质量与减值', '研发与技术',
        '募集资金用途', '突击分红与对赌协议', '市场传闻与负面报道', '行业政策与环境'
    ];

    agentNames.forEach(tagName => {
        const textarea = document.getElementById(`prompt-${tagName}`);
        if (textarea) {
            agentPrompts[tagName] = textarea.value;
        }
    });

    const payload = {
        AGENT_PROMPTS: agentPrompts
    };

    try {
        const res = await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await res.json();
        if (!res.ok) throw new Error(result.detail || '保存失败');
        showMessage('所有Agent提示词已保存');
    } catch (e) {
        showMessage(e.message || '保存失败');
    }
}

async function resetAgentPrompt(tagName) {
    try {
        const res = await fetch('/api/config');
        const cfg = await res.json();
        if (!res.ok) throw new Error(cfg.detail || '获取配置失败');

        const originalPrompt = '';
        document.getElementById(`prompt-${tagName}`).value = originalPrompt;
        showMessage(`${tagName}提示词已重置为默认模板`);
    } catch (e) {
        showMessage(e.message || '重置失败');
    }
}

async function resetAllAgentPrompts() {
    try {
        const res = await fetch('/api/config');
        const cfg = await res.json();
        if (!res.ok) throw new Error(cfg.detail || '获取配置失败');

        const originalPrompt = '';
        const agentNames = [
            '情感分析', '企业识别',
            '同业竞争', '股权与控制权', '关联交易', '历史沿革与股东核查', '重大违法违规',
            '收入与成本', '财务内控不规范', '客户与供应商', '资产质量与减值', '研发与技术',
            '募集资金用途', '突击分红与对赌协议', '市场传闻与负面报道', '行业政策与环境'
        ];

        agentNames.forEach(tagName => {
            const textarea = document.getElementById(`prompt-${tagName}`);
            if (textarea) {
                textarea.value = originalPrompt;
            }
        });

        showMessage('所有Agent提示词已重置为默认模板');
    } catch (e) {
        showMessage(e.message || '重置失败');
    }
}


