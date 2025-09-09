/**
 * 分析结果展示页面JavaScript
 * 负责搜索、结果展示和文章详情
 */

class ResultsDisplayManager {
    constructor() {
        this.currentPage = 1;
        this.pageSize = 20;
        this.totalPages = 1;
        this.currentResults = [];
        this.selectedArticle = null;
        this.searchTimeout = null;
        
        this.initElements();
        this.bindEvents();
        this.loadInitialResults();
    }

    initElements() {
        // 搜索元素
        this.searchInput = document.getElementById('searchInput');
        this.searchBtn = document.getElementById('searchBtn');
        this.toggleAdvancedBtn = document.getElementById('toggleAdvancedBtn');
        this.advancedOptions = document.getElementById('advancedOptions');
        
        // 过滤器元素
        this.sentimentFilter = document.getElementById('sentimentFilter');
        this.tagFilter = document.getElementById('tagFilter');
        this.dateFilter = document.getElementById('dateFilter');
        
        // 结果统计元素
        this.resultCount = document.getElementById('resultCount');
        this.searchTime = document.getElementById('searchTime');
        
        // 结果展示元素
        this.searchResults = document.getElementById('searchResults');
        this.noResults = document.getElementById('noResults');
        this.resultsList = document.getElementById('resultsList');
        this.pagination = document.getElementById('pagination');
        this.currentPageSpan = document.getElementById('currentPage');
        this.totalPagesSpan = document.getElementById('totalPages');
        this.prevPageBtn = document.getElementById('prevPageBtn');
        this.nextPageBtn = document.getElementById('nextPageBtn');
        
        // 文章详情元素
        this.articlePrompt = document.getElementById('articlePrompt');
        this.articleDetail = document.getElementById('articleDetail');
        this.articleTitle = document.getElementById('articleTitle');
        this.articlePublishTime = document.getElementById('articlePublishTime');
        this.articleDataSource = document.getElementById('articleDataSource');
        this.articleAnalysisTime = document.getElementById('articleAnalysisTime');
        this.articleSentiment = document.getElementById('articleSentiment');
        this.articleTags = document.getElementById('articleTags');
        this.articleCompanies = document.getElementById('articleCompanies');
        this.articleDuplicateStatus = document.getElementById('articleDuplicateStatus');
        this.articleContent = document.getElementById('articleContent');
        
        // 详细分析元素
        this.detailSentimentLevel = document.getElementById('detailSentimentLevel');
        this.detailSentimentReason = document.getElementById('detailSentimentReason');
        this.detailTags = document.getElementById('detailTags');
        this.detailCompanies = document.getElementById('detailCompanies');
        this.detailDuplicateStatus = document.getElementById('detailDuplicateStatus');
        this.detailSimilarityScore = document.getElementById('detailSimilarityScore');
        this.detailDuplicateGroup = document.getElementById('detailDuplicateGroup');
        
        // 导出模态框元素
        this.exportModal = document.getElementById('exportModal');
        this.closeExportModal = document.getElementById('closeExportModal');
        this.confirmExportBtn = document.getElementById('confirmExportBtn');
        this.cancelExportBtn = document.getElementById('cancelExportBtn');
    }

