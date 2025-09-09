# -*- coding: utf-8 -*-

import sqlite3
import json
import hashlib
from difflib import SequenceMatcher
from typing import List, Dict, Tuple, Optional
import logging
from datetime import datetime
import uuid
from ali_llm_client import AliLLMClient

logger = logging.getLogger(__name__)

class ComprehensiveFixes:
    """综合修复工具类"""
    
    def __init__(self, db_path="data/analysis_results.db"):
        self.db_path = db_path
        self.llm_client = AliLLMClient()
    
    def fix_empty_summaries(self):
        """修复空摘要问题"""
        print("🔧 开始修复空摘要...")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 查找摘要为空或为"无摘要"的记录
                cursor.execute('''
                    SELECT id, content, summary FROM sentiment_results 
                    WHERE summary IS NULL OR summary = '' OR summary = '无摘要'
                    ORDER BY id DESC
                    LIMIT 50
                ''')
                
                records = cursor.fetchall()
                print(f"找到 {len(records)} 条需要修复摘要的记录")
                
                fixed_count = 0
                for record_id, content, old_summary in records:
                    if not content or len(content.strip()) < 10:
                        continue
                    
                    try:
                        # 使用AI生成摘要
                        new_summary = self.llm_client.generate_summary(content)
                        
                        # 如果AI生成失败，使用截取摘要
                        if "摘要生成失败" in new_summary or not new_summary.strip():
                            new_summary = content[:200] + "..." if len(content) > 200 else content
                        
                        # 更新数据库
                        cursor.execute('''
                            UPDATE sentiment_results 
                            SET summary = ? 
                            WHERE id = ?
                        ''', (new_summary, record_id))
                        
                        fixed_count += 1
                        print(f"✅ 修复记录 {record_id} 的摘要")
                        
                    except Exception as e:
                        print(f"❌ 修复记录 {record_id} 失败: {str(e)}")
                        # 使用截取摘要作为备选
                        fallback_summary = content[:200] + "..." if len(content) > 200 else content
                        cursor.execute('''
                            UPDATE sentiment_results 
                            SET summary = ? 
                            WHERE id = ?
                        ''', (fallback_summary, record_id))
                
                conn.commit()
                print(f"🎉 摘要修复完成，共修复 {fixed_count} 条记录")
                
        except Exception as e:
            print(f"❌ 修复摘要时出错: {str(e)}")
    
    def calculate_content_similarity(self, content1: str, content2: str) -> float:
        """计算两个内容的相似度"""
        if not content1 or not content2:
            return 0.0
        
        # 使用SequenceMatcher计算相似度
        similarity = SequenceMatcher(None, content1.strip(), content2.strip()).ratio()
        return round(similarity, 3)
    
    def generate_content_hash(self, content: str) -> str:
        """生成内容哈希值用于快速比较"""
        if not content:
            return ""
        return hashlib.md5(content.strip().encode('utf-8')).hexdigest()[:16]
    
    def detect_duplicates_and_update(self, similarity_threshold: float = 0.8):
        """检测重复数据并更新duplicate_id和duplication_rate字段"""
        print(f"🔍 开始检测重复数据（相似度阈值: {similarity_threshold}）...")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 获取所有记录
                cursor.execute('''
                    SELECT id, original_id, title, content, duplicate_id, duplication_rate 
                    FROM sentiment_results 
                    ORDER BY id
                ''')
                
                records = cursor.fetchall()
                print(f"共有 {len(records)} 条记录需要检测")
                
                # 构建内容哈希映射
                hash_groups = {}
                for record in records:
                    record_id, original_id, title, content, _, _ = record
                    content_hash = self.generate_content_hash(content)
                    
                    if content_hash not in hash_groups:
                        hash_groups[content_hash] = []
                    hash_groups[content_hash].append(record)
                
                updated_count = 0
                duplicate_groups = []
                
                # 检测每个哈希组内的重复
                for content_hash, group_records in hash_groups.items():
                    if len(group_records) <= 1:
                        continue
                    
                    # 详细相似度检测
                    for i, record1 in enumerate(group_records):
                        for j, record2 in enumerate(group_records[i+1:], i+1):
                            similarity = self.calculate_content_similarity(record1[3], record2[3])
                            
                            if similarity >= similarity_threshold:
                                # 找到重复数据
                                duplicate_groups.append({
                                    'record1': record1,
                                    'record2': record2,
                                    'similarity': similarity
                                })
                
                print(f"找到 {len(duplicate_groups)} 对重复数据")
                
                # 更新重复数据字段
                for dup_group in duplicate_groups:
                    record1 = dup_group['record1']
                    record2 = dup_group['record2']
                    similarity = dup_group['similarity']
                    
                    # 更新第一条记录
                    cursor.execute('''
                        UPDATE sentiment_results 
                        SET duplicate_id = ?, duplication_rate = ?
                        WHERE id = ?
                    ''', (str(record2[0]), similarity, record1[0]))
                    
                    # 更新第二条记录
                    cursor.execute('''
                        UPDATE sentiment_results 
                        SET duplicate_id = ?, duplication_rate = ?
                        WHERE id = ?
                    ''', (str(record1[0]), similarity, record2[0]))
                    
                    updated_count += 2
                    print(f"✅ 标记重复: ID {record1[0]} <-> ID {record2[0]} (相似度: {similarity:.3f})")
                
                conn.commit()
                print(f"🎉 重复检测完成，更新了 {updated_count} 条记录")
                
                return len(duplicate_groups)
                
        except Exception as e:
            print(f"❌ 检测重复数据时出错: {str(e)}")
            return 0
    
    def clean_duplicate_records(self, keep_strategy: str = "first"):
        """清理重复记录"""
        print(f"🧹 开始清理重复记录（保留策略: {keep_strategy}）...")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 查找有重复标记的记录
                cursor.execute('''
                    SELECT id, original_id, duplicate_id, duplication_rate, analysis_time
                    FROM sentiment_results 
                    WHERE duplicate_id IS NOT NULL AND duplicate_id != '' AND duplicate_id != '无'
                    ORDER BY id
                ''')
                
                duplicate_records = cursor.fetchall()
                print(f"找到 {len(duplicate_records)} 条重复记录")
                
                if not duplicate_records:
                    print("没有找到重复记录")
                    return 0
                
                # 按重复组分组
                duplicate_groups = {}
                for record in duplicate_records:
                    record_id, original_id, duplicate_id, duplication_rate, analysis_time = record
                    
                    # 创建重复组的键（使用较小的ID作为组键）
                    group_key = tuple(sorted([record_id, int(duplicate_id)]))
                    
                    if group_key not in duplicate_groups:
                        duplicate_groups[group_key] = []
                    duplicate_groups[group_key].append(record)
                
                deleted_count = 0
                for group_key, group_records in duplicate_groups.items():
                    if len(group_records) <= 1:
                        continue
                    
                    # 根据策略选择保留的记录
                    if keep_strategy == "first":
                        # 保留ID最小的
                        keep_record = min(group_records, key=lambda x: x[0])
                    elif keep_strategy == "latest":
                        # 保留最新的
                        keep_record = max(group_records, key=lambda x: x[4] or "")
                    else:
                        keep_record = group_records[0]
                    
                    # 删除其他记录
                    for record in group_records:
                        if record[0] != keep_record[0]:
                            cursor.execute('DELETE FROM sentiment_results WHERE id = ?', (record[0],))
                            deleted_count += 1
                            print(f"🗑️  删除重复记录 ID: {record[0]}")
                
                conn.commit()
                print(f"🎉 清理完成，删除了 {deleted_count} 条重复记录")
                
                return deleted_count
                
        except Exception as e:
            print(f"❌ 清理重复记录时出错: {str(e)}")
            return 0
    
    def export_deduplicated_data(self, session_id: Optional[str] = None, output_file: str = None):
        """导出去重后的数据"""
        print("📤 开始导出去重后的数据...")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 构建查询条件
                if session_id:
                    query = '''
                        SELECT * FROM sentiment_results 
                        WHERE session_id = ?
                        ORDER BY id DESC
                    '''
                    cursor.execute(query, (session_id,))
                else:
                    query = '''
                        SELECT * FROM sentiment_results 
                        ORDER BY id DESC
                    '''
                    cursor.execute(query)
                
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
                
                # 转换为字典列表
                all_data = []
                for row in rows:
                    data_dict = dict(zip(columns, row))
                    all_data.append(data_dict)
                
                print(f"从数据库获取了 {len(all_data)} 条记录")
                
                # 基于内容去重
                seen_hashes = set()
                deduplicated_data = []
                
                for data in all_data:
                    content = data.get('content', '')
                    content_hash = self.generate_content_hash(content)
                    
                    if content_hash not in seen_hashes:
                        seen_hashes.add(content_hash)
                        deduplicated_data.append(data)
                    else:
                        print(f"跳过重复记录 ID: {data.get('id')}")
                
                print(f"去重后剩余 {len(deduplicated_data)} 条记录")
                
                # 生成输出文件名
                if not output_file:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    output_file = f"deduplicated_analysis_results_{timestamp}.json"
                
                # 导出到JSON文件
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(deduplicated_data, f, ensure_ascii=False, indent=2)
                
                print(f"🎉 去重数据已导出到: {output_file}")
                
                return {
                    'success': True,
                    'total_records': len(all_data),
                    'deduplicated_records': len(deduplicated_data),
                    'removed_duplicates': len(all_data) - len(deduplicated_data),
                    'output_file': output_file
                }
                
        except Exception as e:
            print(f"❌ 导出去重数据时出错: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_database_stats(self):
        """获取数据库统计信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 总记录数
                cursor.execute('SELECT COUNT(*) FROM sentiment_results')
                total_records = cursor.fetchone()[0]
                
                # 有摘要的记录数
                cursor.execute('''
                    SELECT COUNT(*) FROM sentiment_results 
                    WHERE summary IS NOT NULL AND summary != '' AND summary != '无摘要'
                ''')
                records_with_summary = cursor.fetchone()[0]
                
                # 标记为重复的记录数
                cursor.execute('''
                    SELECT COUNT(*) FROM sentiment_results 
                    WHERE duplicate_id IS NOT NULL AND duplicate_id != '' AND duplicate_id != '无'
                ''')
                duplicate_records = cursor.fetchone()[0]
                
                # 最近的记录
                cursor.execute('''
                    SELECT analysis_time FROM sentiment_results 
                    ORDER BY id DESC LIMIT 1
                ''')
                latest_record = cursor.fetchone()
                latest_time = latest_record[0] if latest_record else "无"
                
                stats = {
                    'total_records': total_records,
                    'records_with_summary': records_with_summary,
                    'records_without_summary': total_records - records_with_summary,
                    'duplicate_records': duplicate_records,
                    'latest_record_time': latest_time
                }
                
                print("📊 数据库统计信息:")
                print(f"  总记录数: {stats['total_records']}")
                print(f"  有摘要记录: {stats['records_with_summary']}")
                print(f"  无摘要记录: {stats['records_without_summary']}")
                print(f"  重复记录: {stats['duplicate_records']}")
                print(f"  最新记录时间: {stats['latest_record_time']}")
                
                return stats
                
        except Exception as e:
            print(f"❌ 获取统计信息时出错: {str(e)}")
            return {}

def main():
    """主函数 - 执行所有修复"""
    print("🚀 开始执行综合修复...")
    
    fixer = ComprehensiveFixes()
    
    # 1. 获取当前统计
    print("\n" + "="*50)
    print("📊 修复前统计")
    print("="*50)
    fixer.get_database_stats()
    
    # 2. 修复空摘要
    print("\n" + "="*50)
    print("🔧 修复空摘要")
    print("="*50)
    fixer.fix_empty_summaries()
    
    # 3. 检测并标记重复数据
    print("\n" + "="*50)
    print("🔍 检测重复数据")
    print("="*50)
    duplicate_count = fixer.detect_duplicates_and_update()
    
    # 4. 获取修复后统计
    print("\n" + "="*50)
    print("📊 修复后统计")
    print("="*50)
    stats = fixer.get_database_stats()
    
    # 5. 导出去重数据
    print("\n" + "="*50)
    print("📤 导出去重数据")
    print("="*50)
    export_result = fixer.export_deduplicated_data()
    
    # 总结
    print("\n" + "="*50)
    print("🎉 修复完成总结")
    print("="*50)
    print(f"✅ 修复了空摘要问题")
    print(f"✅ 检测到 {duplicate_count} 对重复数据")
    print(f"✅ 标记了重复记录")
    if export_result.get('success'):
        print(f"✅ 导出了去重数据: {export_result.get('output_file')}")
        print(f"   - 原始记录: {export_result.get('total_records')}")
        print(f"   - 去重后: {export_result.get('deduplicated_records')}")
        print(f"   - 移除重复: {export_result.get('removed_duplicates')}")
    
    print("\n💡 下一步建议:")
    if stats.get('duplicate_records', 0) > 0:
        print("   - 可以运行 fixer.clean_duplicate_records() 清理重复记录")
    print("   - 使用去重后的导出文件作为最终结果")

if __name__ == "__main__":
    main()
