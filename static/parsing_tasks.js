/**
 * 舆情解析任务页面JavaScript
 * 负责任务配置、执行和进度显示
 */

class ParsingTaskManager {
    constructor() {
        this.currentTask = null;
        this.isRunning = false;
        this.startTime = null;
        this.processedCount = 0;
        this.totalCount = 0;
        this.errorCount = 0;
        
        this.initElements();
        this.bindEvents();
        this.initDatabaseConfig();
        // 异步初始化时间输入
        this.initTimeInputs();
    }

    initElements() {
        // 配置元素
        this.dataSourceSelect = document.getElementById('dataSource');
        this.databaseTypeSelect = document.getElementById('databaseType');
        this.customDatabaseConfig = document.getElementById('customDatabaseConfig');
        this.databaseHost = document.getElementById('databaseHost');
        this.databasePort = document.getElementById('databasePort');
        this.databaseName = document.getElementById('databaseName');
        this.databaseUser = document.getElementById('databaseUser');
        this.databasePassword = document.getElementById('databasePassword');
        
        // 时间选择元素
        this.timeFieldSelect = document.getElementById('timeField');
        this.customTimeField = document.getElementById('customTimeField');
        this.customTimeFieldName = document.getElementById('customTimeFieldName');
        this.startTimeInput = document.getElementById('startTime');
        this.endTimeInput = document.getElementById('endTime');
        
        // 数据预览元素
        this.dataPreview = document.getElementById('dataPreview');
        this.selectedTimeRange = document.getElementById('selectedTimeRange');
        this.dataCount = document.getElementById('dataCount');
        this.estimatedProcessTime = document.getElementById('estimatedProcessTime');
        this.refreshDataCountBtn = document.getElementById('refreshDataCountBtn');
        
        // 分析配置元素
        this.enableSentiment = document.getElementById('enableSentiment');
        this.enableTags = document.getElementById('enableTags');
        this.enableCompanies = document.getElementById('enableCompanies');
        this.enableDuplication = document.getElementById('enableDuplication');
        
        // 结果存储配置元素
        this.resultDatabaseSelect = document.getElementById('resultDatabase');
        this.customResultConfig = document.getElementById('customResultConfig');
        this.resultDbHost = document.getElementById('resultDbHost');
        this.resultDbPort = document.getElementById('resultDbPort');
        this.resultDbName = document.getElementById('resultDbName');
        this.resultDbUser = document.getElementById('resultDbUser');
        this.resultDbPassword = document.getElementById('resultDbPassword');
        
        // 按钮元素
        this.startTaskBtn = document.getElementById('startTaskBtn');
        this.analyzeLatestBtn = document.getElementById('analyzeLatestBtn');
        this.stopTaskBtn = document.getElementById('stopTaskBtn');
        this.resetTaskBtn = document.getElementById('resetTaskBtn');
        this.exportResultsBtn = document.getElementById('exportResultsBtn');
        this.newTaskBtn = document.getElementById('newTaskBtn');
        
        // 统计元素
        this.totalDataSpan = document.getElementById('totalData');
        this.processedDataSpan = document.getElementById('processedData');
        this.successRateSpan = document.getElementById('successRate');
        this.estimatedTimeSpan = document.getElementById('estimatedTime');
        
        // 状态和进度元素
        this.taskStatus = document.getElementById('taskStatus');
        this.executionProgress = document.getElementById('executionProgress');
        this.overallProgress = document.getElementById('overallProgress');
        this.progressText = document.getElementById('progressText');
        this.currentItemInfo = document.getElementById('currentItemInfo');
        this.logContainer = document.getElementById('logContainer');
        this.errorSummary = document.getElementById('errorSummary');
        this.errorList = document.getElementById('errorList');
        
        // 任务完成元素
        this.taskCompleteSection = document.getElementById('taskComplete');
        this.finalTotal = document.getElementById('finalTotal');
        this.finalSuccess = document.getElementById('finalSuccess');
        this.finalFailed = document.getElementById('finalFailed');
        this.finalTime = document.getElementById('finalTime');
        
        // 模态框元素
        this.taskConfirmModal = document.getElementById('taskConfirmModal');
        this.confirmDataSource = document.getElementById('confirmDataSource');
        this.confirmDataRange = document.getElementById('confirmDataRange');
        this.confirmAnalysisModules = document.getElementById('confirmAnalysisModules');
        this.confirmDataCount = document.getElementById('confirmDataCount');
        this.confirmTaskBtn = document.getElementById('confirmTaskBtn');
        this.cancelTaskBtn = document.getElementById('cancelTaskBtn');
        this.closeTaskModal = document.getElementById('closeTaskModal');
    }

