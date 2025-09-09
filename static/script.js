// 舆情分析系统前端脚本

// 全局变量
let currentSessionId = null; // 当前批量解析的会话ID
let currentResults = []; // 当前搜索结果数据，供聊天功能使用

// 主要元素
let contentTextarea, analyzeBtn, clearBtn, csvFileInput, uploadBtn, refreshStatsBtn;

// 加载和进度元素
let loadingDiv, progressDiv, progressListDiv, resultsDiv, errorDiv, errorMessage;

// 结果元素
let summaryElement, companiesElement, tagsElement, levelElement, reasonElement;

// 重复度分析元素
let duplicateStatusElement, similarityScoreElement, hammingDistanceElement, simhashValueElement, duplicateGroupElement;

// 去重统计元素
let totalTextsElement, uniqueTextsElement, duplicateTextsElement, duplicationRateElement, batchResultsElement, batchListElement;

// 模态框元素
let tagModal, modalTitle, modalTagName, modalTagStatus, modalTagReason, closeModal;
let sentimentModal, sentimentModalTitle, modalSentimentLevel, modalLevelDescription, modalSentimentReason, closeSentimentModalBtn;

// 初始化DOM元素
function initializeDOMElements() {
    // 主要元素
    contentTextarea = document.getElementById('content');
    analyzeBtn = document.getElementById('analyzeBtn');
    clearBtn = document.getElementById('clearBtn');
    csvFileInput = document.getElementById('csvFile');
    uploadBtn = document.getElementById('uploadBtn');
    refreshStatsBtn = document.getElementById('refreshStatsBtn');

    // 加载和进度元素
    loadingDiv = document.getElementById('loading');
    progressDiv = document.getElementById('progress');
    progressListDiv = document.getElementById('progressList');
    resultsDiv = document.getElementById('results');
    errorDiv = document.getElementById('error');
    errorMessage = document.getElementById('errorMessage');

    // 结果元素
    summaryElement = document.getElementById('summary');
    companiesElement = document.getElementById('companies');
    tagsElement = document.getElementById('tags');
    levelElement = document.getElementById('level');
    reasonElement = document.getElementById('reason');

    // 重复度分析元素
    duplicateStatusElement = document.getElementById('duplicateStatus');
    similarityScoreElement = document.getElementById('similarityScore');
    hammingDistanceElement = document.getElementById('hammingDistance');
    simhashValueElement = document.getElementById('simhashValue');
    duplicateGroupElement = document.getElementById('duplicateGroup');

    // 去重统计元素
    totalTextsElement = document.getElementById('totalTexts');
    uniqueTextsElement = document.getElementById('uniqueTexts');
    duplicateTextsElement = document.getElementById('duplicateTexts');
    duplicationRateElement = document.getElementById('duplicationRate');
    batchResultsElement = document.getElementById('batchResults');
    batchListElement = document.getElementById('batchList');

    // 模态框元素
    tagModal = document.getElementById('tagModal');
    modalTitle = document.getElementById('modalTitle');
    modalTagName = document.getElementById('modalTagName');
    modalTagStatus = document.getElementById('modalTagStatus');
    modalTagReason = document.getElementById('modalTagReason');
    closeModal = document.getElementById('closeModal');

    // 情感等级模态框元素
    sentimentModal = document.getElementById('sentimentModal');
    sentimentModalTitle = document.getElementById('sentimentModalTitle');
    modalSentimentLevel = document.getElementById('modalSentimentLevel');
    modalLevelDescription = document.getElementById('modalLevelDescription');
    modalSentimentReason = document.getElementById('modalSentimentReason');
    closeSentimentModalBtn = document.getElementById('closeSentimentModal');
    
    console.log('DOM元素初始化完成');
}

// 初始化页面导航
function initializePageNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const pages = document.querySelectorAll('.page-content');
    
    navItems.forEach(item => {
        item.addEventListener('click', function() {
            const targetPage = this.getAttribute('data-page');
            
            // 隐藏所有页面
            pages.forEach(page => page.classList.add('hidden'));
            
            // 显示目标页面
            const targetElement = document.getElementById(targetPage);
            if (targetElement) {
                targetElement.classList.remove('hidden');
            }
            
            // 更新导航状态
            navItems.forEach(nav => nav.classList.remove('active'));
            this.classList.add('active');
        });
    });
    
    // 默认显示第一个页面
    if (pages.length > 0) {
        pages[0].classList.remove('hidden');
        if (navItems.length > 0) {
            navItems[0].classList.add('active');
        }
    }
}

// 初始化数据库配置
function initializeDatabaseConfig() {
    // 数据库配置相关的初始化逻辑
    console.log('数据库配置初始化完成');
}

// 关闭标签模态框
function closeTagModal() {
    if (tagModal) {
        tagModal.classList.add('hidden');
    }
}

