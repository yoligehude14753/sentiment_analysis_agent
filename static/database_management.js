// 数据库管理相关功能

class DatabaseManager {
    constructor() {
        this.baseUrl = '';
        this.init();
    }

    init() {
        // 绑定事件监听器
        this.bindEventListeners();
        // 加载初始统计信息
        this.loadDatabaseStats();
    }

    bindEventListeners() {
        // 修复摘要按钮
        const fixSummariesBtn = document.getElementById('fix-summaries-btn');
        if (fixSummariesBtn) {
            fixSummariesBtn.addEventListener('click', () => this.fixSummaries());
        }

        // 检测重复数据按钮
        const detectDuplicatesBtn = document.getElementById('detect-duplicates-btn');
        if (detectDuplicatesBtn) {
            detectDuplicatesBtn.addEventListener('click', () => this.detectDuplicates());
        }

        // 清理重复数据按钮
        const cleanDuplicatesBtn = document.getElementById('clean-duplicates-btn');
        if (cleanDuplicatesBtn) {
            cleanDuplicatesBtn.addEventListener('click', () => this.cleanDuplicates());
        }

        // 导出去重数据按钮
        const exportDeduplicatedBtn = document.getElementById('export-deduplicated-btn');
        if (exportDeduplicatedBtn) {
            exportDeduplicatedBtn.addEventListener('click', () => this.exportDeduplicated());
        }

        // 刷新统计按钮
        const refreshStatsBtn = document.getElementById('refresh-stats-btn');
        if (refreshStatsBtn) {
            refreshStatsBtn.addEventListener('click', () => this.loadDatabaseStats());
        }
    }

    async loadDatabaseStats() {
        try {
            this.showLoading('正在加载数据库统计信息...');
            
            const response = await fetch('/api/results/database/stats');
            const result = await response.json();

            if (result.success) {
                this.displayDatabaseStats(result.data);
            } else {
                this.showError('加载统计信息失败');
            }
        } catch (error) {
            this.showError(`加载统计信息失败: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }

    displayDatabaseStats(stats) {
        // 更新统计信息显示
        const statsContainer = document.getElementById('database-stats');
        if (statsContainer) {
            statsContainer.innerHTML = `
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value">${stats.total_records || 0}</div>
                        <div class="stat-label">总记录数</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${stats.records_with_summary || 0}</div>
                        <div class="stat-label">有摘要记录</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${stats.records_without_summary || 0}</div>
                        <div class="stat-label">无摘要记录</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${stats.duplicate_records || 0}</div>
                        <div class="stat-label">重复记录</div>
                    </div>
                </div>
                <div class="stats-info">
                    <p><strong>最新记录时间:</strong> ${stats.latest_record_time || '无'}</p>
                </div>
            `;
        }
    }

    async fixSummaries() {
        if (!confirm('确定要修复空摘要吗？这可能需要一些时间。')) {
            return;
        }

        try {
            this.showLoading('正在修复空摘要，请稍候...');
            
            const response = await fetch('/api/results/database/fix-summaries', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();

            if (result.success) {
                this.showSuccess('摘要修复完成！');
                // 刷新统计信息
                await this.loadDatabaseStats();
            } else {
                this.showError('修复摘要失败');
            }
        } catch (error) {
            this.showError(`修复摘要失败: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }

    async detectDuplicates() {
        const threshold = document.getElementById('similarity-threshold')?.value || 0.8;
        
        if (!confirm(`确定要检测重复数据吗？相似度阈值: ${threshold}`)) {
            return;
        }

        try {
            this.showLoading('正在检测重复数据，请稍候...');
            
            const response = await fetch(`/api/results/database/detect-duplicates?similarity_threshold=${threshold}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();

            if (result.success) {
                this.showSuccess(`重复检测完成！找到 ${result.duplicate_pairs} 对重复数据`);
                // 刷新统计信息
                await this.loadDatabaseStats();
            } else {
                this.showError('检测重复数据失败');
            }
        } catch (error) {
            this.showError(`检测重复数据失败: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }

    async cleanDuplicates() {
        const strategy = document.getElementById('keep-strategy')?.value || 'first';
        
        if (!confirm(`确定要清理重复数据吗？保留策略: ${strategy === 'first' ? '保留最早的' : '保留最新的'}。此操作不可撤销！`)) {
            return;
        }

        try {
            this.showLoading('正在清理重复数据，请稍候...');
            
            const response = await fetch(`/api/results/database/clean-duplicates?keep_strategy=${strategy}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();

            if (result.success) {
                this.showSuccess(`重复数据清理完成！删除了 ${result.deleted_count} 条记录`);
                // 刷新统计信息
                await this.loadDatabaseStats();
            } else {
                this.showError('清理重复数据失败');
            }
        } catch (error) {
            this.showError(`清理重复数据失败: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }

    async autoDeduplicateDatabase() {
        const threshold = parseFloat(document.getElementById('similarity-threshold')?.value || '0.85');
        
        if (threshold < 0.1 || threshold > 1.0) {
            this.showError('相似度阈值必须在0.1-1.0之间');
            return;
        }
        
        if (!confirm(`确定要使用相似度阈值 ${threshold} 进行自动去重吗？`)) {
            return;
        }

        try {
            this.showLoading('正在执行智能去重分析...');
            
            const response = await fetch(`/api/results/database/auto-deduplicate?similarity_threshold=${threshold}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                const stats = result.stats;
                this.showSuccess(
                    `智能去重分析完成！\n` +
                    `原始记录: ${stats.original_count} 条\n` +
                    `去重后: ${stats.final_count} 条\n` +
                    `移除重复: ${stats.removed_count} 条\n` +
                    `去重率: ${(stats.deduplication_rate * 100).toFixed(1)}%`
                );
                // 刷新统计信息
                await this.loadDatabaseStats();
            } else {
                this.showError('智能去重失败');
            }
        } catch (error) {
            this.showError(`智能去重失败: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }

    async exportDeduplicated() {
        const sessionId = document.getElementById('export-session-id')?.value || null;
        
        try {
            this.showLoading('正在导出去重数据，请稍候...');
            
            let url = '/api/results/export/deduplicated?format=json';
            if (sessionId) {
                url += `&session_id=${sessionId}`;
            }
            
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                // 触发文件下载
                const blob = await response.blob();
                const downloadUrl = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = downloadUrl;
                a.download = `deduplicated_results_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(downloadUrl);
                
                this.showSuccess('去重数据导出完成！');
            } else {
                const result = await response.json();
                this.showError(result.detail || '导出失败');
            }
        } catch (error) {
            this.showError(`导出去重数据失败: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }

    showLoading(message) {
        const loadingEl = document.getElementById('loading-message');
        if (loadingEl) {
            loadingEl.textContent = message;
            loadingEl.style.display = 'block';
        }
    }

    hideLoading() {
        const loadingEl = document.getElementById('loading-message');
        if (loadingEl) {
            loadingEl.style.display = 'none';
        }
    }

    showSuccess(message) {
        this.showMessage(message, 'success');
    }

    showError(message) {
        this.showMessage(message, 'error');
    }

    showMessage(message, type) {
        // 创建消息元素
        const messageEl = document.createElement('div');
        messageEl.className = `message message-${type}`;
        messageEl.textContent = message;
        
        // 添加到页面
        const container = document.getElementById('message-container') || document.body;
        container.appendChild(messageEl);
        
        // 自动移除
        setTimeout(() => {
            if (messageEl.parentNode) {
                messageEl.parentNode.removeChild(messageEl);
            }
        }, 5000);
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    window.databaseManager = new DatabaseManager();
});