    bindEvents() {
        // 数据源变化事件
        this.dataSourceSelect.addEventListener('change', () => {
            this.toggleDatabaseConfig();
        });
        
        // 数据库类型变化事件
        this.databaseTypeSelect.addEventListener('change', () => {
            this.toggleCustomDatabaseConfig();
        });
        
        // 时间字段变化事件
        this.timeFieldSelect.addEventListener('change', () => {
            this.toggleCustomTimeField();
        });
        
        // 时间范围变化事件
        this.startTimeInput.addEventListener('change', () => {
            this.updateDataPreview();
        });
        
        this.endTimeInput.addEventListener('change', () => {
            this.updateDataPreview();
        });
        
        // 结果数据库变化事件
        this.resultDatabaseSelect.addEventListener('change', () => {
            this.toggleCustomResultConfig();
        });
        
        // 刷新数据量按钮事件
        this.refreshDataCountBtn.addEventListener('click', () => {
            this.updateDataPreview();
        });
        
        // 按钮事件
        this.startTaskBtn.addEventListener('click', () => {
            this.showTaskConfirm();
        });
        
        this.analyzeLatestBtn.addEventListener('click', () => {
            this.analyzeLatestData();
        });
        
        this.stopTaskBtn.addEventListener('click', () => {
            this.stopTask();
        });
        
        this.resetTaskBtn.addEventListener('click', () => {
            this.resetTask();
        });
        
        if (this.exportResultsBtn) {
            this.exportResultsBtn.addEventListener('click', () => {
                this.handleExportResults();
            });
        }
        
        if (this.newTaskBtn) {
            this.newTaskBtn.addEventListener('click', () => {
                this.newTask();
            });
        }
        
        // 模态框事件
        this.confirmTaskBtn.addEventListener('click', () => {
            this.startTask();
        });
        
        this.cancelTaskBtn.addEventListener('click', () => {
            this.hideTaskConfirm();
        });
        
        this.closeTaskModal.addEventListener('click', () => {
            this.hideTaskConfirm();
        });
        
        // 日志控制事件
        const clearLogBtn = document.getElementById('clearLogBtn');
        const exportLogBtn = document.getElementById('exportLogBtn');
        
        if (clearLogBtn) {
            clearLogBtn.addEventListener('click', () => {
            this.clearLog();
        });
        }
        
        if (exportLogBtn) {
            exportLogBtn.addEventListener('click', () => {
            this.exportLog();
        });
        }
    }

