# -*- coding: utf-8 -*-

import sqlite3
import os
from datetime import datetime
import json

class ResultDatabase:
    def __init__(self, db_path="data/analysis_results.db"):
        """Initialize database connection"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database table structure"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create results table with enhanced structure
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sentiment_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        original_id INTEGER,
                        title TEXT,
                        content TEXT,
                        summary TEXT,
                        source TEXT,
                        publish_time TEXT,
                        sentiment_level TEXT,
                        sentiment_reason TEXT,
                        
                        -- 14个标签匹配结果字段
                        tag_同业竞争 TEXT DEFAULT '否',
                        tag_股权与控制权 TEXT DEFAULT '否',
                        tag_关联交易 TEXT DEFAULT '否',
                        tag_历史沿革与股东核查 TEXT DEFAULT '否',
                        tag_重大违法违规 TEXT DEFAULT '否',
                        tag_收入与成本 TEXT DEFAULT '否',
                        tag_财务内控不规范 TEXT DEFAULT '否',
                        tag_客户与供应商 TEXT DEFAULT '否',
                        tag_资产质量与减值 TEXT DEFAULT '否',
                        tag_研发与技术 TEXT DEFAULT '否',
                        tag_募集资金用途 TEXT DEFAULT '否',
                        tag_突击分红与对赌协议 TEXT DEFAULT '否',
                        tag_市场传闻与负面报道 TEXT DEFAULT '否',
                        tag_行业政策与环境 TEXT DEFAULT '否',
                        
                        -- 14个标签原因字段
                        reason_同业竞争 TEXT DEFAULT '无',
                        reason_股权与控制权 TEXT DEFAULT '无',
                        reason_关联交易 TEXT DEFAULT '无',
                        reason_历史沿革与股东核查 TEXT DEFAULT '无',
                        reason_重大违法违规 TEXT DEFAULT '无',
                        reason_收入与成本 TEXT DEFAULT '无',
                        reason_财务内控不规范 TEXT DEFAULT '无',
                        reason_客户与供应商 TEXT DEFAULT '无',
                        reason_资产质量与减值 TEXT DEFAULT '无',
                        reason_研发与技术 TEXT DEFAULT '无',
                        reason_募集资金用途 TEXT DEFAULT '无',
                        reason_突击分红与对赌协议 TEXT DEFAULT '无',
                        reason_市场传闻与负面报道 TEXT DEFAULT '无',
                        reason_行业政策与环境 TEXT DEFAULT '无',
                        
                        -- 其他字段
                        companies TEXT,
                        duplicate_id TEXT,
                        duplication_rate REAL DEFAULT 0.0,
                        processing_time INTEGER DEFAULT 0,
                        analysis_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        processing_status TEXT DEFAULT 'completed',
                        session_id TEXT  -- 批量解析会话ID
                    )
                ''')
                
                # Create tags table for detailed tag information
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tag_matches (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        result_id INTEGER,
                        tag_name TEXT NOT NULL,
                        tag_value TEXT,
                        match_reason TEXT,
                        confidence REAL,
                        FOREIGN KEY (result_id) REFERENCES sentiment_results (id)
                    )
                ''')
                
                # Create error logs table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS error_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        error_type TEXT NOT NULL,
                        error_message TEXT,
                        query_text TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        stack_trace TEXT
                    )
                ''')
                
                # Create API stats table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS api_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        api_name TEXT NOT NULL,
                        call_count INTEGER DEFAULT 0,
                        success_count INTEGER DEFAULT 0,
                        error_count INTEGER DEFAULT 0,
                        last_called TIMESTAMP,
                        avg_response_time REAL
                    )
                ''')
                
                conn.commit()
                print(f"Database initialized successfully: {self.db_path}")
                
        except Exception as e:
            print(f"Database initialization failed: {e}")
            raise
    
    def save_result(self, original_id=None, title=None, content=None, summary=None, 
                   source=None, publish_time=None, sentiment_level=None, sentiment_reason=None,
                   companies=None, duplicate_id=None, duplication_rate=None, processing_time_ms=None,
                   tags=None, **kwargs):
        """Save sentiment analysis result with enhanced fields"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Prepare tag fields
                tag_fields = {}
                reason_fields = {}
                
                if tags and isinstance(tags, dict):
                    for key, value in tags.items():
                        if key.startswith('tag_'):
                            tag_fields[key] = value
                        elif key.startswith('reason_'):
                            reason_fields[key] = value
                
                # Build column names and values for all tag and reason fields
                tag_columns = ['tag_同业竞争', 'tag_股权与控制权', 'tag_关联交易', 'tag_历史沿革与股东核查',
                              'tag_重大违法违规', 'tag_收入与成本', 'tag_财务内控不规范', 'tag_客户与供应商',
                              'tag_资产质量与减值', 'tag_研发与技术', 'tag_募集资金用途', 'tag_突击分红与对赌协议',
                              'tag_市场传闻与负面报道', 'tag_行业政策与环境']
                
                reason_columns = ['reason_同业竞争', 'reason_股权与控制权', 'reason_关联交易', 'reason_历史沿革与股东核查',
                                 'reason_重大违法违规', 'reason_收入与成本', 'reason_财务内控不规范', 'reason_客户与供应商',
                                 'reason_资产质量与减值', 'reason_研发与技术', 'reason_募集资金用途', 'reason_突击分红与对赌协议',
                                 'reason_市场传闻与负面报道', 'reason_行业政策与环境']
                
                # Prepare values for tag and reason columns
                tag_values = [tag_fields.get(col, '否') for col in tag_columns]
                reason_values = [reason_fields.get(col, '无') for col in reason_columns]
                
                cursor.execute('''
                    INSERT INTO sentiment_results 
                    (original_id, title, content, summary, source, publish_time, sentiment_level, 
                     sentiment_reason, tag_同业竞争, tag_股权与控制权, tag_关联交易, tag_历史沿革与股东核查, tag_重大违法违规,
                     tag_收入与成本, tag_财务内控不规范, tag_客户与供应商, tag_资产质量与减值, tag_研发与技术,
                     tag_募集资金用途, tag_突击分红与对赌协议, tag_市场传闻与负面报道, tag_行业政策与环境,
                     reason_同业竞争, reason_股权与控制权, reason_关联交易, reason_历史沿革与股东核查, reason_重大违法违规,
                     reason_收入与成本, reason_财务内控不规范, reason_客户与供应商, reason_资产质量与减值, reason_研发与技术,
                     reason_募集资金用途, reason_突击分红与对赌协议, reason_市场传闻与负面报道, reason_行业政策与环境,
                     companies, duplicate_id, duplication_rate, processing_time, processing_status, session_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (original_id, title, content, summary, source, publish_time, sentiment_level,
                     sentiment_reason) + tuple(tag_values) + tuple(reason_values) + 
                     (companies, duplicate_id, duplication_rate, processing_time_ms, 'completed', kwargs.get('session_id')))
                
                result_id = cursor.lastrowid
                
                conn.commit()
                return result_id
                
        except Exception as e:
            print(f"Failed to save result: {e}")
            self.log_error("save_result_error", str(e), {"original_id": original_id, "title": title})
            return None
    
    def _save_tag_matches(self, cursor, result_id, tags):
        """Save individual tag matches"""
        try:
            for tag_name, tag_info in tags.items():
                if isinstance(tag_info, dict):
                    tag_value = tag_info.get('value', '')
                    match_reason = tag_info.get('reason', '')
                    confidence = tag_info.get('confidence', 0.0)
                else:
                    tag_value = str(tag_info)
                    match_reason = ''
                    confidence = 0.0
                
                cursor.execute('''
                    INSERT INTO tag_matches 
                    (result_id, tag_name, tag_value, match_reason, confidence)
                    VALUES (?, ?, ?, ?, ?)
                ''', (result_id, tag_name, tag_value, match_reason, confidence))
                
        except Exception as e:
            print(f"Failed to save tag matches: {e}")
    
    def log_error(self, error_type, error_message, query_text=None, stack_trace=None):
        """Log error information"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO error_logs 
                    (error_type, error_message, query_text, stack_trace)
                    VALUES (?, ?, ?, ?)
                ''', (error_type, error_message, query_text, stack_trace))
                
                conn.commit()
                
        except Exception as e:
            print(f"Failed to log error: {e}")
    
    def get_recent_results(self, limit=10):
        """Get recent analysis results"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM sentiment_results 
                    ORDER BY analysis_time DESC 
                    LIMIT ?
                ''', (limit,))
                
                return cursor.fetchall()
                
        except Exception as e:
            print(f"Failed to get results: {e}")
            return []
    
    def get_results_by_query(self, query_text):
        """Get results by query text"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM sentiment_results 
                    WHERE query_text LIKE ?
                    ORDER BY analysis_time DESC
                ''', (f'%{query_text}%',))
                
                return cursor.fetchall()
                
        except Exception as e:
            print(f"Failed to query results: {e}")
            return []
    
    def update_api_stats(self, api_name, success=True, response_time=None):
        """Update API call statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if record exists
                cursor.execute('SELECT * FROM api_stats WHERE api_name = ?', (api_name,))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing record
                    if success:
                        cursor.execute('''
                            UPDATE api_stats 
                            SET call_count = call_count + 1,
                                success_count = success_count + 1,
                                last_called = CURRENT_TIMESTAMP,
                                avg_response_time = CASE 
                                    WHEN avg_response_time IS NULL THEN ?
                                    ELSE (avg_response_time + ?) / 2
                                END
                            WHERE api_name = ?
                        ''', (response_time or 0, response_time or 0, api_name))
                    else:
                        cursor.execute('''
                            UPDATE api_stats 
                            SET call_count = call_count + 1,
                                error_count = error_count + 1,
                                last_called = CURRENT_TIMESTAMP
                            WHERE api_name = ?
                        ''', (api_name,))
                else:
                    # Create new record
                    if success:
                        cursor.execute('''
                            INSERT INTO api_stats 
                            (api_name, call_count, success_count, last_called, avg_response_time)
                            VALUES (?, 1, 1, CURRENT_TIMESTAMP, ?)
                        ''', (api_name, response_time or 0))
                    else:
                        cursor.execute('''
                            INSERT INTO api_stats 
                            (api_name, call_count, error_count, last_called)
                            VALUES (?, 1, 1, CURRENT_TIMESTAMP)
                        ''', (api_name,))
                
                conn.commit()
                
        except Exception as e:
            print(f"Failed to update API stats: {e}")
    
    def get_database_stats(self):
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total results
                cursor.execute('SELECT COUNT(*) FROM sentiment_results')
                total_results = cursor.fetchone()[0]
                
                # Successful results
                cursor.execute('SELECT COUNT(*) FROM sentiment_results WHERE processing_status = "completed"')
                successful_results = cursor.fetchone()[0]
                
                # Error logs
                cursor.execute('SELECT COUNT(*) FROM error_logs')
                total_errors = cursor.fetchone()[0]
                
                # API stats
                cursor.execute('SELECT * FROM api_stats')
                api_stats = cursor.fetchall()
                
                return {
                    'total_results': total_results,
                    'successful_results': successful_results,
                    'total_errors': total_errors,
                    'api_stats': api_stats
                }
                
        except Exception as e:
            print(f"Failed to get statistics: {e}")
            return {}
    
    def cleanup_old_records(self, days=30):
        """Clean up old records"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete error logs older than 30 days
                cursor.execute('''
                    DELETE FROM error_logs 
                    WHERE timestamp < datetime('now', '-{} days')
                '''.format(days))
                
                deleted_errors = cursor.rowcount
                
                conn.commit()
                print(f"Cleanup completed, deleted {deleted_errors} old error logs")
                
        except Exception as e:
            print(f"Failed to cleanup old records: {e}")
    
    def export_results(self, output_file="sentiment_results_export.json"):
        """Export results to JSON file"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM sentiment_results 
                    ORDER BY analysis_time DESC
                ''')
                
                results = cursor.fetchall()
                
                # Get column names
                columns = [description[0] for description in cursor.description]
                
                # Convert to list of dictionaries
                export_data = []
                for row in results:
                    row_dict = dict(zip(columns, row))
                    # Convert timestamp to string
                    if row_dict.get('analysis_time'):
                        row_dict['analysis_time'] = str(row_dict['analysis_time'])
                    export_data.append(row_dict)
                
                # Write to JSON file
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
                
                print(f"Results exported to: {output_file}")
                return True
                
        except Exception as e:
            print(f"Export failed: {e}")
            return False
    
    def get_analysis_results(self, page=1, page_size=50, search_keyword=None):
        """Get analysis results with pagination and search - enhanced with new structure"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 构建搜索条件
                where_clause = ""
                search_params = []
                
                if search_keyword and search_keyword.strip():
                    where_clause = """WHERE (
                        title LIKE ? OR 
                        content LIKE ? OR 
                        summary LIKE ? OR 
                        companies LIKE ?
                    )"""
                    search_term = f"%{search_keyword.strip()}%"
                    search_params = [search_term, search_term, search_term, search_term]
                
                # 获取总记录数
                count_query = f'SELECT COUNT(*) FROM sentiment_results {where_clause}'
                cursor.execute(count_query, search_params)
                total = cursor.fetchone()[0]
                
                # 计算分页
                offset = (page - 1) * page_size
                total_pages = (total + page_size - 1) // page_size
                
                # 获取标签名称列表
                tag_names = [
                    "同业竞争", "股权与控制权", "关联交易", "历史沿革与股东核查", "重大违法违规",
                    "收入与成本", "财务内控不规范", "客户与供应商", "资产质量与减值", "研发与技术",
                    "募集资金用途", "突击分红与对赌协议", "市场传闻与负面报道", "行业政策与环境"
                ]
                
                # 构建标签字段查询
                tag_fields = []
                reason_fields = []
                for tag_name in tag_names:
                    tag_fields.append(f'tag_{tag_name}')
                    reason_fields.append(f'reason_{tag_name}')
                
                all_tag_fields = ', '.join(tag_fields + reason_fields)
                
                # 使用新的表结构查询，包含搜索条件
                query_params = search_params + [page_size, offset]
                cursor.execute(f'''
                    SELECT 
                        id,
                        COALESCE(original_id, id) as original_id,
                        COALESCE(title, '无标题') as title,
                        COALESCE(content, '无内容') as content,
                        COALESCE(summary, '无摘要') as summary,
                        COALESCE(source, '未知来源') as source,
                        COALESCE(publish_time, '未知时间') as publish_time,
                        COALESCE(sentiment_level, '未知') as sentiment_level,
                        COALESCE(sentiment_reason, '无原因') as sentiment_reason,
                        COALESCE(companies, '') as companies,
                        COALESCE(duplicate_id, '无') as duplicate_id,
                        COALESCE(duplication_rate, 0.0) as duplication_rate,
                        COALESCE(processing_time, 0) as processing_time,
                        {all_tag_fields}
                    FROM sentiment_results 
                    {where_clause}
                    ORDER BY id DESC 
                    LIMIT ? OFFSET ?
                ''', query_params)
                
                results = cursor.fetchall()
                
                # Convert to list of dictionaries with proper format
                data = []
                for row in results:
                    # 构建基本字段
                    result_dict = {
                        'id': row[0],
                        'original_id': row[1],
                        'title': row[2],
                        'content': row[3],
                        'summary': row[4],
                        'source': row[5],
                        'publish_time': row[6],
                        'sentiment_level': row[7],
                        'sentiment_reason': row[8],
                        'companies': row[9],
                        'duplicate_id': row[10],
                        'duplication_rate': row[11],
                        'processing_time': row[12]
                    }
                    
                    # 添加标签字段（从第13个字段开始）
                    field_index = 13
                    for tag_name in tag_names:
                        result_dict[f'tag_{tag_name}'] = row[field_index] if field_index < len(row) else '否'
                        field_index += 1
                    
                    # 添加原因字段
                    for tag_name in tag_names:
                        result_dict[f'reason_{tag_name}'] = row[field_index] if field_index < len(row) else '无'
                        field_index += 1
                    
                    data.append(result_dict)
                
                return {
                    'success': True,
                    'data': data,
                    'total': total,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': total_pages
                }
                
        except Exception as e:
            print(f"Failed to get analysis results: {e}")
            return {
                'success': False,
                'message': str(e)
            }

    def get_analysis_result_by_id(self, result_id):
        """Get single analysis result by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 获取标签名称列表
                tag_names = [
                    "同业竞争", "股权与控制权", "关联交易", "历史沿革与股东核查", "重大违法违规",
                    "收入与成本", "财务内控不规范", "客户与供应商", "资产质量与减值", "研发与技术",
                    "募集资金用途", "突击分红与对赌协议", "市场传闻与负面报道", "行业政策与环境"
                ]
                
                # 构建标签字段查询
                tag_fields = []
                reason_fields = []
                for tag_name in tag_names:
                    tag_fields.append(f'tag_{tag_name}')
                    reason_fields.append(f'reason_{tag_name}')
                
                all_tag_fields = ', '.join(tag_fields + reason_fields)
                
                # 查询单条结果
                cursor.execute(f'''
                    SELECT 
                        id,
                        COALESCE(original_id, id) as original_id,
                        COALESCE(title, '无标题') as title,
                        COALESCE(content, '无内容') as content,
                        COALESCE(summary, '无摘要') as summary,
                        COALESCE(source, '未知来源') as source,
                        COALESCE(publish_time, '未知时间') as publish_time,
                        COALESCE(sentiment_level, '未知') as sentiment_level,
                        COALESCE(sentiment_reason, '无原因') as sentiment_reason,
                        COALESCE(companies, '') as companies,
                        COALESCE(duplicate_id, '无') as duplicate_id,
                        COALESCE(duplication_rate, 0.0) as duplication_rate,
                        COALESCE(processing_time, 0) as processing_time,
                        {all_tag_fields}
                    FROM sentiment_results 
                    WHERE id = ?
                ''', (result_id,))
                
                row = cursor.fetchone()
                
                if not row:
                    return {
                        'success': False,
                        'message': f'未找到ID为 {result_id} 的结果'
                    }
                
                # 构建结果字典
                result_dict = {
                    'id': row[0],
                    'original_id': row[1],
                    'title': row[2],
                    'content': row[3],
                    'summary': row[4],
                    'source': row[5],
                    'publish_time': row[6],
                    'sentiment_level': row[7],
                    'sentiment_reason': row[8],
                    'companies': row[9],
                    'duplicate_id': row[10],
                    'duplication_rate': row[11],
                    'processing_time': row[12]
                }
                
                # 添加标签字段（从第13个字段开始）
                field_index = 13
                for tag_name in tag_names:
                    result_dict[f'tag_{tag_name}'] = row[field_index] if field_index < len(row) else '否'
                    result_dict[f'reason_{tag_name}'] = row[field_index + len(tag_names)] if field_index < len(row) else ''
                    field_index += 1
                
                # 构建标签列表
                tags = []
                for tag_name in tag_names:
                    tag_key = f'tag_{tag_name}'
                    if result_dict.get(tag_key) == '是':
                        tags.append(tag_name)
                
                result_dict['tags'] = tags
                
                return {
                    'success': True,
                    'data': result_dict
                }
                
        except Exception as e:
            print(f"Error getting analysis result by ID: {e}")
            return {
                'success': False,
                'message': f'获取分析结果失败: {str(e)}'
            }
    
    def get_analysis_results_by_original_id(self, original_id):
        """
        根据original_id查询分析结果
        
        Args:
            original_id: 原始ID
            
        Returns:
            list: 匹配的结果列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM sentiment_results 
                    WHERE original_id = ?
                    ORDER BY analysis_time DESC
                ''', (original_id,))
                
                columns = [description[0] for description in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    result = dict(zip(columns, row))
                    results.append(result)
                
                return results
                
        except Exception as e:
            print(f"Failed to get analysis results by original_id: {e}")
            return []

    def _get_tag_matches(self, result_id):
        """Get detailed tag matches for a specific result"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT tag_name, tag_value, match_reason, confidence
                    FROM tag_matches 
                    WHERE result_id = ?
                    ORDER BY confidence DESC
                ''', (result_id,))
                
                matches = cursor.fetchall()
                tag_details = {}
                
                for match in matches:
                    tag_name, tag_value, match_reason, confidence = match
                    tag_details[tag_name] = {
                        'value': tag_value,
                        'reason': match_reason,
                        'confidence': confidence
                    }
                
                return tag_details
                
        except Exception as e:
            print(f"Failed to get tag matches: {e}")
            return {}
    
    def save_analysis_result(self, data):
        """Save analysis result - enhanced version with new structure"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 提取基本字段
                original_id = data.get('original_id')
                
                # 检查是否已存在相同original_id的记录
                if original_id is not None:
                    cursor.execute('SELECT id FROM sentiment_results WHERE original_id = ?', (original_id,))
                    existing_record = cursor.fetchone()
                    if existing_record:
                        return {
                            'success': False,
                            'message': f'记录已存在，original_id: {original_id}，跳过重复保存',
                            'duplicate': True,
                            'existing_id': existing_record[0]
                        }
                title = data.get('title', '无标题')
                content = data.get('content', '无内容')
                summary = data.get('summary', '无摘要')
                source = data.get('source', '未知来源')
                publish_time = data.get('publish_time', '未知时间')
                sentiment_level = data.get('sentiment_level', '未知')
                sentiment_reason = data.get('sentiment_reason', '无原因')
                companies = data.get('companies', '')
                duplicate_id = data.get('duplicate_id', '无')
                duplication_rate = data.get('duplication_rate', 0.0)
                processing_time = data.get('processing_time', 0)
                session_id = data.get('session_id')  # 会话ID
                
                # 提取标签数据
                tag_results = data.get('tag_results', {})
                
                # 准备标签字段和原因字段的值
                tag_fields = {}
                reason_fields = {}
                
                # 获取所有14个标签的配置
                tag_names = [
                    "同业竞争", "股权与控制权", "关联交易", "历史沿革与股东核查", "重大违法违规",
                    "收入与成本", "财务内控不规范", "客户与供应商", "资产质量与减值", "研发与技术",
                    "募集资金用途", "突击分红与对赌协议", "市场传闻与负面报道", "行业政策与环境"
                ]
                
                # 处理标签结果
                for tag_name in tag_names:
                    if tag_name in tag_results:
                        tag_result = tag_results[tag_name]
                        tag_fields[f'tag_{tag_name}'] = '是' if tag_result.get('belongs', False) else '否'
                        reason_fields[f'reason_{tag_name}'] = tag_result.get('reason', '无')
                    else:
                        tag_fields[f'tag_{tag_name}'] = '否'
                        reason_fields[f'reason_{tag_name}'] = '无'
                
                # 构建插入语句
                insert_fields = [
                    'original_id', 'title', 'content', 'summary', 'source', 'publish_time',
                    'sentiment_level', 'sentiment_reason', 'companies', 'duplicate_id',
                    'duplication_rate', 'processing_time', 'session_id'
                ]
                
                # 添加标签字段
                insert_fields.extend(tag_fields.keys())
                insert_fields.extend(reason_fields.keys())
                
                # 准备值列表
                values = [
                    original_id, title, content, summary, source, publish_time,
                    sentiment_level, sentiment_reason, companies, duplicate_id,
                    duplication_rate, processing_time, session_id
                ]
                
                # 添加标签值
                values.extend(tag_fields.values())
                values.extend(reason_fields.values())
                
                # 构建SQL语句
                placeholders = ', '.join(['?'] * len(values))
                field_names = ', '.join(insert_fields)
                
                cursor.execute(f'''
                    INSERT INTO sentiment_results ({field_names})
                    VALUES ({placeholders})
                ''', values)
                
                result_id = cursor.lastrowid
                conn.commit()
                
                return {
                    'success': True,
                    'message': '结果保存成功',
                    'id': result_id
                }
                
        except Exception as e:
            print(f"Failed to save analysis result: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def get_database_info(self):
        """Get database information - compatible with existing API"""
        try:
            import os
            
            # Get file size
            file_size_bytes = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            file_size_mb = round(file_size_bytes / (1024 * 1024), 2)
            
            # Get table information
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get table names
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                # Get total records
                total_records = 0
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    total_records += cursor.fetchone()[0]
            
            return {
                'database_path': self.db_path,
                'file_size_mb': file_size_mb,
                'tables': tables,
                'total_records': total_records
            }
            
        except Exception as e:
            print(f"Failed to get database info: {e}")
            return {
                'database_path': self.db_path,
                'file_size_mb': 0,
                'tables': [],
                'total_records': 0
            }
    
    def get_sentiment_statistics(self):
        """Get sentiment analysis statistics - compatible with existing API"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get total analyses
                cursor.execute('SELECT COUNT(*) FROM sentiment_results')
                total_analyses = cursor.fetchone()[0]
                
                # Get sentiment distribution
                cursor.execute('''
                    SELECT sentiment_label, COUNT(*) as count
                    FROM sentiment_results 
                    WHERE sentiment_label IS NOT NULL
                    GROUP BY sentiment_label
                ''')
                
                sentiment_distribution = {}
                for row in cursor.fetchall():
                    sentiment_distribution[row[0]] = row[1]
                
                # Get average processing time (placeholder)
                avg_processing_time_ms = 0
                
                return {
                    'total_analyses': total_analyses,
                    'sentiment_distribution': sentiment_distribution,
                    'avg_processing_time_ms': avg_processing_time_ms
                }
                
        except Exception as e:
            print(f"Failed to get sentiment statistics: {e}")
            return {
                'total_analyses': 0,
                'sentiment_distribution': {},
                'avg_processing_time_ms': 0
            }
    
    def cleanup_old_results(self, days=30):
        """Clean up old results - compatible with existing API"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete old results
                cursor.execute('''
                    DELETE FROM sentiment_results 
                    WHERE analysis_time < datetime('now', '-{} days')
                '''.format(days))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                print(f"Cleanup completed, deleted {deleted_count} old results")
                return deleted_count
                
        except Exception as e:
            print(f"Failed to cleanup old results: {e}")
            return 0

    def delete_analysis_result(self, result_id):
        """
        删除指定的分析结果记录
        
        Args:
            result_id: 记录ID
            
        Returns:
            dict: 删除结果
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 检查记录是否存在
                cursor.execute('SELECT id FROM sentiment_results WHERE id = ?', (result_id,))
                if not cursor.fetchone():
                    return {
                        'success': False,
                        'message': f'记录ID {result_id} 不存在'
                    }
                
                # 删除记录
                cursor.execute('DELETE FROM sentiment_results WHERE id = ?', (result_id,))
                conn.commit()
                
                if cursor.rowcount > 0:
                    return {
                        'success': True,
                        'message': f'成功删除记录ID {result_id}'
                    }
                else:
                    return {
                        'success': False,
                        'message': f'删除记录ID {result_id} 失败'
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'message': f'删除记录时发生错误: {str(e)}'
            }
    
    def get_results_by_session(self, session_id):
        """
        按会话ID获取分析结果
        
        Args:
            session_id: 会话ID
            
        Returns:
            dict: 查询结果
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 查询该会话的所有记录
                cursor.execute('''
                    SELECT * FROM sentiment_results 
                    WHERE session_id = ? 
                    ORDER BY id DESC
                ''', (session_id,))
                
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
                
                # 转换为字典列表
                results = []
                for row in rows:
                    result = dict(zip(columns, row))
                    results.append(result)
                
                return {
                    'success': True,
                    'data': results,
                    'total': len(results),
                    'session_id': session_id
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'获取会话数据时发生错误: {str(e)}',
                'data': [],
                'total': 0
            }

    def search_analysis_results(self, search_conditions=None, page=1, page_size=20):
        """Advanced search with multiple conditions"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 构建搜索条件
                where_clauses = []
                search_params = []

                if search_conditions:
                    # 关键词搜索
                    if 'query' in search_conditions and search_conditions['query']:
                        query = search_conditions['query'].strip()
                        if query:
                            where_clauses.append("""(
                            title LIKE ? OR
                            content LIKE ? OR
                            summary LIKE ? OR
                            companies LIKE ?
                        )""")
                        search_term = f"%{query}%"
                        search_params.extend([search_term, search_term, search_term, search_term])

                # 情感等级搜索
                if 'sentiment_level' in search_conditions and search_conditions['sentiment_level']:
                    sentiment = search_conditions['sentiment_level']
                    where_clauses.append("sentiment_level = ?")
                    search_params.append(sentiment)

                # 标签搜索 - 检查是否有匹配的标签
                if 'tag' in search_conditions and search_conditions['tag']:
                    tag = search_conditions['tag']
                    where_clauses.append(f"tag_{tag} = '是'")

                # 日期范围搜索
                if 'date_range' in search_conditions and search_conditions['date_range']:
                    date_range = search_conditions['date_range']
                    if 'start_date' in date_range and 'end_date' in date_range:
                        where_clauses.append("publish_time >= ? AND publish_time <= ?")
                        search_params.extend([date_range['start_date'], date_range['end_date']])

                # 组合WHERE条件
                where_clause = ""
                if where_clauses:
                    where_clause = "WHERE " + " AND ".join(where_clauses)

                # 获取总记录数
                count_query = f'SELECT COUNT(*) FROM sentiment_results {where_clause}'
                cursor.execute(count_query, search_params)
                total = cursor.fetchone()[0]

                # 计算分页
                offset = (page - 1) * page_size
                total_pages = (total + page_size - 1) // page_size

                # 获取标签名称列表
                tag_names = [
                    "同业竞争", "股权与控制权", "关联交易", "历史沿革与股东核查", "重大违法违规",
                    "收入与成本", "财务内控不规范", "客户与供应商", "资产质量与减值", "研发与技术",
                    "募集资金用途", "突击分红与对赌协议", "市场传闻与负面报道", "行业政策与环境"
                ]

                # 构建标签字段查询
                tag_fields = []
                reason_fields = []
                for tag_name in tag_names:
                    tag_fields.append(f'tag_{tag_name}')
                    reason_fields.append(f'reason_{tag_name}')

                all_tag_fields = ', '.join(tag_fields + reason_fields)

                # 查询数据
                query_params = search_params + [page_size, offset]
                cursor.execute(f'''
                    SELECT
                        COALESCE(original_id, id) as original_id,
                        COALESCE(title, '无标题') as title,
                        COALESCE(content, '无内容') as content,
                        COALESCE(summary, '无摘要') as summary,
                        COALESCE(source, '未知来源') as source,
                        COALESCE(publish_time, '未知时间') as publish_time,
                        COALESCE(sentiment_level, '未知') as sentiment_level,
                        COALESCE(sentiment_reason, '无原因') as sentiment_reason,
                        COALESCE(companies, '') as companies,
                        COALESCE(duplicate_id, '无') as duplicate_id,
                        COALESCE(duplication_rate, 0.0) as duplication_rate,
                        COALESCE(processing_time, 0) as processing_time,
                        {all_tag_fields}
                    FROM sentiment_results
                    {where_clause}
                    ORDER BY id DESC
                    LIMIT ? OFFSET ?
                ''', query_params)

                results = cursor.fetchall()

                # 转换数据格式
                data = []
                for row in results:
                    # 构建基本字段
                    result_dict = {
                        'id': row[0],
                        'title': row[1],
                        'content': row[2],
                        'summary': row[3],
                        'source': row[4],
                        'publish_time': row[5],
                        'sentiment_level': row[6],
                        'sentiment_reason': row[7],
                        'companies': row[8],
                        'duplicate_id': row[9],
                        'duplication_rate': row[10],
                        'processing_time': row[11]
                    }

                    # 添加标签字段（从第12个字段开始）
                    field_index = 12
                    tags = []
                    for tag_name in tag_names:
                        tag_value = row[field_index] if field_index < len(row) else '否'
                        result_dict[f'tag_{tag_name}'] = tag_value
                        if tag_value == '是':
                            tags.append(tag_name)
                        field_index += 1

                    # 添加原因字段
                    for tag_name in tag_names:
                        result_dict[f'reason_{tag_name}'] = row[field_index] if field_index < len(row) else '无'
                        field_index += 1

                    # 添加标签列表（用于前端显示）
                    result_dict['tags'] = tags

                    data.append(result_dict)

                return {
                    'success': True,
                    'data': data,
                    'total': total,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': total_pages,
                    'message': f'找到 {total} 条记录'
                }

        except Exception as e:
            return {
                'success': False,
                'data': [],
                'total': 0,
                'page': page,
                'page_size': page_size,
                'total_pages': 0,
                'message': f'搜索失败: {str(e)}'
            }

# Usage example
if __name__ == "__main__":
    # Create database instance
    db = ResultDatabase()
    
    # Test saving result
    result_id = db.save_result(
        query_text="This is a test query",
        sentiment_score=0.8,
        sentiment_label="positive",
        confidence=0.95,
        model_used="test_model",
        raw_response="Test response"
    )
    
    if result_id:
        print(f"Result saved successfully, ID: {result_id}")
    
    # Get statistics
    stats = db.get_database_stats()
    print("Database statistics:", stats)

    # Export results
    db.export_results()