    bindEvents() {
        // 搜索事件
        this.searchInput.addEventListener('input', () => {
            this.debounceSearch();
        });
        
        this.searchBtn.addEventListener('click', () => {
            this.performSearch();
        });
        
        // 高级搜索切换
        this.toggleAdvancedBtn.addEventListener('click', () => {
            this.toggleAdvancedSearch();
        });
        
        // 过滤器变化事件
        this.sentimentFilter.addEventListener('change', () => {
            this.performSearch();
        });
        
        this.tagFilter.addEventListener('change', () => {
            this.performSearch();
        });
        
        this.dateFilter.addEventListener('change', () => {
            this.performSearch();
        });
        
        // 分页事件
        this.prevPageBtn.addEventListener('click', () => {
            this.goToPage(this.currentPage - 1);
        });
        
        this.nextPageBtn.addEventListener('click', () => {
            this.goToPage(this.currentPage + 1);
        });
        
        // 导出模态框事件
        this.closeExportModal.addEventListener('click', () => {
            this.hideExportModal();
        });
        
        this.confirmExportBtn.addEventListener('click', () => {
            this.confirmExport();
        });
        
        this.cancelExportBtn.addEventListener('click', () => {
            this.hideExportModal();
        });
        
        // 文章操作事件
        document.getElementById('exportArticleBtn').addEventListener('click', () => {
            this.showExportModal();
        });
        
        document.getElementById('shareArticleBtn').addEventListener('click', () => {
            this.shareArticle();
        });
        
        document.getElementById('printArticleBtn').addEventListener('click', () => {
            this.printArticle();
        });
        
        // 回车键搜索
        this.searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.performSearch();
            }
        });
    }

    debounceSearch() {
        clearTimeout(this.searchTimeout);
        this.searchTimeout = setTimeout(() => {
            this.performSearch();
        }, 500);
    }

    async performSearch() {
        const startTime = Date.now();
        
        // 构建搜索参数
        const params = new URLSearchParams({
            search: this.searchInput.value.trim(),
            page: this.currentPage,
            page_size: this.pageSize
        });
        
        // 添加过滤器参数
        if (this.sentimentFilter.value) {
            params.append('sentiment', this.sentimentFilter.value);
        }
        
        if (this.tagFilter.value) {
            params.append('tags', this.tagFilter.value);
        }
        
        if (this.dateFilter.value) {
            params.append('date_range', this.dateFilter.value);
        }
        
        try {
            const response = await fetch(`/api/analysis_results?${params.toString()}`);
            const result = await response.json();
            
            if (result.success) {
                this.displayResults(result.data, result.total, result.total_pages);
                this.updateSearchStats(result.total, Date.now() - startTime);
            } else {
                this.showError(result.error || '搜索失败');
            }
        } catch (error) {
            console.error('搜索失败:', error);
            this.showError('搜索过程中出现错误');
        }
    }

    displayResults(results, total, totalPages) {
        this.currentResults = results;
        this.totalPages = totalPages;
        
        // 更新结果数量
        this.resultCount.textContent = total;
        
        // 显示/隐藏分页
        if (totalPages > 1) {
            this.pagination.classList.remove('hidden');
            this.updatePagination();
        } else {
            this.pagination.classList.add('hidden');
        }
        
        // 显示结果
        if (results.length === 0) {
            this.showNoResults();
        } else {
            this.hideNoResults();
            this.renderResultsList(results);
        }
    }

    renderResultsList(results) {
        this.resultsList.innerHTML = '';
        
        results.forEach((result, index) => {
            const resultItem = this.createResultItem(result, index);
            this.resultsList.appendChild(resultItem);
        });
    }

    createResultItem(result, index) {
        const item = document.createElement('div');
        item.className = 'result-row';
        item.dataset.articleId = result.original_id || result.id;
        
        // 标题单元格
        const titleCell = document.createElement('div');
        titleCell.className = 'result-cell title-cell';
        titleCell.textContent = result.title || '无标题';
        titleCell.addEventListener('click', () => {
            this.selectArticle(result);
        });
        titleCell.style.cursor = 'pointer';
        
        // 摘要单元格（小字体）
        const summaryCell = document.createElement('div');
        summaryCell.className = 'result-cell summary-cell';
        summaryCell.textContent = result.summary || '无摘要';

        // 发布时间单元格 (只显示日期)
        const dateCell = document.createElement('div');
        dateCell.className = 'result-cell date-cell';
        dateCell.textContent = this.formatDateOnly(result.publish_time);
        
        // 标签单元格
        const tagsCell = document.createElement('div');
        tagsCell.className = 'result-cell tags-cell';
        
        // 从字段构造匹配到的标签数组
        const tags = this.extractMatchedTags(result);
        if (tags.length > 0) {
            const matchedTags = tags;
            if (matchedTags.length > 0) {
                matchedTags.forEach(tag => {
                    const tagSpan = document.createElement('span');
                    tagSpan.className = 'tag-item clickable';
                    tagSpan.textContent = tag;
                    tagSpan.addEventListener('click', (e) => {
                        e.stopPropagation();
                        this.showTagReason(tag, result);
                    });
                    tagsCell.appendChild(tagSpan);
                });
            } else {
                tagsCell.textContent = '无标签';
                tagsCell.className += ' no-tags';
            }
        } else {
            tagsCell.textContent = '无标签';
            tagsCell.className += ' no-tags';
        }
        
        // 情感等级单元格
        const sentimentCell = document.createElement('div');
        sentimentCell.className = 'result-cell sentiment-cell';
        
        const sentimentSpan = document.createElement('span');
        const sentiment = result.sentiment_level || result.sentiment || '';
        sentimentSpan.className = `sentiment-item clickable sentiment-${this.getSentimentClass(sentiment)}`;
        sentimentSpan.textContent = sentiment || '未知';
        sentimentSpan.addEventListener('click', (e) => {
            e.stopPropagation();
            this.showSentimentReason(result);
        });
        sentimentCell.appendChild(sentimentSpan);
        
        // 匹配的公司单元格
        const companyCell = document.createElement('div');
        companyCell.className = 'result-cell company-cell';
        
        const topCompany = this.extractTopCompany(result.companies);
        if (topCompany) {
            companyCell.textContent = topCompany;
        } else {
            companyCell.textContent = '无';
            companyCell.className += ' no-company';
        }
        
        // 组装结果行
        item.appendChild(titleCell);
        item.appendChild(summaryCell);
        item.appendChild(dateCell);
        item.appendChild(tagsCell);
        item.appendChild(sentimentCell);
        item.appendChild(companyCell);
        
        return item;
    }

    getSentimentClass(sentiment) {
        if (!sentiment) return 'neutral';
        if (String(sentiment).includes('正面') || String(sentiment).includes('积极')) return 'positive';
        if (String(sentiment).includes('负面')) return 'negative';
        return 'neutral';
    }

    selectArticle(article) {
        console.log('选择文章:', article);
        this.selectedArticle = article;
        this.showArticleDetail(article);
        this.highlightSelectedArticle(article.original_id || article.id);
    }

    showArticleDetail(article) {
        console.log('显示文章详情:', article);
        
        // 获取HTML元素
        const articlePrompt = document.querySelector('.article-prompt');
        const articleDetailContent = document.querySelector('.article-detail-content');
        const articleTitle = document.getElementById('articleTitle');
        const articlePublishTime = document.getElementById('articlePublishTime');
        const articleDataSource = document.getElementById('articleDataSource');
        const articleAnalysisTime = document.getElementById('articleAnalysisTime');
        const articleSentiment = document.getElementById('articleSentiment');
        const articleTags = document.getElementById('articleTags');
        const articleCompanies = document.getElementById('articleCompanies');
        const articleDuplicateStatus = document.getElementById('articleDuplicateStatus');
        const articleContent = document.getElementById('articleContent');
        
        // 隐藏提示，显示详情
        if (articlePrompt) articlePrompt.classList.add('hidden');
        if (articleDetailContent) articleDetailContent.classList.remove('hidden');
        
        // 填充文章基本信息
        if (articleTitle) articleTitle.textContent = article.title || '无标题';
        if (articlePublishTime) articlePublishTime.textContent = this.formatDate(article.publish_time) || '未知时间';
        if (articleDataSource) articleDataSource.textContent = article.source || article.data_source || '未知来源';
        if (articleAnalysisTime) articleAnalysisTime.textContent = this.formatDate(article.analysis_time) || '未知时间';
        
        // 填充分析结果概览
        const sentiment = article.sentiment_level || article.sentiment || '未知';
        if (articleSentiment) {
            articleSentiment.textContent = sentiment;
            articleSentiment.className = `sentiment-badge sentiment-${this.getSentimentClass(sentiment)}`;
        }
        
        // 填充标签
        if (articleTags) {
            articleTags.innerHTML = '';
            const detailTags = this.extractMatchedTags(article);
            if (detailTags.length > 0) {
                detailTags.forEach(tag => {
                    const tagSpan = document.createElement('span');
                    tagSpan.className = 'tag risk-tag';
                    tagSpan.textContent = tag;
                    articleTags.appendChild(tagSpan);
                });
            } else {
                const noTagSpan = document.createElement('span');
                noTagSpan.className = 'tag no-tag';
                noTagSpan.textContent = '无风险标签';
                articleTags.appendChild(noTagSpan);
            }
        }
        
        // 填充企业信息
        if (articleCompanies) {
            articleCompanies.innerHTML = '';
            const companies = this.extractCompaniesArray(article.companies);
            if (companies.length > 0) {
                companies.forEach(company => {
                    const companySpan = document.createElement('span');
                    companySpan.className = 'company-badge';
                    companySpan.textContent = company;
                    articleCompanies.appendChild(companySpan);
                });
            } else {
                const noCompanySpan = document.createElement('span');
                noCompanySpan.className = 'company-badge no-company';
                noCompanySpan.textContent = '未识别到企业';
                articleCompanies.appendChild(noCompanySpan);
            }
        }
        
        // 填充重复度
        if (articleDuplicateStatus) {
            articleDuplicateStatus.textContent = article.duplicate_status || '未知';
            articleDuplicateStatus.className = `duplicate-badge duplicate-${(article.duplicate_status === '重复') ? 'duplicate' : 'unique'}`;
        }
        
        // 填充文章内容（这里应该从数据库获取完整内容）
        if (articleContent) {
            articleContent.innerHTML = `
                <p>${article.summary || '无摘要内容'}</p>
                <p class="content-note">注：此处显示的是文章摘要，完整内容需要从数据库获取。</p>
            `;
        }
        
        // 填充详细分析结果
        this.fillDetailedAnalysis(article);
    }

    fillDetailedAnalysis(article) {
        // 获取HTML元素
        const detailSentimentLevel = document.getElementById('detailSentimentLevel');
        const detailSentimentReason = document.getElementById('detailSentimentReason');
        const detailTags = document.getElementById('detailTags');
        const detailCompanies = document.getElementById('detailCompanies');
        
        // 情感分析详情
        const sentiment = article.sentiment_level || article.sentiment || '';
        if (detailSentimentLevel) detailSentimentLevel.textContent = sentiment;
        if (detailSentimentReason) detailSentimentReason.textContent = '详细的分析原因将在这里显示...';
        
        // 标签分析详情
        if (detailTags) {
            detailTags.innerHTML = '';
            const detailTagsArray = this.extractMatchedTags(article);
            if (detailTagsArray.length > 0) {
                detailTagsArray.forEach(tag => {
                    const tagDetail = document.createElement('div');
                    tagDetail.className = 'analysis-item';
                    tagDetail.innerHTML = `
                        <span class="label">${tag}：</span>
                        <span>该标签的详细分析原因将在这里显示...</span>
                    `;
                    detailTags.appendChild(tagDetail);
                });
            } else {
                const noTagDetail = document.createElement('div');
                noTagDetail.className = 'analysis-item';
                noTagDetail.innerHTML = `
                    <span class="label">无匹配标签：</span>
                    <span>该文章未识别到任何预定义的风险标签。</span>
                `;
                detailTags.appendChild(noTagDetail);
            }
        }
        
        // 企业分析详情
        if (detailCompanies) {
            detailCompanies.innerHTML = '';
            const companies = this.extractCompaniesArray(article.companies);
            if (companies.length > 0) {
                companies.forEach(company => {
                    const companyDetail = document.createElement('div');
                    companyDetail.className = 'analysis-item';
                    companyDetail.innerHTML = `
                        <span class="label">${company}：</span>
                        <span>该企业的详细分析结果将在这里显示...</span>
                    `;
                    detailCompanies.appendChild(companyDetail);
                });
            } else {
                const noCompanyDetail = document.createElement('div');
                noCompanyDetail.className = 'analysis-item';
                noCompanyDetail.innerHTML = `
                    <span class="label">无相关企业：</span>
                    <span>该文章未识别到任何相关企业。</span>
                `;
                detailCompanies.appendChild(noCompanyDetail);
            }
        }
        
        // 企业识别详情
        this.detailCompanies.innerHTML = '';
        const companies = this.extractCompaniesArray(article.companies);
        if (companies.length > 0) {
            companies.forEach(company => {
                const companyDetail = document.createElement('div');
                companyDetail.className = 'analysis-item';
                companyDetail.innerHTML = `
                    <span class="label">${company}：</span>
                    <span>通过AI智能识别技术识别到的企业实体。</span>
                `;
                this.detailCompanies.appendChild(companyDetail);
            });
        } else {
            const noCompanyDetail = document.createElement('div');
            noCompanyDetail.className = 'analysis-item';
            noCompanyDetail.innerHTML = `
                <span class="label">未识别到企业：</span>
                <span>该文章内容中未识别到明确的企业实体。</span>
            `;
            this.detailCompanies.appendChild(noCompanyDetail);
        }
        
        // 重复度分析详情
        this.detailDuplicateStatus.textContent = article.duplicate_status;
        this.detailSimilarityScore.textContent = '相似度计算中...';
        this.detailDuplicateGroup.textContent = '重复组ID计算中...';
    }

    highlightSelectedArticle(articleId) {
        // 移除所有高亮
        document.querySelectorAll('.result-row').forEach(item => {
            item.classList.remove('selected');
        });
        
        // 高亮选中的文章
        const selectedItem = document.querySelector(`[data-article-id="${articleId}"]`);
        if (selectedItem) {
            selectedItem.classList.add('selected');
        }
    }

    toggleAdvancedSearch() {
        this.advancedOptions.classList.toggle('hidden');
        const icon = this.toggleAdvancedBtn.querySelector('i');
        if (this.advancedOptions.classList.contains('hidden')) {
            icon.className = 'fas fa-filter';
            this.toggleAdvancedBtn.innerHTML = '<i class="fas fa-filter"></i> 筛选';
        } else {
            icon.className = 'fas fa-chevron-up';
            this.toggleAdvancedBtn.innerHTML = '<i class="fas fa-chevron-up"></i> 收起筛选';
        }
    }

    goToPage(page) {
        if (page < 1 || page > this.totalPages) {
            return;
        }
        
        this.currentPage = page;
        this.performSearch();
    }

    updatePagination() {
        this.currentPageSpan.textContent = this.currentPage;
        this.totalPagesSpan.textContent = this.totalPages;
        
        this.prevPageBtn.disabled = this.currentPage <= 1;
        this.nextPageBtn.disabled = this.currentPage >= this.totalPages;
    }

    updateSearchStats(total, searchTime) {
        this.resultCount.textContent = total;
        this.searchTime.textContent = `(搜索用时: ${searchTime}ms)`;
    }

    showNoResults() {
        this.noResults.classList.remove('hidden');
        this.resultsList.innerHTML = '';
        this.pagination.classList.add('hidden');
    }

    hideNoResults() {
        this.noResults.classList.add('hidden');
    }

    showError(message) {
        // 这里可以实现更好的错误提示
        console.error(message);
        this.showNoResults();
    }

    formatDate(dateString) {
        if (!dateString) return '未知时间';
        
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (e) {
            return dateString;
        }
    }

    formatDateOnly(dateString) {
        if (!dateString) return '未知日期';
        
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit'
            });
        } catch (e) {
            return dateString;
        }
    }

    showTagReason(tag, result) {
        // 显示标签匹配原因的弹窗或提示
        const reasonsMap = this.extractTagReasonsMap(result);
        const reason = reasonsMap[tag] || '暂无详细原因';
        alert(`标签: ${tag}\n匹配原因: ${reason}`);
    }

    showSentimentReason(result) {
        // 显示情感分析原因的弹窗或提示
        const sentiment = result.sentiment_level || result.sentiment || '';
        const reason = result.sentiment_reason || '暂无详细原因';
        alert(`情感等级: ${sentiment}\n分析原因: ${reason}`);
    }

    async loadInitialResults() {
        // 加载初始结果
        await this.performSearch();
    }

    showExportModal() {
        this.exportModal.classList.remove('hidden');
    }

    hideExportModal() {
        this.exportModal.classList.add('hidden');
    }

    async confirmExport() {
        const format = (document.querySelector('input[name="exportFormat"]:checked') || {}).value || 'excel';
        try {
            const formData = new FormData();
            formData.append('export_format', format);
            formData.append('include_metadata', 'true');
            const response = await fetch('/api/export/enhanced', { method: 'POST', body: formData });
            const result = await response.json();
            if (result.success && result.export_file) {
                alert(`导出完成: ${result.export_file}`);
            } else {
                alert(`导出失败: ${result.detail || result.message || '未知错误'}`);
            }
        } catch (e) {
            alert(`导出失败: ${e.message}`);
        } finally {
            this.hideExportModal();
        }
    }

    shareArticle() {
        if (navigator.share && this.selectedArticle) {
            navigator.share({
                title: this.selectedArticle.title,
                text: this.selectedArticle.summary,
                url: window.location.href
            });
        } else {
            // 复制链接到剪贴板
            navigator.clipboard.writeText(window.location.href).then(() => {
                alert('链接已复制到剪贴板');
            });
        }
    }

    printArticle() {
        if (this.selectedArticle) {
            const printWindow = window.open('', '_blank');
            printWindow.document.write(`
                <html>
                <head>
                    <title>${this.selectedArticle.title}</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 20px; }
                        .title { font-size: 24px; font-weight: bold; margin-bottom: 20px; }
                        .meta { color: #666; margin-bottom: 20px; }
                        .content { line-height: 1.6; }
                    </style>
                </head>
                <body>
                    <div class="title">${this.selectedArticle.title}</div>
                    <div class="meta">
                        发布时间: ${this.formatDate(this.selectedArticle.publish_time)}<br>
                        数据源: ${(this.selectedArticle.source || this.selectedArticle.data_source || '')}<br>
                        情感等级: ${(this.selectedArticle.sentiment_level || this.selectedArticle.sentiment || '')}
                    </div>
                    <div class="content">${this.selectedArticle.summary}</div>
                </body>
                </html>
            `);
            printWindow.document.close();
            printWindow.print();
        }
    }

    extractMatchedTags(result) {
        // 支持两种结构：tags数组 或 多个 tag_字段为"是"
        const tagList = Array.isArray(result.tags) ? result.tags.filter(Boolean) : [];
        const knownTags = [
            "同业竞争", "股权与控制权", "关联交易", "历史沿革与股东核查", "重大违法违规",
            "收入与成本", "财务内控不规范", "客户与供应商", "资产质量与减值", "研发与技术",
            "募集资金用途", "突击分红与对赌协议", "市场传闻与负面报道", "行业政策与环境"
        ];
        const detected = [];
        knownTags.forEach(name => {
            const key = `tag_${name}`;
            if (result[key] === '是') detected.push(name);
        });
        const union = Array.from(new Set([...tagList, ...detected]));
        return union.length > 0 ? union : [];
    }

    extractTagReasonsMap(result) {
        const reasons = {};
        const knownTags = [
            "同业竞争", "股权与控制权", "关联交易", "历史沿革与股东核查", "重大违法违规",
            "收入与成本", "财务内控不规范", "客户与供应商", "资产质量与减值", "研发与技术",
            "募集资金用途", "突击分红与对赌协议", "市场传闻与负面报道", "行业政策与环境"
        ];
        knownTags.forEach(name => {
            const key = `reason_${name}`;
            if (result[key]) reasons[name] = result[key];
        });
        if (result.tag_reasons) {
            Object.assign(reasons, result.tag_reasons);
        }
        return reasons;
    }

    extractCompaniesArray(companiesField) {
        if (!companiesField) return [];
        if (Array.isArray(companiesField)) return companiesField.filter(Boolean);
        if (typeof companiesField === 'string') return companiesField.split(',').map(s => s.trim()).filter(Boolean);
        return [];
    }

    extractTopCompany(companiesField) {
        const arr = this.extractCompaniesArray(companiesField);
        return arr.length > 0 ? arr[0] : '';
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    new ResultsDisplayManager();
});