// 关闭情感等级模态框
function closeSentimentModal() {
    if (sentimentModal) {
        sentimentModal.classList.add('hidden');
    }
}

// 页面切换功能
document.addEventListener('DOMContentLoaded', function() {
    // 初始化页面切换
    initializePageNavigation();

    // 初始化DOM元素
    initializeDOMElements();

    // 分析按钮点击事件
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', analyzeSingleText);
    }

    // 清空按钮点击事件
    if (clearBtn) {
        clearBtn.addEventListener('click', clearContent);
    }

    // 上传按钮点击事件
    if (uploadBtn) {
        uploadBtn.addEventListener('click', uploadCSVFile);
    }

    // 刷新统计按钮点击事件
    if (refreshStatsBtn) {
        refreshStatsBtn.addEventListener('click', refreshDuplicateStats);
    }

    // 主页搜索功能
    initializeSearchFunctionality();

    // 模态框关闭事件
    if (closeModal) {
        closeModal.addEventListener('click', closeTagModal);
    }

    // 点击模态框外部关闭
    if (tagModal) {
        tagModal.addEventListener('click', function(e) {
            if (e.target === tagModal) {
                closeTagModal();
            }
        });
    }

    // 情感等级模态框关闭事件
    if (closeSentimentModalBtn) {
        closeSentimentModalBtn.addEventListener('click', function() {
            closeSentimentModal();
        });
    }
    
    // 点击情感等级模态框外部关闭
    if (sentimentModal) {
        sentimentModal.addEventListener('click', function(e) {
            if (e.target === sentimentModal) {
                closeSentimentModal();
            }
        });
    }
    
    // ESC键关闭模态框
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            if (tagModal && !tagModal.classList.contains('hidden')) {
                closeTagModal();
            }
            if (sentimentModal && !sentimentModal.classList.contains('hidden')) {
                closeSentimentModal();
            }
        }
    });
    
    // 导出按钮点击事件
    const exportBtn = document.getElementById('exportBtn');
    if (exportBtn) {
        exportBtn.addEventListener('click', function() {
            const exportModal = document.getElementById('exportModal');
            if (exportModal) {
                exportModal.classList.remove('hidden');
            }
        });
    }

    // 确认导出按钮点击事件
    const confirmExportBtn = document.getElementById('confirmExportBtn');
    if (confirmExportBtn) {
        confirmExportBtn.addEventListener('click', exportResults);
    }

    // 取消导出按钮点击事件
    const cancelExportBtn = document.getElementById('cancelExportBtn');
    if (cancelExportBtn) {
        cancelExportBtn.addEventListener('click', function() {
            const exportModal = document.getElementById('exportModal');
            if (exportModal) {
                exportModal.classList.add('hidden');
            }
        });
    }
});

// 初始化搜索功能
function initializeSearchFunctionality() {
    // 获取搜索相关的DOM元素
    const searchBtn = document.querySelector('.search-box .btn-primary');
    const searchInput = document.querySelector('.search-input');
    const sentimentFilter = document.querySelector('.advanced-search select:nth-child(1)');
    const tagFilter = document.querySelector('.advanced-search select:nth-child(2)');
    const dateFilter = document.querySelector('.advanced-search select:nth-child(3)');

    // 搜索按钮点击事件
    if (searchBtn) {
        searchBtn.addEventListener('click', () => searchResults(1));
    }

    // 筛选器变化事件
    if (sentimentFilter) {
        sentimentFilter.addEventListener('change', () => searchResults(1));
    }
    if (tagFilter) {
        tagFilter.addEventListener('change', () => searchResults(1));
    }
    if (dateFilter) {
        dateFilter.addEventListener('change', () => searchResults(1));
    }

    // 回车键搜索
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchResults(1);
            }
        });
    }

    // 首次进入页面自动拉取数据
    try { 
        searchResults(1); 
    } catch (e) { 
        console.log('初始化搜索失败:', e);
    }
}

