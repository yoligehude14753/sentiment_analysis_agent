#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import pandas as pd
import os
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库管理器，负责舆情数据的存储和查询"""
    
    def __init__(self, db_path: str = "data/sentiment_analysis.db"):
        self.db_path = db_path
        self.ensure_db_directory()
        self.init_database()
    
    def ensure_db_directory(self):
        """确保数据库目录存在"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def init_database(self):
        """初始化数据库表结构"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建舆情数据表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sentiment_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT,
                        content TEXT,
                        source TEXT,
                        publish_time TEXT,
                        company_name TEXT,
                        industry TEXT,
                        sentiment_level TEXT,
                        risk_tags TEXT,
                        analysis_reason TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 创建字段配置表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS field_config (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        field_name TEXT UNIQUE NOT NULL,
                        display_name TEXT NOT NULL,
                        is_visible BOOLEAN DEFAULT 1,
                        is_searchable BOOLEAN DEFAULT 1,
                        is_filterable BOOLEAN DEFAULT 1,
                        display_order INTEGER DEFAULT 0,
                        field_type TEXT DEFAULT 'text',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 插入默认字段配置
                default_fields = [
                    ('title', '标题', 1, 1, 1, 1, 'text'),
                    ('content', '内容', 1, 1, 1, 2, 'text'),
                    ('source', '来源', 1, 1, 1, 3, 'text'),
                    ('publish_time', '发布时间', 1, 1, 1, 4, 'datetime'),
                    ('company_name', '公司名称', 1, 1, 1, 5, 'text'),
                    ('industry', '行业', 1, 1, 1, 6, 'text'),
                    ('sentiment_level', '情感等级', 1, 1, 1, 7, 'text'),
                    ('risk_tags', '风险标签', 1, 1, 1, 8, 'text'),
                    ('analysis_reason', '分析原因', 1, 1, 0, 9, 'text')
                ]
                
                for field in default_fields:
                    cursor.execute('''
                        INSERT OR IGNORE INTO field_config 
                        (field_name, display_name, is_visible, is_searchable, is_filterable, display_order, field_type)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', field)
                
                conn.commit()
                logger.info("数据库初始化完成")
                
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
            raise
    
    def import_csv_data(self, csv_path: str, chunk_size: int = 1000) -> Dict[str, Any]:
        """导入CSV数据到数据库"""
        try:
            if not os.path.exists(csv_path):
                raise FileNotFoundError(f"CSV文件不存在: {csv_path}")
            
            # 读取CSV文件
            df = pd.read_csv(csv_path, encoding='utf-8')
            logger.info(f"CSV文件读取成功，共{len(df)}行数据")
            
            # 标准化列名
            df.columns = [col.strip() for col in df.columns]
            
            # 处理数据并插入数据库
            total_imported = 0
            total_skipped = 0
            
            with sqlite3.connect(self.db_path) as conn:
                for i in range(0, len(df), chunk_size):
                    chunk = df.iloc[i:i+chunk_size]
                    
                    for _, row in chunk.iterrows():
                        try:
                            # 准备数据
                            data = {
                                'title': str(row.get('标题', row.get('title', ''))),
                                'content': str(row.get('内容', row.get('content', ''))),
                                'source': str(row.get('来源', row.get('source', ''))),
                                'publish_time': str(row.get('发布时间', row.get('publish_time', ''))),
                                'company_name': str(row.get('公司名称', row.get('company_name', ''))),
                                'industry': str(row.get('行业', row.get('industry', ''))),
                                'sentiment_level': str(row.get('情感等级', row.get('sentiment_level', ''))),
                                'risk_tags': str(row.get('风险标签', row.get('risk_tags', ''))),
                                'analysis_reason': str(row.get('分析原因', row.get('analysis_reason', '')))
                            }
                            
                            # 插入数据
                            cursor = conn.cursor()
                            cursor.execute('''
                                INSERT INTO sentiment_data 
                                (title, content, source, publish_time, company_name, industry, sentiment_level, risk_tags, analysis_reason)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                data['title'], data['content'], data['source'], data['publish_time'],
                                data['company_name'], data['industry'], data['sentiment_level'], 
                                data['risk_tags'], data['analysis_reason']
                            ))
                            
                            total_imported += 1
                            
                        except Exception as e:
                            logger.warning(f"跳过行数据: {str(e)}")
                            total_skipped += 1
                            continue
                    
                    conn.commit()
                    logger.info(f"已处理 {i+len(chunk)}/{len(df)} 行数据")
            
            return {
                'success': True,
                'total_rows': len(df),
                'imported': total_imported,
                'skipped': total_skipped,
                'message': f"数据导入完成，成功导入{total_imported}条，跳过{total_skipped}条"
            }
            
        except Exception as e:
            logger.error(f"CSV数据导入失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': f"数据导入失败: {str(e)}"
            }
    
    def get_data(self, 
                 fields: Optional[List[str]] = None,
                 filters: Optional[Dict[str, Any]] = None,
                 search: Optional[str] = None,
                 page: int = 1,
                 page_size: int = 50,
                 sort_by: str = 'publish_time',
                 sort_order: str = 'DESC') -> Dict[str, Any]:
        """查询数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 构建查询字段
                if fields is None:
                    fields = ['*']
                
                field_str = ', '.join(fields)
                
                # 构建WHERE子句
                where_conditions = []
                params = []
                
                if filters:
                    for field, value in filters.items():
                        if isinstance(value, dict) and 'start' in value and 'end' in value:
                            # 时间范围过滤 - 统一处理，精确到分钟（与get_data_count保持一致）
                            start_time = self._normalize_time_format(value['start'])
                            end_time = self._normalize_time_format(value['end'])
                            
                            # 使用BETWEEN查询，确保时间范围完全匹配
                            where_conditions.append(f"{field} BETWEEN ? AND ?")
                            params.extend([start_time, end_time])
                            
                            # 记录时间范围查询参数，用于调试
                            logger.debug(f"get_data时间范围查询: {field} BETWEEN '{start_time}' AND '{end_time}'")
                        elif isinstance(value, (list, tuple)):
                            placeholders = ','.join(['?' for _ in value])
                            where_conditions.append(f"{field} IN ({placeholders})")
                            params.extend(value)
                        else:
                            where_conditions.append(f"{field} = ?")
                            params.append(value)
                
                if search:
                    search_fields = ['title', 'content', 'company_name', 'industry']
                    search_conditions = []
                    for field in search_fields:
                        search_conditions.append(f"{field} LIKE ?")
                        params.append(f"%{search}%")
                    where_conditions.append(f"({' OR '.join(search_conditions)})")
                
                where_clause = ""
                if where_conditions:
                    where_clause = "WHERE " + " AND ".join(where_conditions)
                
                # 构建排序
                order_clause = f"ORDER BY {sort_by} {sort_order.upper()}"
                
                # 构建分页
                offset = (page - 1) * page_size
                limit_clause = f"LIMIT {page_size} OFFSET {offset}"
                
                # 执行查询
                query = f"""
                    SELECT {field_str} FROM sentiment_data 
                    {where_clause} 
                    {order_clause} 
                    {limit_clause}
                """
                
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                # 获取总记录数
                count_query = f"""
                    SELECT COUNT(*) FROM sentiment_data {where_clause}
                """
                cursor.execute(count_query, params)
                total_count = cursor.fetchone()[0]
                
                # 格式化结果
                if fields == ['*']:
                    # 获取列名
                    cursor.execute("PRAGMA table_info(sentiment_data)")
                    columns = [col[1] for col in cursor.fetchall()]
                    result = [dict(zip(columns, row)) for row in rows]
                else:
                    result = [dict(zip(fields, row)) for row in rows]
                
                return {
                    'success': True,
                    'data': result,
                    'total': total_count,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (total_count + page_size - 1) // page_size
                }
                
        except Exception as e:
            logger.error(f"数据查询失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': f"数据查询失败: {str(e)}"
            }
    
    def get_data_count(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """查询数据量，使用统一的时间范围处理"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 构建WHERE子句
                where_conditions = []
                params = []
                
                if filters:
                    for field, value in filters.items():
                        if isinstance(value, dict) and 'start' in value and 'end' in value:
                            # 时间范围过滤 - 统一处理，精确到分钟
                            start_time = self._normalize_time_format(value['start'])
                            end_time = self._normalize_time_format(value['end'])
                            
                            # 使用BETWEEN查询，确保时间范围完全匹配
                            # 注意：BETWEEN是包含边界的，所以这里的时间范围是 [start_time, end_time]
                            where_conditions.append(f"{field} BETWEEN ? AND ?")
                            params.extend([start_time, end_time])
                            
                            # 记录时间范围查询参数，用于调试
                            logger.debug(f"时间范围查询: {field} BETWEEN '{start_time}' AND '{end_time}'")
                        elif isinstance(value, (list, tuple)):
                            placeholders = ','.join(['?' for _ in value])
                            where_conditions.append(f"{field} IN ({placeholders})")
                            params.extend(value)
                        else:
                            where_conditions.append(f"{field} = ?")
                            params.append(value)
                
                where_clause = ""
                if where_conditions:
                    where_clause = "WHERE " + " AND ".join(where_conditions)
                
                # 执行计数查询
                count_query = f"""
                    SELECT COUNT(*) FROM sentiment_data {where_clause}
                """
                cursor.execute(count_query, params)
                total_count = cursor.fetchone()[0]
                
                return {
                    'success': True,
                    'total': total_count,
                    'message': '查询成功'
                }
                
        except Exception as e:
            logger.error(f"数据量查询失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': f"数据量查询失败: {str(e)}"
            }
    
    def _normalize_time_format(self, time_str: str) -> str:
        """标准化时间格式，将ISO格式转换为数据库格式，精确到分钟"""
        try:
            # 移除可能的时区信息
            if 'T' in time_str:
                # ISO格式: 2024-01-01T00:00 或 2024-01-01T00:00:00
                time_str = time_str.replace('T', ' ')
            
            # 如果只有日期，添加时间
            if len(time_str) == 10:  # YYYY-MM-DD
                time_str += " 00:00:00"
            elif len(time_str) == 16:  # YYYY-MM-DD HH:MM
                time_str += ":00"
            elif len(time_str) == 19:  # YYYY-MM-DD HH:MM:SS
                pass  # 已经是完整格式
            else:
                # 其他格式，尝试解析
                import datetime
                try:
                    # 尝试解析为datetime对象
                    parsed_time = datetime.datetime.fromisoformat(time_str.replace('T', ' '))
                    time_str = parsed_time.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    # 如果解析失败，返回原字符串
                    logger.warning(f"无法解析时间格式: {time_str}")
                    return time_str
            
            # 验证时间格式
            import datetime
            datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            
            # 记录时间格式标准化结果，用于调试
            logger.debug(f"时间格式标准化: '{time_str}' -> '{time_str}'")
            
            return time_str
        except Exception as e:
            logger.warning(f"时间格式转换失败: {time_str}, 错误: {str(e)}")
            # 如果转换失败，返回原字符串
            return time_str

    def get_field_config(self) -> Dict[str, Any]:
        """获取字段配置"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT field_name, display_name, is_visible, is_searchable, 
                           is_filterable, display_order, field_type
                    FROM field_config 
                    ORDER BY display_order
                ''')
                
                fields = []
                for row in cursor.fetchall():
                    fields.append({
                        'field_name': row[0],
                        'display_name': row[1],
                        'is_visible': bool(row[2]),
                        'is_searchable': bool(row[3]),
                        'is_filterable': bool(row[4]),
                        'display_order': row[5],
                        'field_type': row[6]
                    })
                
                return {
                    'success': True,
                    'fields': fields
                }
                
        except Exception as e:
            logger.error(f"获取字段配置失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': f"获取字段配置失败: {str(e)}"
            }
    
    def update_field_config(self, field_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """更新字段配置"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 更新字段配置
                cursor.execute('''
                    UPDATE field_config 
                    SET display_name = ?, is_visible = ?, is_searchable = ?, 
                        is_filterable = ?, display_order = ?, field_type = ?
                    WHERE field_name = ?
                ''', (
                    config.get('display_name'),
                    config.get('is_visible', True),
                    config.get('is_searchable', True),
                    config.get('is_filterable', True),
                    config.get('display_order', 0),
                    config.get('field_type', 'text'),
                    field_name
                ))
                
                if cursor.rowcount == 0:
                    return {
                        'success': False,
                        'message': f"字段 {field_name} 不存在"
                    }
                
                conn.commit()
                
                return {
                    'success': True,
                    'message': f"字段 {field_name} 配置更新成功"
                }
                
        except Exception as e:
            logger.error(f"更新字段配置失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': f"更新字段配置失败: {str(e)}"
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取数据统计信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 总记录数
                cursor.execute("SELECT COUNT(*) FROM sentiment_data")
                total_records = cursor.fetchone()[0]
                
                # 情感等级分布
                cursor.execute("""
                    SELECT sentiment_level, COUNT(*) as count 
                    FROM sentiment_data 
                    WHERE sentiment_level IS NOT NULL AND sentiment_level != ''
                    GROUP BY sentiment_level
                """)
                sentiment_distribution = dict(cursor.fetchall())
                
                # 行业分布
                cursor.execute("""
                    SELECT industry, COUNT(*) as count 
                    FROM sentiment_data 
                    WHERE industry IS NOT NULL AND industry != ''
                    GROUP BY industry
                    ORDER BY count DESC
                    LIMIT 10
                """)
                industry_distribution = dict(cursor.fetchall())
                
                # 公司分布
                cursor.execute("""
                    SELECT company_name, COUNT(*) as count 
                    FROM sentiment_data 
                    WHERE company_name IS NOT NULL AND company_name != ''
                    GROUP BY company_name
                    ORDER BY count DESC
                    LIMIT 10
                """)
                company_distribution = dict(cursor.fetchall())
                
                return {
                    'success': True,
                    'statistics': {
                        'total_records': total_records,
                        'sentiment_distribution': sentiment_distribution,
                        'industry_distribution': industry_distribution,
                        'company_distribution': company_distribution
                    }
                }
                
        except Exception as e:
            logger.error(f"获取统计信息失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': f"获取统计信息失败: {str(e)}"
            }

    def get_database_info(self) -> Dict[str, Any]:
        """获取数据库信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 获取表信息
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                # 获取各表记录数
                table_counts = {}
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    table_counts[table] = cursor.fetchone()[0]
                
                # 获取数据库文件大小
                file_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                
                return {
                    'database_path': self.db_path,
                    'file_size_mb': round(file_size / (1024 * 1024), 2),
                    'tables': tables,
                    'table_counts': table_counts,
                    'total_records': sum(table_counts.values())
                }
                
        except Exception as e:
            logger.error(f"获取数据库信息失败: {str(e)}")
            return {}
    
    def get_sentiment_statistics(self, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """获取情感分析统计信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                date_filter = ""
                params = []
                if start_date and end_date:
                    date_filter = "WHERE publish_time BETWEEN ? AND ?"
                    params = [start_date, end_date]
                
                # 获取情感等级分布
                cursor.execute(f'''
                    SELECT sentiment_level, COUNT(*) as count
                    FROM sentiment_data
                    {date_filter}
                    GROUP BY sentiment_level
                    ORDER BY count DESC
                ''', params)
                
                sentiment_distribution = dict(cursor.fetchall())
                
                # 获取总记录数
                cursor.execute(f'''
                    SELECT COUNT(*) FROM sentiment_data {date_filter}
                ''', params)
                total_records = cursor.fetchone()[0]
                
                return {
                    'total_records': total_records,
                    'sentiment_distribution': sentiment_distribution
                }
                
        except Exception as e:
            logger.error(f"获取情感分析统计失败: {str(e)}")
            return {}
    
    def cleanup_old_records(self, days_to_keep: int = 90) -> int:
        """清理旧的舆情记录"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 删除旧记录
                cursor.execute('''
                    DELETE FROM sentiment_data 
                    WHERE created_at < datetime('now', '-{} days')
                '''.format(days_to_keep))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"清理完成，删除了 {deleted_count} 条旧记录")
                return deleted_count
                
        except Exception as e:
            logger.error(f"清理旧记录失败: {str(e)}")
            return 0

    def get_time_range(self) -> Dict[str, Any]:
        """获取数据库中的时间范围"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 查询最早和最晚的发布时间
                cursor.execute('''
                    SELECT 
                        MIN(publish_time) as earliest_time,
                        MAX(publish_time) as latest_time
                    FROM sentiment_data 
                    WHERE publish_time IS NOT NULL AND publish_time != ''
                ''')
                
                result = cursor.fetchone()
                if result and result[0] and result[1]:
                    return {
                        'success': True,
                        'earliest_time': result[0],
                        'latest_time': result[1],
                        'message': '查询成功'
                    }
                else:
                    return {
                        'success': False,
                        'message': '未找到有效的时间数据'
                    }
                
        except Exception as e:
            logger.error(f"获取时间范围失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': f"获取时间范围失败: {str(e)}"
            }