    async initTimeInputs() {
        try {
            // 首先查询数据库中的实际时间范围
            const response = await fetch('/api/database/time-range');
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    // 使用数据库中的实际时间范围
                    const startDate = new Date(result.earliest_time);
                    const endDate = new Date(result.latest_time);
                    
                    this.startTimeInput.value = this.formatDateTimeLocal(startDate);
                    this.endTimeInput.value = this.formatDateTimeLocal(endDate);
                } else {
                    // 如果查询失败，使用默认范围（最近7天）
                    this.setDefaultTimeRange();
                }
            } else {
                // 如果API调用失败，使用默认范围
                this.setDefaultTimeRange();
            }
        } catch (error) {
            console.error('初始化时间范围失败:', error);
            // 使用默认范围
            this.setDefaultTimeRange();
        }
        
        // 初始化数据预览
        this.updateDataPreview();
    }

    setDefaultTimeRange() {
        // 设置默认时间范围（最近7天），精确到分钟
        const now = new Date();
        const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        
        // 设置开始时间为7天前的00:00
        weekAgo.setHours(0, 0, 0, 0);
        // 设置结束时间为今天的23:59
        now.setHours(23, 59, 0, 0);
        
        this.startTimeInput.value = this.formatDateTimeLocal(weekAgo);
        this.endTimeInput.value = this.formatDateTimeLocal(now);
        
        // 更新数据预览
        this.updateDataPreview();
    }

    initDatabaseConfig() {
        // 初始化数据库配置显示状态
        this.toggleDatabaseConfig();
        this.toggleCustomDatabaseConfig();
        this.toggleCustomTimeField();
        this.toggleCustomResultConfig();
    }

    toggleDatabaseConfig() {
        const dataSource = this.dataSourceSelect.value;
        const databaseConfig = document.getElementById('databaseConfig');
        
        if (dataSource === '舆情数据库') {
            databaseConfig.style.display = 'block';
            this.databaseTypeSelect.value = 'sqlite';
        } else if (dataSource === '自定义数据库') {
            databaseConfig.style.display = 'block';
            this.databaseTypeSelect.value = 'mysql';
        } else if (dataSource === '外部API') {
            databaseConfig.style.display = 'none';
        }
        
        this.toggleCustomDatabaseConfig();
    }

    toggleCustomDatabaseConfig() {
        const databaseType = this.databaseTypeSelect.value;
        
        if (databaseType === 'sqlite') {
            this.customDatabaseConfig.classList.add('hidden');
        } else {
            this.customDatabaseConfig.classList.remove('hidden');
        }
    }

    toggleCustomTimeField() {
        const timeField = this.timeFieldSelect.value;
        
        if (timeField === 'custom') {
            this.customTimeField.classList.remove('hidden');
        } else {
            this.customTimeField.classList.add('hidden');
        }
    }

    toggleCustomResultConfig() {
        const resultDatabase = this.resultDatabaseSelect.value;
        
        if (resultDatabase === 'custom') {
            this.customResultConfig.classList.remove('hidden');
        } else {
            this.customResultConfig.classList.add('hidden');
        }
    }

    async updateDataPreview() {
        const startTime = this.startTimeInput.value;
        const endTime = this.endTimeInput.value;
        
        if (!startTime || !endTime) {
            this.dataPreview.classList.add('hidden');
            return;
        }
        
        try {
            // 显示数据预览区域
            this.dataPreview.classList.remove('hidden');
            
            // 更新时间范围显示，精确到分钟
            const startDate = new Date(startTime);
            const endDate = new Date(endTime);
            
            // 使用标准化的时间显示格式，确保与查询参数一致
            const startFormatted = this.formatDisplayTime(startDate);
            const endFormatted = this.formatDisplayTime(endDate);
            this.selectedTimeRange.textContent = `${startFormatted} - ${endFormatted}`;
            
            // 查询数据量
            await this.queryDataCount();
            
        } catch (error) {
            console.error('更新数据预览失败:', error);
            this.dataCount.textContent = '查询失败';
            this.estimatedProcessTime.textContent = '--';
        }
    }

    async queryDataCount() {
        try {
            const timeField = this.timeFieldSelect.value === 'custom' 
                ? this.customTimeFieldName.value 
                : this.timeFieldSelect.value;
            
            if (!timeField) {
                throw new Error('请选择时间字段');
            }
            
            const startTime = this.startTimeInput.value;
            const endTime = this.endTimeInput.value;
            
            if (!startTime || !endTime) {
                throw new Error('请选择时间范围');
            }
            
            console.log('查询数据量参数:', { timeField, startTime, endTime });
            
            // 使用正确的API端点和参数格式，添加缓存清除参数
            const params = {
                time_field: timeField,
                start_time: startTime,
                end_time: endTime,
                _t: Date.now() // 添加时间戳防止缓存
            };
            
            const response = await fetch(`/api/database/data-count?${new URLSearchParams(params)}`, {
                cache: 'no-cache', // 禁用浏览器缓存
                headers: {
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            console.log('API响应结果:', result);
            
            if (result.success) {
                // 更新数据量显示
                this.dataCount.textContent = result.total.toLocaleString();
                
                // 计算预计处理时间（基于实际数据量，每条数据平均处理时间0.1秒）
                const estimatedSeconds = Math.ceil(result.total * 0.1);
                if (estimatedSeconds < 60) {
                    this.estimatedProcessTime.textContent = `${estimatedSeconds} 秒`;
                } else {
                    const estimatedMinutes = Math.ceil(estimatedSeconds / 60);
                    this.estimatedProcessTime.textContent = `${estimatedMinutes} 分钟`;
                }
                
                console.log(`数据量查询成功: ${result.total} 条记录`);
        } else {
                throw new Error(result.error || '查询失败');
            }
        } catch (error) {
            console.error('查询数据量失败:', error);
            this.dataCount.textContent = '查询失败';
            this.estimatedProcessTime.textContent = '--';
            this.showError(`查询数据量失败: ${error.message}`);
        }
    }

    formatDateTimeLocal(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        
        return `${year}-${month}-${day}T${hours}:${minutes}`;
    }
    
    formatDisplayTime(date) {
        const year = date.getFullYear();
        const month = date.getMonth() + 1;
        const day = date.getDate();
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        
        return `${year}/${month}/${day} ${hours}:${minutes}`;
    }

    // 快速时间范围设置函数（同时挂到window，供内联onclick使用）
    setQuickTimeRange(range) {
        const now = new Date();
        let startDate = new Date();
        let endDate = new Date();
        
        switch (range) {
            case 'today':
                startDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
                startDate.setHours(0, 0, 0, 0);
                endDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
                endDate.setHours(23, 59, 0, 0);
                break;
            case 'yesterday':
                startDate = new Date(now.getTime() - 24 * 60 * 60 * 1000);
                startDate.setHours(0, 0, 0, 0);
                endDate = new Date(startDate.getTime() + 24 * 60 * 60 * 1000 - 1000);
                endDate.setHours(23, 59, 0, 0);
                break;
            case 'week':
                // 最近7天：从7天前开始，到今天结束（包含今天）
                startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                startDate.setHours(0, 0, 0, 0);
                endDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
                endDate.setHours(23, 59, 0, 0);
                break;
            case 'month':
                // 最近30天：从30天前开始，到今天结束（包含今天）
                startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
                startDate.setHours(0, 0, 0, 0);
                endDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
                endDate.setHours(23, 59, 0, 0);
                break;
        }
        
        this.startTimeInput.value = this.formatDateTimeLocal(startDate);
        this.endTimeInput.value = this.formatDateTimeLocal(endDate);
        
        // 更新数据预览
        this.updateDataPreview();
    }

    // 暴露到全局，兼容模板内联按钮
    static exposeGlobals(instance) {
        if (typeof window !== 'undefined') {
            window.setQuickTimeRange = (range) => instance.setQuickTimeRange(range);
        }
    }

    showTaskConfirm() {
        // 验证配置
        if (!this.validateConfig()) {
            return;
        }
        
        // 填充确认信息
        this.confirmDataSource.textContent = this.dataSourceSelect.value;
        
        const startTime = new Date(this.startTimeInput.value);
        const endTime = new Date(this.endTimeInput.value);
        
        // 使用标准化的时间显示格式
        const startFormatted = this.formatDisplayTime(startTime);
        const endFormatted = this.formatDisplayTime(endTime);
        this.confirmDataRange.textContent = `${startFormatted} - ${endFormatted}`;
        
        // 分析模块
        const modules = [];
        if (this.enableSentiment.checked) modules.push('情感分析');
        if (this.enableTags.checked) modules.push('标签分类');
        if (this.enableCompanies.checked) modules.push('企业识别');
        if (this.enableDuplication.checked) modules.push('重复度检测');
        this.confirmAnalysisModules.textContent = modules.join('、');
        
        // 数据量
        this.confirmDataCount.textContent = this.dataCount.textContent;
        
        // 显示模态框
        this.taskConfirmModal.classList.remove('hidden');
    }

    hideTaskConfirm() {
        // 隐藏任务确认模态框
        this.taskConfirmModal.classList.add('hidden');
    }

    validateConfig() {
        // 验证时间范围
        if (!this.startTimeInput.value || !this.endTimeInput.value) {
            alert('请选择时间范围');
                return false;
            }
            
        const startTime = new Date(this.startTimeInput.value);
        const endTime = new Date(this.endTimeInput.value);
            
        if (startTime >= endTime) {
            alert('开始时间必须早于结束时间');
                return false;
        }
        
        // 验证自定义时间字段
        if (this.timeFieldSelect.value === 'custom' && !this.customTimeFieldName.value.trim()) {
            alert('请输入自定义时间字段名');
            return false;
        }
        
        // 验证数据库配置
        if (this.dataSourceSelect.value !== '外部API') {
            if (this.databaseTypeSelect.value !== 'sqlite') {
                if (!this.databaseHost.value || !this.databasePort.value || !this.databaseName.value) {
                    alert('请填写完整的数据库连接信息');
                    return false;
                }
            }
        }
        
        // 验证结果存储配置
        if (this.resultDatabaseSelect.value === 'custom') {
            if (!this.resultDbHost.value || !this.resultDbPort.value || !this.resultDbName.value) {
                alert('请填写完整的结果数据库连接信息');
                return false;
            }
        }
        
        return true;
    }

    async startTask() {
        this.hideTaskConfirm();
        
        // 准备任务配置 - 只发送后端API需要的参数
        const taskConfig = {
            data_source: this.dataSourceSelect.value,
            start_time: this.startTimeInput.value,
            end_time: this.endTimeInput.value,
            enable_sentiment: this.enableSentiment.checked,
            enable_tags: this.enableTags.checked,
            enable_companies: this.enableCompanies.checked
        };
        
        // 开始任务
        this.isRunning = true;
        this.startTime = new Date();
        this.processedCount = 0;
        this.errorCount = 0;
        
        this.updateTaskStatus('running');
        this.showExecutionProgress();
        this.clearLog();
        this.addLogEntry('开始执行批量解析任务...');
        
        try {
            const response = await fetch('/api/batch_parse', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                },
                cache: 'no-cache',
                body: JSON.stringify(taskConfig)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            this.handleStreamData(data);
                        } catch (e) {
                            console.error('解析流数据失败:', e);
                        }
                    }
                }
            }
            
        } catch (error) {
            this.addLogEntry(`任务执行失败: ${error.message}`, 'error');
            this.updateTaskStatus('error');
        }
    }

    handleStreamData(data) {
        switch (data.type) {
            case 'start':
                this.addLogEntry(data.message);
                break;
                
            case 'progress':
                this.updateProgress(data.current, data.total, data.percentage);
                break;
                
            case 'log':
                this.addLogEntry(data.message);
                break;
                
            case 'complete':
                this.markTaskComplete(data.total_processed);
                // 保存会话ID用于导出
                if (data.session_id) {
                    window.currentSessionId = data.session_id;
                    console.log('保存会话ID:', data.session_id);
                }
                break;
        }
    }

    updateProgress(current, total, percentage) {
        this.processedCount = current;
        this.totalCount = total;
        
        // 更新进度条
        this.overallProgress.style.width = `${percentage}%`;
        this.progressText.textContent = `${Math.round(percentage)}%`;
        
        // 更新统计信息
        this.processedDataSpan.textContent = current;
        this.totalDataSpan.textContent = total;
        
        const successRate = current > 0 ? (((current - this.errorCount) / current) * 100).toFixed(1) : 0;
        this.successRateSpan.textContent = `${successRate}%`;
        
        // 更新当前处理项信息
        this.currentItemInfo.innerHTML = `
            <p><strong>正在处理第 ${current} 条数据</strong></p>
            <p>进度: ${current}/${total} (${Math.round(percentage)}%)</p>
            <p>预计剩余时间: ${this.calculateEstimatedTime(percentage)}</p>
        `;
        
        // 添加日志
        this.addLogEntry(`处理进度: ${current}/${total} (${Math.round(percentage)}%)`);
    }

    calculateEstimatedTime(percentage) {
        if (percentage <= 0 || percentage >= 100) return '--';
        
        const elapsed = (new Date() - this.startTime) / 1000; // 秒
        const remaining = (elapsed / percentage) * (100 - percentage);
        
        if (remaining < 60) {
            return `${Math.round(remaining)}秒`;
        } else if (remaining < 3600) {
            return `${Math.round(remaining / 60)}分钟`;
        } else {
            return `${Math.round(remaining / 3600)}小时`;
        }
    }



    markTaskComplete(totalProcessed) {
        this.isRunning = false;
        const totalTime = new Date() - this.startTime;
        
        // 更新最终统计
        this.finalTotal.textContent = totalProcessed;
        this.finalSuccess.textContent = totalProcessed - this.errorCount;
        this.finalFailed.textContent = this.errorCount;
        this.finalTime.textContent = this.formatDuration(totalTime);
        
        // 隐藏执行进度，显示完成页面
        this.executionProgress.classList.add('hidden');
        this.taskCompleteSection.classList.remove('hidden');
        
        this.addLogEntry('任务执行完成！', 'success');
        this.updateTaskStatus('completed');
    }

    formatDuration(milliseconds) {
        const seconds = Math.floor(milliseconds / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        
        if (hours > 0) {
            return `${hours}小时${minutes % 60}分钟`;
        } else if (minutes > 0) {
            return `${minutes}分钟${seconds % 60}秒`;
        } else {
            return `${seconds}秒`;
        }
    }

    stopTask() {
        if (confirm('确定要停止当前任务吗？')) {
            this.isRunning = false;
            this.updateTaskStatus('stopped');
            this.addLogEntry('任务已手动停止', 'warning');
        }
    }

    resetTask() {
        if (confirm('确定要重置任务配置吗？')) {
            // 重置表单
            this.dataSourceSelect.value = '舆情数据库';
            this.enableSentiment.checked = true;
            this.enableTags.checked = true;
            this.enableCompanies.checked = true;
            
            
            // 重置时间范围
            const now = new Date();
            const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
            this.startTimeInput.value = this.formatDateTimeLocal(weekAgo);
            this.endTimeInput.value = this.formatDateTimeLocal(now);
            this.updateDataPreview();

            // 重置数据库配置
            this.databaseTypeSelect.value = 'sqlite';
            this.customDatabaseConfig.classList.add('hidden');
            this.databaseHost.value = '';
            this.databasePort.value = '';
            this.databaseName.value = '';
            this.databaseUser.value = '';
            this.databasePassword.value = '';

            // 重置分析模块
            this.enableSentiment.checked = true;
            this.enableTags.checked = true;
            this.enableCompanies.checked = true;
            this.enableDuplication.checked = false;

            // 重置结果存储配置
            this.resultDatabaseSelect.value = '舆情数据库';
            this.customResultConfig.classList.add('hidden');
            this.resultDbHost.value = '';
            this.resultDbPort.value = '';
            this.resultDbName.value = '';
            this.resultDbUser.value = '';
            this.resultDbPassword.value = '';
            
            // 重置状态
            this.isRunning = false;
            this.processedCount = 0;
            this.totalCount = 0;
            this.errorCount = 0;
            
            this.updateTaskStatus('idle');
            this.hideExecutionProgress();
            this.hideTaskComplete();
            this.clearLog();
            
            // 重置统计
            this.totalDataSpan.textContent = '0';
            this.processedDataSpan.textContent = '0';
            this.successRateSpan.textContent = '0%';
            this.estimatedTimeSpan.textContent = '--';
        }
    }

    updateTaskStatus(status) {
        const statusIndicator = this.taskStatus.querySelector('.status-indicator');
        const icon = statusIndicator.querySelector('i');
        const text = statusIndicator.querySelector('span');
        
        // 移除所有状态类
        icon.className = 'fas fa-circle';
        statusIndicator.className = 'status-indicator';
        
        switch (status) {
            case 'idle':
                icon.classList.add('status-idle');
                text.textContent = '等待开始';
                break;
            case 'running':
                icon.classList.add('status-running');
                text.textContent = '正在执行';
                break;
            case 'completed':
                icon.classList.add('status-completed');
                text.textContent = '执行完成';
                break;
            case 'error':
                icon.classList.add('status-error');
                text.textContent = '执行出错';
                break;
            case 'stopped':
                icon.classList.add('status-stopped');
                text.textContent = '已停止';
                break;
        }
    }

    showExecutionProgress() {
        this.executionProgress.classList.remove('hidden');
        this.startTaskBtn.classList.add('hidden');
        this.stopTaskBtn.classList.remove('hidden');
    }

    hideExecutionProgress() {
        this.executionProgress.classList.add('hidden');
        this.startTaskBtn.classList.remove('hidden');
        this.stopTaskBtn.classList.add('hidden');
    }

    hideTaskComplete() {
        this.taskCompleteSection.classList.add('hidden');
    }

    clearLog() {
        this.logContainer.innerHTML = `
            <div class="log-entry">
                <span class="log-time">--:--:--</span>
                <span class="log-message">系统就绪，等待任务开始...</span>
            </div>
        `;
    }

    exportLog() {
        const logContent = Array.from(this.logContainer.children)
            .map(entry => {
                const time = entry.querySelector('.log-time').textContent;
                const message = entry.querySelector('.log-message').textContent;
                return `[${time}] ${message}`;
            })
            .join('\n');
        
        const blob = new Blob([logContent], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `parsing_task_log_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.txt`;
        a.click();
        URL.revokeObjectURL(url);
    }

    exportResults() {
        // 这里应该实现导出结果的功能
        alert('导出功能开发中...');
    }

    async handleExportResults() {
        try {
            const sessionId = window.currentSessionId;
            if (!sessionId) {
                alert('尚未获取到会话ID，无法按会话导出');
                return;
            }
            const url = `/api/results/export/deduplicated?format=json&session_id=${encodeURIComponent(sessionId)}`;
            const response = await fetch(url, { method: 'POST' });
            if (!response.ok) {
                const err = await response.json().catch(() => ({}));
                throw new Error(err.detail || `导出失败 (${response.status})`);
            }
            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = `deduplicated_results_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(downloadUrl);
            this.addLogEntry('success', '去重数据导出完成！');
        } catch (e) {
            this.addLogEntry('error', `导出失败: ${e.message}`);
            alert(`导出失败: ${e.message}`);
        }
    }

    async analyzeLatestData() {
        try {
            // 显示执行进度
            this.showExecutionProgress();
            this.updateTaskStatus('running');
            
            // 获取分析模块配置
            const analysisModules = [];
            if (this.enableSentiment.checked) analysisModules.push('sentiment');
            if (this.enableTags.checked) analysisModules.push('tags');
            if (this.enableCompanies.checked) analysisModules.push('companies');
            if (this.enableDuplication.checked) analysisModules.push('duplication');
            
            // 获取时间字段
            const timeField = this.timeFieldSelect.value === 'custom' 
                ? this.customTimeFieldName.value 
                : this.timeFieldSelect.value;
            
            if (!timeField) {
                throw new Error('请选择时间字段');
            }
            
            // 构建分析请求
            const requestData = {
                time_field: timeField,
                start_time: this.startTimeInput.value,
                end_time: this.endTimeInput.value,
                limit: 100,  // 分析最新100条数据
                analysis_modules: analysisModules
            };
            
            // 调用分析API
            const response = await fetch('/api/analysis/analyze-latest', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });
            
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.detail || '分析失败');
            }
            
            // 显示分析结果
            this.showAnalysisResults(result);
            
            // 更新任务状态
            this.updateTaskStatus('completed');
            this.hideExecutionProgress();
            
            // 记录日志
            this.addLogEntry('success', `成功分析 ${result.total} 条数据，耗时 ${result.analysis_results.processing_time} 秒`);
            
        } catch (error) {
            console.error('分析最新数据失败:', error);
            this.updateTaskStatus('error');
            this.hideExecutionProgress();
            this.addLogEntry('error', `分析失败: ${error.message}`);
        }
    }

    showAnalysisResults(result) {
        // 创建结果展示区域
        const resultsContainer = document.createElement('div');
        resultsContainer.className = 'analysis-results';
        resultsContainer.innerHTML = `
            <h3><i class="fas fa-chart-line"></i> 分析结果</h3>
            <div class="results-summary">
                <div class="result-item">
                    <span class="label">总处理数据:</span>
                    <span class="value">${result.total}</span>
                </div>
                <div class="result-item">
                    <span class="label">处理时间:</span>
                    <span class="value">${result.analysis_results.processing_time} 秒</span>
                </div>
            </div>
            <div class="results-details">
                <h4>详细结果</h4>
                <div class="result-section">
                    <h5>情感分析</h5>
                    <p>处理了 ${result.analysis_results.sentiment_analysis.length} 条数据</p>
                </div>
                <div class="result-section">
                    <h5>标签分类</h5>
                    <p>处理了 ${result.analysis_results.tag_analysis.length} 条数据</p>
                </div>
                <div class="result-section">
                    <h5>企业识别</h5>
                    <p>处理了 ${result.analysis_results.company_analysis.length} 条数据</p>
                </div>
                <div class="result-section">
                    <h5>重复度检测</h5>
                    <p>处理了 ${result.analysis_results.duplication_analysis.length} 条数据</p>
                </div>
            </div>
        `;
        
        // 插入到页面中
        const mainContent = document.querySelector('.main-content');
        mainContent.appendChild(resultsContainer);
    }

    addLogEntry(type, message) {
        // 处理不同的调用方式
        if (typeof type === 'string' && typeof message === 'string') {
            // 带类型的调用: addLogEntry('success', 'message')
            this._createLogEntry(type, message);
        } else if (typeof type === 'string') {
            // 不带类型的调用: addLogEntry('message')
            this._createLogEntry('info', type);
        } else {
            // 默认情况
            this._createLogEntry('info', '未知日志消息');
        }
    }

    _createLogEntry(type, message) {
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry log-${type}`;
        
        const time = new Date().toLocaleTimeString();
        logEntry.innerHTML = `
            <span class="log-time">${time}</span>
            <span class="log-message">${message}</span>
        `;
        
        this.logContainer.appendChild(logEntry);
        this.logContainer.scrollTop = this.logContainer.scrollHeight;
    }

    newTask() {
        this.resetTask();
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    const manager = new ParsingTaskManager();
    ParsingTaskManager.exposeGlobals(manager);
});