// 搜索结果函数
async function searchResults(page = 1) {
    try {
        const searchInput = document.querySelector('.search-input');
        const sentimentFilter = document.querySelector('.advanced-search select:nth-child(1)');
        const tagFilter = document.querySelector('.advanced-search select:nth-child(2)');
        const dateFilter = document.querySelector('.advanced-search select:nth-child(3)');

        // 构建搜索参数
        const searchParams = new URLSearchParams();
        searchParams.append('page', page);
        searchParams.append('page_size', 20);

        if (searchInput && searchInput.value.trim()) {
            searchParams.append('search', searchInput.value.trim());
        }

        if (sentimentFilter && sentimentFilter.value && sentimentFilter.value !== '全部') {
            searchParams.append('sentiment', sentimentFilter.value);
        }

        if (tagFilter && tagFilter.value && tagFilter.value !== '全部') {
            searchParams.append('tags', tagFilter.value);
        }

        if (dateFilter && dateFilter.value && dateFilter.value !== '全部') {
            const now = new Date();
            let startDate = null;

            switch (dateFilter.value) {
                case '最近1天':
                    startDate = new Date(now.getTime() - 24 * 60 * 60 * 1000);
                    break;
                case '最近7天':
                    startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                    break;
                case '最近30天':
                    startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
                    break;
            }

            if (startDate) {
                searchParams.append('start_date', startDate.toISOString().split('T')[0]);
                searchParams.append('end_date', now.toISOString().split('T')[0]);
            }
        }

        // 显示加载状态
        showSearchLoading();

        // 发送搜索API请求
        const response = await fetch(`/api/analysis_results?${searchParams.toString()}`);
        const data = await response.json();

        if (response.ok && data.success) {
            displaySearchResults(data);
        } else {
            displaySearchError(data.detail || '搜索失败');
        }
    } catch (error) {
        console.error('搜索错误:', error);
        displaySearchError('网络错误，请稍后重试');
    }
}

// 显示搜索结果
function displaySearchResults(data) {
    const searchResults = document.getElementById('searchResults');
    if (!searchResults) return;

    // 清空结果
    searchResults.innerHTML = '';

    // 更新统计信息
    const resultCount = document.getElementById('resultCount');
    if (resultCount) resultCount.textContent = data.total || 0;
    
    const searchTime = document.getElementById('searchTime');
    if (searchTime) searchTime.textContent = data.search_time || '0.00';

    // 保存搜索结果到全局变量，供聊天功能使用
    if (data.data && data.data.length > 0) {
        currentResults = data.data;
        window.currentResults = data.data;
        
        // 显示结果
        data.data.forEach(result => {
            const resultRow = createSearchResultRow(result);
            searchResults.appendChild(resultRow);
        });
        
        // 在聊天界面显示搜索结果更新提示
        showSearchResultsUpdate(data.data.length);
    } else {
        currentResults = [];
        window.currentResults = [];
        searchResults.innerHTML = '<div class="no-results">未找到匹配的结果</div>';
    }
}

// 创建搜索结果行
function createSearchResultRow(result) {
    const row = document.createElement('div');
    row.className = 'search-result-row';
    row.onclick = () => showArticleDetail(result);

    const publishTime = result.publish_time ? new Date(result.publish_time).toLocaleDateString('zh-CN') : '未知';

    // 处理标签 - 直接从API返回的标签字段中提取
    const tags = [];
    const tagNames = [
        '同业竞争', '股权与控制权', '关联交易', '历史沿革与股东核查', '重大违法违规',
        '收入与成本', '财务内控不规范', '客户与供应商', '资产质量与减值', '研发与技术',
        '募集资金用途', '突击分红与对赌协议', '市场传闻与负面报道', '行业政策与环境'
    ];
    
    // 从API返回的标签字段中提取标签
    for (const tagName of tagNames) {
        const tagKey = `tag_${tagName}`;
        if (result[tagKey] === '是') {
            tags.push(tagName);
        }
    }

    const tagsHtml = tags.length > 0 ?
        tags.map(tag => `<span class="tag-item clickable-tag" onclick="showTagDetail('${tag}', event)">${tag}</span>`).join('') :
        '<span class="no-tags">无标签</span>';

    // 处理公司 - 直接从API返回的companies字段获取
    let companies = [];
    if (result.companies && typeof result.companies === 'string') {
        if (result.companies !== '无' && result.companies.trim()) {
            companies = result.companies.split(',').map(c => c.trim()).filter(Boolean);
        }
    } else if (Array.isArray(result.companies)) {
        companies = result.companies;
    }

    const companiesHtml = companies.length > 0 ?
        companies.slice(0, 1).map(company => `<span class="company">${company}</span>`).join('') :
        '<span class="no-company">无相关公司</span>';

    // 处理情感分析结果 - 直接从API返回的字段获取
    const sentimentLevel = result.sentiment_level || '未知';
    const sentimentReason = result.sentiment_reason || '';

    row.innerHTML = `
        <div class="result-header">
            <h3 class="result-title">${result.title || '无标题'}</h3>
            <span class="sentiment-level clickable-sentiment" onclick="showSentimentDetail('${sentimentLevel}', '${sentimentReason}', event)">
                ${sentimentLevel}
            </span>
            <span class="result-time">${publishTime}</span>
        </div>
        <div class="result-content">
            <p class="result-summary">${result.summary || '无摘要'}</p>
            <div class="result-meta">
                <div class="result-tags">${tagsHtml}</div>
                <div class="result-companies">${companiesHtml}</div>
            </div>
        </div>
    `;

    // 为标题添加点击事件，确保可以跳转
    const titleElement = row.querySelector('.result-title');
    if (titleElement) {
        titleElement.style.cursor = 'pointer';
        titleElement.addEventListener('click', (event) => {
            event.stopPropagation(); // 阻止事件冒泡到整个row
            showArticleDetail(result);
        });
    }

    return row;
}

