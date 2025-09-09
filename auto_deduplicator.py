#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自动去重模块
在数据导出前自动执行去重处理，确保导出的数据不包含重复项
"""

import logging
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict, Counter
import hashlib
import re
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

class AutoDeduplicator:
    """
    自动去重器
    在导出数据前自动检测并处理重复数据
    """
    
    def __init__(self, db_path: str = "data/analysis_results.db"):
        self.db_path = db_path
        self.similarity_threshold = 0.85  # 默认相似度阈值
        
    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的相似度"""
        if not text1 or not text2:
            return 0.0
        
        # 清理文本
        clean_text1 = self._clean_text(text1)
        clean_text2 = self._clean_text(text2)
        
        # 使用SequenceMatcher计算相似度
        similarity = SequenceMatcher(None, clean_text1, clean_text2).ratio()
        return similarity
    
    def _clean_text(self, text: str) -> str:
        """清理文本，去除HTML标签和多余空白"""
        if not text:
            return ""
        
        # 去除HTML标签
        clean_text = re.sub(r'<[^>]+>', '', text)
        # 去除多余的空白字符
        clean_text = re.sub(r'\s+', ' ', clean_text.strip())
        return clean_text
    
    def _generate_content_hash(self, content: str) -> str:
        """生成内容哈希值用于快速比较"""
        if not content:
            return ""
        
        clean_content = self._clean_text(content)
        return hashlib.md5(clean_content.encode('utf-8')).hexdigest()
    
    def detect_duplicates_in_data(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        在给定数据中检测重复项
        
        Args:
            data: 要检测的数据列表
            
        Returns:
            检测结果字典，包含重复组信息和统计
        """
        logger.info(f"🔍 开始检测 {len(data)} 条记录中的重复数据...")
        
        # 按original_id分组进行初步筛选
        original_id_groups = defaultdict(list)
        content_hash_groups = defaultdict(list)
        
        for i, item in enumerate(data):
            original_id = item.get('original_id')
            content = item.get('content', '')
            
            # 按original_id分组
            if original_id:
                original_id_groups[original_id].append((i, item))
            
            # 按内容哈希分组
            content_hash = self._generate_content_hash(content)
            if content_hash:
                content_hash_groups[content_hash].append((i, item))
        
        duplicate_groups = []
        duplicate_indices = set()
        
        # 1. 检测相同original_id的重复
        for original_id, group in original_id_groups.items():
            if len(group) > 1:
                logger.debug(f"发现 original_id {original_id} 有 {len(group)} 条重复记录")
                
                # 保留第一条，其他标记为重复
                primary_index = group[0][0]
                duplicate_items = []
                
                for i, (index, item) in enumerate(group[1:], 1):
                    duplicate_indices.add(index)
                    duplicate_items.append({
                        'index': index,
                        'item': item,
                        'reason': f'相同original_id: {original_id}',
                        'similarity': 1.0
                    })
                
                if duplicate_items:
                    duplicate_groups.append({
                        'primary_index': primary_index,
                        'primary_item': group[0][1],
                        'duplicates': duplicate_items,
                        'type': 'original_id_duplicate'
                    })
        
        # 2. 检测内容相似的重复（排除已经通过original_id发现的重复）
        for content_hash, group in content_hash_groups.items():
            if len(group) > 1:
                # 过滤掉已经标记为重复的项
                filtered_group = [(i, item) for i, item in group if i not in duplicate_indices]
                
                if len(filtered_group) > 1:
                    logger.debug(f"发现内容哈希 {content_hash[:8]}... 有 {len(filtered_group)} 条可能重复的记录")
                    
                    # 进行详细的相似度检测
                    for j, (index1, item1) in enumerate(filtered_group):
                        for index2, item2 in filtered_group[j+1:]:
                            if index2 in duplicate_indices:
                                continue
                                
                            similarity = self.calculate_text_similarity(
                                item1.get('content', ''), 
                                item2.get('content', '')
                            )
                            
                            if similarity >= self.similarity_threshold:
                                duplicate_indices.add(index2)
                                
                                # 找到或创建重复组
                                existing_group = None
                                for group in duplicate_groups:
                                    if group['primary_index'] == index1:
                                        existing_group = group
                                        break
                                
                                if existing_group:
                                    existing_group['duplicates'].append({
                                        'index': index2,
                                        'item': item2,
                                        'reason': f'内容相似度: {similarity:.2f}',
                                        'similarity': similarity
                                    })
                                else:
                                    duplicate_groups.append({
                                        'primary_index': index1,
                                        'primary_item': item1,
                                        'duplicates': [{
                                            'index': index2,
                                            'item': item2,
                                            'reason': f'内容相似度: {similarity:.2f}',
                                            'similarity': similarity
                                        }],
                                        'type': 'content_similarity_duplicate'
                                    })
        
        total_duplicates = len(duplicate_indices)
        logger.info(f"✅ 重复检测完成，发现 {len(duplicate_groups)} 个重复组，共 {total_duplicates} 条重复记录")
        
        return {
            'duplicate_groups': duplicate_groups,
            'duplicate_indices': duplicate_indices,
            'total_records': len(data),
            'total_duplicates': total_duplicates,
            'unique_records': len(data) - total_duplicates,
            'detection_time': datetime.now().isoformat()
        }
    
    def remove_duplicates_from_data(self, data: List[Dict[str, Any]], 
                                  detection_result: Dict[str, Any] = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        从数据中移除重复项
        
        Args:
            data: 原始数据列表
            detection_result: 可选的检测结果，如果不提供则重新检测
            
        Returns:
            (去重后的数据, 去重统计信息)
        """
        if detection_result is None:
            detection_result = self.detect_duplicates_in_data(data)
        
        duplicate_indices = detection_result['duplicate_indices']
        
        # 创建去重后的数据列表
        deduplicated_data = []
        removed_items = []
        
        for i, item in enumerate(data):
            if i in duplicate_indices:
                removed_items.append({
                    'index': i,
                    'item': item,
                    'original_id': item.get('original_id'),
                    'title': item.get('title', '')[:50] + '...' if item.get('title') else 'No title'
                })
            else:
                deduplicated_data.append(item)
        
        stats = {
            'original_count': len(data),
            'removed_count': len(removed_items),
            'final_count': len(deduplicated_data),
            'duplicate_groups': len(detection_result['duplicate_groups']),
            'removed_items': removed_items,
            'processing_time': datetime.now().isoformat()
        }
        
        logger.info(f"🧹 去重完成: 原始 {stats['original_count']} 条 → 去重后 {stats['final_count']} 条 (移除 {stats['removed_count']} 条)")
        
        return deduplicated_data, stats
    
    def auto_deduplicate_export_data(self, data: List[Dict[str, Any]], 
                                   export_options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        自动去重导出数据
        这是主要的接口函数，在导出前调用
        
        Args:
            data: 要导出的数据
            export_options: 导出选项
            
        Returns:
            包含去重后数据和统计信息的字典
        """
        start_time = datetime.now()
        logger.info(f"🚀 开始自动去重处理，原始数据量: {len(data)} 条")
        
        if not data:
            return {
                'success': True,
                'data': [],
                'stats': {
                    'original_count': 0,
                    'final_count': 0,
                    'removed_count': 0,
                    'processing_time': 0
                },
                'message': '没有数据需要处理'
            }
        
        try:
            # 1. 检测重复
            detection_result = self.detect_duplicates_in_data(data)
            
            # 2. 移除重复项
            deduplicated_data, removal_stats = self.remove_duplicates_from_data(data, detection_result)
            
            # 3. 生成详细统计
            processing_time = (datetime.now() - start_time).total_seconds()
            
            final_stats = {
                **removal_stats,
                'detection_result': detection_result,
                'processing_time_seconds': processing_time,
                'similarity_threshold': self.similarity_threshold,
                'deduplication_rate': removal_stats['removed_count'] / removal_stats['original_count'] if removal_stats['original_count'] > 0 else 0
            }
            
            logger.info(f"✅ 自动去重完成，耗时 {processing_time:.2f}s，去重率 {final_stats['deduplication_rate']:.2%}")
            
            return {
                'success': True,
                'data': deduplicated_data,
                'stats': final_stats,
                'message': f'去重完成：{final_stats["original_count"]} → {final_stats["final_count"]} 条记录'
            }
            
        except Exception as e:
            logger.error(f"❌ 自动去重失败: {str(e)}")
            return {
                'success': False,
                'data': data,  # 返回原始数据
                'stats': {
                    'original_count': len(data),
                    'final_count': len(data),
                    'removed_count': 0,
                    'error': str(e)
                },
                'message': f'去重失败，返回原始数据: {str(e)}'
            }
    
    def get_duplicate_summary_report(self, data: List[Dict[str, Any]]) -> str:
        """
        生成重复数据摘要报告
        
        Args:
            data: 要分析的数据
            
        Returns:
            格式化的报告字符串
        """
        detection_result = self.detect_duplicates_in_data(data)
        
        report_lines = [
            "=" * 60,
            "📊 重复数据检测报告",
            "=" * 60,
            f"总记录数: {detection_result['total_records']}",
            f"重复记录数: {detection_result['total_duplicates']}",
            f"唯一记录数: {detection_result['unique_records']}",
            f"重复组数: {len(detection_result['duplicate_groups'])}",
            f"重复率: {detection_result['total_duplicates'] / detection_result['total_records']:.2%}",
            "",
            "🔍 重复组详情:"
        ]
        
        for i, group in enumerate(detection_result['duplicate_groups'][:10], 1):  # 只显示前10个组
            primary_item = group['primary_item']
            primary_title = primary_item.get('title', 'No title')[:30] + '...'
            
            report_lines.append(f"  组 {i}: {primary_title}")
            report_lines.append(f"    主记录: original_id={primary_item.get('original_id')}")
            
            for dup in group['duplicates'][:3]:  # 每组只显示前3个重复项
                dup_title = dup['item'].get('title', 'No title')[:30] + '...'
                report_lines.append(f"    重复项: {dup_title} ({dup['reason']})")
            
            if len(group['duplicates']) > 3:
                report_lines.append(f"    ... 还有 {len(group['duplicates']) - 3} 个重复项")
            report_lines.append("")
        
        if len(detection_result['duplicate_groups']) > 10:
            report_lines.append(f"... 还有 {len(detection_result['duplicate_groups']) - 10} 个重复组")
        
        report_lines.extend([
            "=" * 60,
            f"检测时间: {detection_result['detection_time']}",
            "=" * 60
        ])
        
        return "\n".join(report_lines)


class DatabaseAutoDeduplicator(AutoDeduplicator):
    """
    数据库自动去重器
    直接对数据库中的数据进行去重处理
    """
    
    def get_all_records_from_db(self) -> List[Dict[str, Any]]:
        """从数据库获取所有记录"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row  # 使结果可以按列名访问
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM sentiment_results 
                    ORDER BY analysis_time DESC
                ''')
                
                records = cursor.fetchall()
                
                # 转换为字典列表
                data = []
                for row in records:
                    data.append(dict(row))
                
                logger.info(f"📊 从数据库获取了 {len(data)} 条记录")
                return data
                
        except Exception as e:
            logger.error(f"❌ 从数据库获取记录失败: {str(e)}")
            return []
    
    def auto_deduplicate_database(self) -> Dict[str, Any]:
        """
        自动对数据库进行去重处理
        
        Returns:
            处理结果字典
        """
        logger.info("🗄️ 开始数据库自动去重处理...")
        
        # 获取所有记录
        all_records = self.get_all_records_from_db()
        
        if not all_records:
            return {
                'success': False,
                'message': '数据库中没有记录',
                'stats': {}
            }
        
        # 执行去重
        dedup_result = self.auto_deduplicate_export_data(all_records)
        
        if not dedup_result['success']:
            return dedup_result
        
        # 可选：将去重结果保存回数据库或导出
        # 这里我们只返回结果，不修改原数据库
        
        return {
            'success': True,
            'message': f'数据库去重完成: {dedup_result["stats"]["original_count"]} → {dedup_result["stats"]["final_count"]} 条',
            'data': dedup_result['data'],
            'stats': dedup_result['stats']
        }


# 全局实例
auto_deduplicator = AutoDeduplicator()
database_auto_deduplicator = DatabaseAutoDeduplicator()

def get_auto_deduplicator() -> AutoDeduplicator:
    """获取自动去重器实例"""
    return auto_deduplicator

def get_database_auto_deduplicator() -> DatabaseAutoDeduplicator:
    """获取数据库自动去重器实例"""
    return database_auto_deduplicator