// 显示文章详情
function showArticleDetail(result) {
    const articleDetail = document.getElementById('articleDetail');
    if (!articleDetail) return;

    // 处理标签 - 直接从API返回的标签字段中提取
    const tags = [];
    const tagNames = [
        '同业竞争', '股权与控制权', '关联交易', '历史沿革与股东核查', '重大违法违规',
        '收入与成本', '财务内控不规范', '客户与供应商', '资产质量与减值', '研发与技术',
        '募集资金用途', '突击分红与对赌协议', '市场传闻与负面报道', '行业政策与环境'
    ];
    
    // 从API返回的标签字段中提取标签
    for (const tagName of tagNames) {
        const tagKey = `tag_${tagName}`;
        if (result[tagKey] === '是') {
            tags.push(tagName);
        }
    }

    // 处理公司 - 直接从API返回的companies字段获取
    let companies = [];
    if (result.companies && typeof result.companies === 'string') {
        if (result.companies !== '无' && result.companies.trim()) {
            companies = result.companies.split(',').map(c => c.trim()).filter(Boolean);
        }
    } else if (Array.isArray(result.companies)) {
        companies = result.companies;
    }

    // 处理情感分析结果 - 直接从API返回的字段获取
    const sentimentLevel = result.sentiment_level || '未知';
    const sentimentReason = result.sentiment_reason || '';

    articleDetail.innerHTML = `
        <div class="article-content">
            <h2>${result.title || '无标题'}</h2>
            <div class="article-meta">
                <span class="publish-time">发布时间: ${result.publish_time ? new Date(result.publish_time).toLocaleString('zh-CN') : '未知'}</span>
                <span class="sentiment-level">情感等级: ${sentimentLevel}</span>
            </div>
            <div class="article-summary">
                <h3>摘要</h3>
                <p>${result.summary || '无摘要'}</p>
            </div>
            <div class="article-tags">
                <h3>标签</h3>
                <div class="tags-container">
                    ${tags.length > 0 ? 
                        tags.map(tag => `<span class="tag">${tag}</span>`).join('') : 
                        '<span class="no-tags">无标签</span>'
                    }
                </div>
            </div>
            <div class="article-companies">
                <h3>相关公司</h3>
                <div class="companies-container">
                    ${companies.length > 0 ? 
                        companies.map(company => `<span class="company">${company}</span>`).join('') : 
                        '<span class="no-companies">无相关公司</span>'
                    }
                </div>
            </div>
            ${sentimentReason ? `
            <div class="article-sentiment-reason">
                <h3>情感分析原因</h3>
                <p>${sentimentReason}</p>
            </div>
            ` : ''}
        </div>
    `;
}

// 显示搜索加载状态
function showSearchLoading() {
    const searchResults = document.getElementById('searchResults');
    if (searchResults) {
        searchResults.innerHTML = '<div class="loading"><div class="spinner"></div><p>搜索中...</p></div>';
    }
}

// 显示搜索错误
function displaySearchError(message) {
    const searchResults = document.getElementById('searchResults');
    if (searchResults) {
        searchResults.innerHTML = `<div class="error"><i class="fas fa-exclamation-triangle"></i><p>${message}</p></div>`;
    }
}

// 占位函数 - 这些函数在其他地方实现
function analyzeSingleText() {
    console.log('分析单条文本功能待实现');
}

function clearContent() {
    console.log('清空内容功能待实现');
}

function uploadCSVFile() {
    console.log('上传CSV文件功能待实现');
}

function refreshDuplicateStats() {
    console.log('刷新重复统计功能待实现');
}

function exportResults() {
    console.log('导出结果功能待实现');
}

// 显示标签详情
function showTagDetail(tagName, event) {
    event.stopPropagation(); // 阻止事件冒泡，避免触发文章详情
    
    // 创建标签详情模态框
    const modal = document.createElement('div');
    modal.className = 'tag-detail-modal';
    modal.innerHTML = `
        <div class="tag-detail-content">
            <div class="tag-detail-header">
                <h3>标签详情：${tagName}</h3>
                <span class="close-tag-modal" onclick="this.parentElement.parentElement.parentElement.remove()">&times;</span>
            </div>
            <div class="tag-detail-body">
                <div class="tag-description">
                    <h4>标签说明：</h4>
                    <p>${getTagDescription(tagName)}</p>
                </div>
                <div class="tag-criteria">
                    <h4>识别标准：</h4>
                    <p>${getTagCriteria(tagName)}</p>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // 添加点击外部关闭功能
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.remove();
        }
    });
}

// 显示情感分析详情
function showSentimentDetail(level, reason, event) {
    event.stopPropagation(); // 阻止事件冒泡，避免触发文章详情
    
    // 创建情感分析详情模态框
    const modal = document.createElement('div');
    modal.className = 'sentiment-detail-modal';
    modal.innerHTML = `
        <div class="sentiment-detail-content">
            <div class="sentiment-detail-header">
                <h3>情感分析详情</h3>
                <span class="close-sentiment-modal" onclick="this.parentElement.parentElement.parentElement.remove()">&times;</span>
            </div>
            <div class="sentiment-detail-body">
                <div class="sentiment-level-info">
                    <h4>情感等级：${level}</h4>
                    <p>${getSentimentLevelDescription(level)}</p>
                </div>
                <div class="sentiment-reason">
                    <h4>分析原因：</h4>
                    <p>${reason || '暂无详细分析原因'}</p>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // 添加点击外部关闭功能
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.remove();
        }
    });
}

// 获取标签描述
function getTagDescription(tagName) {
    const descriptions = {
        '同业竞争': '指公司与同行业其他企业之间存在直接或间接的竞争关系，可能影响公司的市场份额和盈利能力。',
        '股权与控制权': '涉及公司股权结构、股东权益、控制权变更等事项，可能影响公司治理和经营稳定性。',
        '关联交易': '公司与关联方之间的交易行为，需要关注交易的公允性和必要性。',
        '历史沿革与股东核查': '公司历史发展过程中的重要事件和股东变更情况，可能影响公司信誉和合规性。',
        '重大违法违规': '公司或其相关人员存在重大违法违规行为，可能面临法律风险和处罚。',
        '收入与成本': '公司收入确认和成本核算的规范性，可能影响财务数据的真实性。',
        '财务内控不规范': '公司财务内部控制制度不完善或执行不到位，可能增加财务风险。',
        '客户与供应商': '公司与主要客户和供应商的关系稳定性，可能影响经营持续性。',
        '资产质量与减值': '公司资产质量状况和减值计提的合理性，可能影响资产价值评估。',
        '研发与技术': '公司研发投入和技术创新能力，可能影响未来发展潜力。',
        '募集资金用途': '公司募集资金的使用合规性和效率性，可能影响资金使用效果。',
        '突击分红与对赌协议': '公司突击分红行为或存在对赌协议，可能影响股东权益和公司稳定性。',
        '市场传闻与负面报道': '市场上关于公司的传闻或负面媒体报道，可能影响公司声誉和股价。',
        '行业政策与环境': '行业政策变化和外部环境变化对公司经营的影响，可能增加经营风险。'
    };
    return descriptions[tagName] || '该标签暂无详细说明。';
}

// 获取标签识别标准
function getTagCriteria(tagName) {
    const criteria = {
        '同业竞争': '通过分析公司业务范围、市场份额、竞争对手信息等，识别是否存在同业竞争关系。',
        '股权与控制权': '分析公司股权结构、股东背景、控制权变更历史等，评估控制权稳定性。',
        '关联交易': '识别公司与股东、实际控制人、关联企业之间的交易，评估交易的必要性和公允性。',
        '历史沿革与股东核查': '梳理公司发展历史、股东变更记录、重要事件等，评估公司发展稳定性。',
        '重大违法违规': '通过公开信息查询、媒体报道等，识别公司是否存在违法违规行为。',
        '收入与成本': '分析公司收入确认政策、成本核算方法、财务数据一致性等，评估财务真实性。',
        '财务内控不规范': '评估公司财务内部控制制度的完善程度和执行效果，识别内控缺陷。',
        '客户与供应商': '分析公司主要客户和供应商的稳定性、集中度、信用状况等，评估经营风险。',
        '资产质量与减值': '评估公司资产质量、减值计提的合理性、资产价值等，识别资产风险。',
        '研发与技术': '分析公司研发投入、技术储备、创新能力等，评估技术发展潜力。',
        '募集资金用途': '评估募集资金使用的合规性、效率性、项目进展等，识别资金使用风险。',
        '突击分红与对赌协议': '识别公司突击分红行为、对赌协议条款等，评估股东权益风险。',
        '市场传闻与负面报道': '监控市场传闻、媒体报道等，识别声誉风险和舆情风险。',
        '行业政策与环境': '分析行业政策变化、外部环境变化等，评估政策风险和经营风险。'
    };
    return criteria[tagName] || '该标签暂无识别标准说明。';
}

// 获取情感等级描述
function getSentimentLevelDescription(level) {
    const descriptions = {
        '正面': '内容整体呈现积极、正面的情感倾向，对公司或行业有利。',
        '中性': '内容情感倾向不明显，保持客观中立的表述。',
        '负面一级': '内容存在轻微的负面情感，但影响程度较低。',
        '负面二级': '内容存在明显的负面情感，可能对公司或行业产生一定影响。',
        '负面三级': '内容存在严重的负面情感，可能对公司或行业产生重大影响。',
        '未知': '无法确定内容的情感倾向，需要进一步分析。'
    };
    return descriptions[level] || '该情感等级暂无详细说明。';
}

// ===== 聊天功能相关代码 =====

// 聊天相关全局变量
let chatHistory = [];
let currentKnowledgeBase = {
    title: true,
    content: true,
    tags: true,
    sentiment: true,
    companies: true,
    date: true
};

// 切换知识库设置面板
function toggleKnowledgeBase() {
    const panel = document.getElementById('knowledgeBasePanel');
    if (panel) {
        panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
    }
}

// 清空聊天记录
function clearChat() {
    chatHistory = [];
    const chatMessages = document.getElementById('chatMessages');
    if (chatMessages) {
        chatMessages.innerHTML = `
            <div class="welcome-message">
                <div class="message ai-message">
                    <div class="message-avatar">
                        <i class="fas fa-robot"></i>
                    </div>
                    <div class="message-content">
                        <div class="message-text">
                            您好！我是AI助手，可以基于搜索结果数据库为您提供智能问答服务。
                            <br><br>
                            <strong>使用说明：</strong>
                            <br>• 在左侧搜索数据后，我可以基于搜索结果回答您的问题
                            <br>• 您可以在上方"知识库设置"中选择要包含的字段类型
                            <br>• 支持中文问答，请直接输入您的问题
                        </div>
                        <div class="message-time">现在</div>
                    </div>
                </div>
            </div>
        `;
    }
}

// 发送聊天消息
async function sendChatMessage() {
    const chatInput = document.getElementById('chatInput');
    const message = chatInput.value.trim();
    
    if (!message) return;
    
    // 添加用户消息到聊天记录
    addMessageToChat('user', message);
    
    // 清空输入框
    chatInput.value = '';
    
    // 添加正在输入提示
    const typingMessage = addMessageToChat('ai', '正在思考中...');
    
    try {
        // 调用后端LLM API
        const response = await callChatAPI(message);
        
        // 移除正在输入提示
        if (typingMessage && typingMessage.parentNode) {
            typingMessage.remove();
        }
        
        if (response.success) {
            addMessageToChat('ai', response.response);
        } else {
            addMessageToChat('ai', `抱歉，出现了错误：${response.error}`);
        }
    } catch (error) {
        // 移除正在输入提示
        if (typingMessage && typingMessage.parentNode) {
            typingMessage.remove();
        }
        addMessageToChat('ai', `抱歉，网络连接出现问题：${error.message}`);
    }
}

// 添加消息到聊天界面
function addMessageToChat(sender, text) {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return null;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const avatar = sender === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
    const currentTime = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    
    messageDiv.innerHTML = `
        <div class="message-avatar">
            ${avatar}
        </div>
        <div class="message-content">
            <div class="message-text">${text}</div>
            <div class="message-time">${currentTime}</div>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    
    // 滚动到底部
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // 添加到历史记录
    chatHistory.push({ sender, text, timestamp: new Date() });
    
    return messageDiv;
}

// 调用聊天API
async function callChatAPI(message) {
    // 获取当前搜索结果
    const searchResults = getCurrentSearchResults();
    
    // 获取选中的知识库字段
    const knowledgeBaseFields = getSelectedKnowledgeBaseFields();
    
    // 获取对话历史
    const conversationHistory = getConversationHistory();
    
    const requestData = {
        message: message,
        search_results: searchResults,
        knowledge_base_fields: knowledgeBaseFields,
        conversation_history: conversationHistory
    };
    
    const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
    });
    
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return await response.json();
}

// 获取当前搜索结果
function getCurrentSearchResults() {
    // 从全局变量获取当前的搜索结果
    return window.currentResults || [];
}

// 获取选中的知识库字段
function getSelectedKnowledgeBaseFields() {
    const fields = [];
    const checkboxes = document.querySelectorAll('#knowledgeBasePanel input[type="checkbox"]:checked');
    
    checkboxes.forEach(checkbox => {
        const fieldMap = {
            'kbTitle': 'title',
            'kbContent': 'content', 
            'kbTags': 'tags',
            'kbSentiment': 'sentiment_level',
            'kbCompanies': 'companies',
            'kbDate': 'publish_time'
        };
        
        const field = fieldMap[checkbox.id];
        if (field) {
            fields.push(field);
        }
    });
    
    return fields.length > 0 ? fields : ['title', 'content', 'tags', 'sentiment_level', 'companies', 'publish_time'];
}

// 获取对话历史
function getConversationHistory() {
    const history = [];
    
    // 从chatHistory全局变量获取历史记录
    if (window.chatHistory && Array.isArray(window.chatHistory)) {
        window.chatHistory.forEach(msg => {
            history.push({
                role: msg.sender === 'user' ? 'user' : 'assistant',
                content: msg.text
            });
        });
    }
    
    // 只保留最近10条消息
    return history.slice(-10);
}

// 生成AI回复 (旧版本，现在用作fallback)
function generateAIResponse(userQuestion) {
    // 检查是否有搜索结果
    if (!currentResults || currentResults.length === 0) {
        addMessageToChat('ai', '抱歉，目前还没有搜索结果。请先在左侧进行数据搜索，然后我就可以基于搜索结果为您提供智能问答服务了。');
        return;
    }
    
    // 构建知识库数据
    const knowledgeBaseData = buildKnowledgeBaseData();
    
    // 基于用户问题和知识库数据生成回复
    const response = generateResponseFromKnowledgeBase(userQuestion, knowledgeBaseData);
    
    // 添加AI回复到聊天界面
    addMessageToChat('ai', response);
}

// 构建知识库数据
function buildKnowledgeBaseData() {
    const data = [];
    
    currentResults.forEach(result => {
        const item = {};
        
        if (currentKnowledgeBase.title && result.title) {
            item.title = result.title;
        }
        
        if (currentKnowledgeBase.content && result.summary) {
            item.content = result.summary;
        }
        
        if (currentKnowledgeBase.tags) {
            const tags = [];
            const tagNames = [
                '同业竞争', '股权与控制权', '关联交易', '历史沿革与股东核查', '重大违法违规',
                '收入与成本', '财务内控不规范', '客户与供应商', '资产质量与减值', '研发与技术',
                '募集资金用途', '突击分红与对赌协议', '市场传闻与负面报道', '行业政策与环境'
            ];
            
            for (const tagName of tagNames) {
                const tagKey = `tag_${tagName}`;
                if (result[tagKey] === '是') {
                    tags.push(tagName);
                }
            }
            
            if (tags.length > 0) {
                item.tags = tags;
            }
        }
        
        if (currentKnowledgeBase.sentiment && result.sentiment_level) {
            item.sentiment = result.sentiment_level;
        }
        
        if (currentKnowledgeBase.companies && result.companies) {
            if (result.companies !== '无' && result.companies.trim()) {
                item.companies = result.companies.split(',').map(c => c.trim()).filter(Boolean);
            }
        }
        
        if (currentKnowledgeBase.date && result.publish_time) {
            item.date = new Date(result.publish_time).toLocaleDateString('zh-CN');
        }
        
        if (Object.keys(item).length > 0) {
            data.push(item);
        }
    });
    
    return data;
}

// 基于知识库生成回复
function generateResponseFromKnowledgeBase(question, knowledgeBase) {
    const questionLower = question.toLowerCase();
    
    // 情感分析相关问题
    if (question.includes('负面') || question.includes('风险') || question.includes('问题')) {
        const negativeItems = knowledgeBase.filter(item => 
            item.sentiment && (item.sentiment.includes('负面') || item.sentiment.includes('风险'))
        );
        
        if (negativeItems.length > 0) {
            return `根据搜索结果，我找到了 ${negativeItems.length} 条负面或风险相关的信息：\n\n` +
                   negativeItems.map(item => 
                       `• ${item.title || '无标题'}\n  情感：${item.sentiment || '未知'}\n  标签：${item.tags ? item.tags.join(', ') : '无'}\n  时间：${item.date || '未知'}`
                   ).join('\n\n');
        } else {
            return '根据搜索结果，目前没有发现明显的负面或风险信息。';
        }
    }
    
    // 特定地区相关问题
    if (question.includes('四平') || question.includes('地区') || question.includes('城市')) {
        const regionalItems = knowledgeBase.filter(item => 
            item.title && item.title.includes('四平') || 
            item.content && item.content.includes('四平')
        );
        
        if (regionalItems.length > 0) {
            return `关于四平市的相关信息，我找到了 ${regionalItems.length} 条：\n\n` +
                   regionalItems.map(item => 
                       `• ${item.title || '无标题'}\n  内容：${item.content ? item.content.substring(0, 100) + '...' : '无内容'}\n  时间：${item.date || '未知'}`
                   ).join('\n\n');
        } else {
            return '抱歉，在搜索结果中没有找到关于四平市的具体信息。';
        }
    }
    
    // 公司相关问题
    if (question.includes('公司') || question.includes('企业')) {
        const companyItems = knowledgeBase.filter(item => item.companies && item.companies.length > 0);
        
        if (companyItems.length > 0) {
            const allCompanies = new Set();
            companyItems.forEach(item => {
                item.companies.forEach(company => allCompanies.add(company));
            });
            
            return `在搜索结果中涉及的公司有：${Array.from(allCompanies).join(', ')}\n\n相关新闻：\n` +
                   companyItems.slice(0, 5).map(item => 
                       `• ${item.title || '无标题'} (${item.date || '未知'})`
                   ).join('\n');
        } else {
            return '在搜索结果中没有找到涉及具体公司的信息。';
        }
    }
    
    // 标签相关问题
    if (question.includes('标签') || question.includes('分类')) {
        const tagCounts = {};
        knowledgeBase.forEach(item => {
            if (item.tags) {
                item.tags.forEach(tag => {
                    tagCounts[tag] = (tagCounts[tag] || 0) + 1;
                });
            }
        });
        
        if (Object.keys(tagCounts).length > 0) {
            const tagList = Object.entries(tagCounts)
                .sort((a, b) => b[1] - a[1])
                .map(([tag, count]) => `${tag}: ${count}条`)
                .join(', ');
            
            return `搜索结果中的标签分布如下：\n${tagList}`;
        } else {
            return '在搜索结果中没有找到标签信息。';
        }
    }
    
    // 时间相关问题
    if (question.includes('时间') || question.includes('日期') || question.includes('最近')) {
        const recentItems = knowledgeBase
            .filter(item => item.date)
            .sort((a, b) => new Date(b.date) - new Date(a.date))
            .slice(0, 5);
        
        if (recentItems.length > 0) {
            return `最近的几条信息：\n\n` +
                   recentItems.map(item => 
                       `• ${item.title || '无标题'} - ${item.date}`
                   ).join('\n');
        } else {
            return '抱歉，无法获取时间相关信息。';
        }
    }
    
    // 统计信息
    if (question.includes('统计') || question.includes('数量') || question.includes('多少')) {
        const totalCount = knowledgeBase.length;
        const sentimentCounts = {};
        const tagCounts = {};
        
        knowledgeBase.forEach(item => {
            if (item.sentiment) {
                sentimentCounts[item.sentiment] = (sentimentCounts[item.sentiment] || 0) + 1;
            }
            if (item.tags) {
                item.tags.forEach(tag => {
                    tagCounts[tag] = (tagCounts[tag] || 0) + 1;
                });
            }
        });
        
        let response = `搜索结果统计信息：\n\n总数量：${totalCount}条\n\n`;
        
        if (Object.keys(sentimentCounts).length > 0) {
            response += '情感分布：\n' + Object.entries(sentimentCounts)
                .map(([sentiment, count]) => `${sentiment}: ${count}条`)
                .join('\n') + '\n\n';
        }
        
        if (Object.keys(tagCounts).length > 0) {
            response += '标签分布：\n' + Object.entries(tagCounts)
                .map(([tag, count]) => `${tag}: ${count}条`)
                .join('\n');
        }
        
        return response;
    }
    
    // 默认回复
    return `我理解您的问题"${question}"，但在搜索结果中没有找到完全匹配的信息。\n\n您可以尝试：\n• 询问更具体的问题，如"有哪些负面新闻？"\n• 询问统计信息，如"总共有多少条结果？"\n• 询问特定内容，如"四平市的相关信息有哪些？"`;
}

// 显示搜索结果更新提示
function showSearchResultsUpdate(resultCount) {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;
    
    // 检查是否已经有更新提示
    const existingUpdate = chatMessages.querySelector('.search-update-message');
    if (existingUpdate) {
        existingUpdate.remove();
    }
    
    const updateMessage = document.createElement('div');
    updateMessage.className = 'message ai-message search-update-message';
    updateMessage.innerHTML = `
        <div class="message-avatar">
            <i class="fas fa-robot"></i>
        </div>
        <div class="message-content">
            <div class="message-text">
                <i class="fas fa-info-circle"></i> 搜索结果已更新，共找到 ${resultCount} 条结果。
                <br>现在您可以基于这些数据向我提问了！
            </div>
            <div class="message-time">现在</div>
        </div>
    `;
    
    // 插入到欢迎消息之后
    const welcomeMessage = chatMessages.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.after(updateMessage);
    } else {
        chatMessages.appendChild(updateMessage);
    }
    
    // 滚动到底部
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 切换高级搜索面板
function toggleAdvancedSearch() {
    const advancedSearch = document.getElementById('advancedSearch');
    if (advancedSearch) {
        advancedSearch.style.display = advancedSearch.style.display === 'none' ? 'block' : 'none';
    }
}

// 监听知识库设置变化
document.addEventListener('DOMContentLoaded', function() {
    // 绑定知识库字段选择事件
    const fieldCheckboxes = ['kbTitle', 'kbContent', 'kbTags', 'kbSentiment', 'kbCompanies', 'kbDate'];
    
    fieldCheckboxes.forEach(fieldId => {
        const checkbox = document.getElementById(fieldId);
        if (checkbox) {
            checkbox.addEventListener('change', function() {
                const fieldName = fieldId.replace('kb', '').toLowerCase();
                currentKnowledgeBase[fieldName] = this.checked;
            });
        }
    });
    
    // 绑定回车键发送消息
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendChatMessage();
            }
        });
    }
});
