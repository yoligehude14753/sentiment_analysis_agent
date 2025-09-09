"""
舆情分析系统综合修复工具 V2.0
修复版本 - 基于original_id的正确去重逻辑
"""

import sqlite3
import json
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, List, Any
import hashlib
import os
import logging

logger = logging.getLogger(__name__)

class ComprehensiveFixesV2:
    """综合修复工具类 V2.0 - 修复版本"""
    
    def __init__(self, db_path: str = "data/analysis_results.db"):
        self.db_path = db_path
        
    def generate_content_hash(self, content: str) -> str:
        """生成内容哈希值"""
        if not content:
            return ""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def fix_empty_summaries(self):
        """修复空摘要"""
        print("🔧 开始修复空摘要...")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 查找空摘要记录
                cursor.execute("""
                    SELECT id, title, content 
                    FROM sentiment_results 
                    WHERE summary IS NULL OR summary = '' OR summary = 'None'
                """)
                
                empty_summary_records = cursor.fetchall()
                print(f"发现 {len(empty_summary_records)} 条空摘要记录")
                
                fixed_count = 0
                for record_id, title, content in empty_summary_records:
                    # 生成简单摘要（使用标题或内容前100字符）
                    if title and title.strip():
                        summary = title.strip()[:100]
                    elif content and content.strip():
                        # 清理HTML标签并取前100字符
                        import re
                        clean_content = re.sub(r'<[^>]+>', '', content)
                        clean_content = clean_content.replace('\n', '').replace('\r', '').strip()
                        summary = clean_content[:100] if clean_content else "无摘要"
                    else:
                        summary = "无摘要"
                    
                    # 更新摘要
                    cursor.execute("""
                        UPDATE sentiment_results 
                        SET summary = ? 
                        WHERE id = ?
                    """, (summary, record_id))
                    
                    fixed_count += 1
                
                conn.commit()
                print(f"✅ 成功修复 {fixed_count} 条空摘要记录")
                return fixed_count
                
        except Exception as e:
            print(f"❌ 修复空摘要时出错: {str(e)}")
            return 0
    
    def detect_and_mark_duplicates(self):
        """检测并标记重复数据"""
        print("🔍 开始检测重复数据...")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 获取所有记录
                cursor.execute("SELECT id, original_id, content FROM sentiment_results ORDER BY id")
                all_records = cursor.fetchall()
                
                print(f"总记录数: {len(all_records)}")
                
                # 按original_id分组检测重复
                original_id_groups = {}
                for record_id, original_id, content in all_records:
                    if original_id not in original_id_groups:
                        original_id_groups[original_id] = []
                    original_id_groups[original_id].append((record_id, content))
                
                duplicate_pairs = 0
                marked_count = 0
                
                for original_id, records in original_id_groups.items():
                    if len(records) > 1:
                        # 有重复，保留第一条，标记其他为重复
                        primary_record = records[0]  # ID最小的作为主记录
                        
                        for i, (record_id, content) in enumerate(records[1:], 1):
                            # 计算相似度（简单的基于内容长度的相似度）
                            similarity = 1.0  # 同original_id认为100%重复
                            
                            # 更新重复标记
                            cursor.execute("""
                                UPDATE sentiment_results 
                                SET duplicate_id = ?, duplication_rate = ?
                                WHERE id = ?
                            """, (primary_record[0], similarity, record_id))
                            
                            duplicate_pairs += 1
                            marked_count += 1
                
                conn.commit()
                print(f"✅ 检测完成，发现 {duplicate_pairs} 对重复数据，标记了 {marked_count} 条重复记录")
                return duplicate_pairs
                
        except Exception as e:
            print(f"❌ 检测重复数据时出错: {str(e)}")
            return 0
    
    def export_deduplicated_data(self, session_id: Optional[str] = None, 
                               output_format: str = "both", 
                               keep_strategy: str = "first"):
        """导出去重后的数据（修复版本）"""
        print("📤 开始导出去重后的数据...")
        print(f"🔧 去重策略: 基于original_id，保留{keep_strategy}条记录")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 构建查询条件
                if session_id:
                    query = '''
                        SELECT * FROM sentiment_results 
                        WHERE session_id = ?
                        ORDER BY id ASC
                    '''
                    cursor.execute(query, (session_id,))
                else:
                    query = '''
                        SELECT * FROM sentiment_results 
                        ORDER BY id ASC
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
                
                if not all_data:
                    return {'success': False, 'message': '没有找到记录', 'files': []}
                
                # ✅ 修复：基于original_id去重
                original_id_groups = {}
                for data in all_data:
                    original_id = data.get('original_id')
                    if original_id is None:
                        original_id = f"id_{data.get('id')}"
                    
                    if original_id not in original_id_groups:
                        original_id_groups[original_id] = []
                    original_id_groups[original_id].append(data)
                
                # 统计重复情况
                duplicate_groups = {k: v for k, v in original_id_groups.items() if len(v) > 1}
                total_duplicates = sum(len(v) - 1 for v in duplicate_groups.values())
                
                print(f"📊 去重统计:")
                print(f"   唯一original_id数: {len(original_id_groups)}")
                print(f"   重复的original_id数: {len(duplicate_groups)}")
                print(f"   重复记录总数: {total_duplicates}")
                
                if duplicate_groups:
                    print(f"🔍 重复记录详情（显示前5个）:")
                    for original_id, group in list(duplicate_groups.items())[:5]:
                        print(f"   original_id '{original_id}': {len(group)} 条记录")
                
                # 执行去重
                deduplicated_data = []
                for original_id, group in original_id_groups.items():
                    if keep_strategy == "first":
                        selected_record = min(group, key=lambda x: x.get('id', 0))
                    elif keep_strategy == "last":
                        selected_record = max(group, key=lambda x: x.get('id', 0))
                    else:
                        selected_record = group[0]
                    
                    deduplicated_data.append(selected_record)
                
                print(f"✅ 去重完成: {len(all_data)} -> {len(deduplicated_data)} 条记录")
                
                # 确保导出目录存在
                os.makedirs("exports", exist_ok=True)
                
                # 导出文件
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                exported_files = []
                
                if output_format in ["json", "both"]:
                    json_file = f"exports/deduplicated_results_v2_{timestamp}.json"
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(deduplicated_data, f, ensure_ascii=False, indent=2, default=str)
                    exported_files.append(json_file)
                    print(f"💾 JSON文件已保存: {json_file}")
                
                if output_format in ["csv", "both"]:
                    csv_file = f"exports/deduplicated_results_v2_{timestamp}.csv"
                    df = pd.DataFrame(deduplicated_data)
                    df.to_csv(csv_file, index=False, encoding='utf-8-sig')
                    exported_files.append(csv_file)
                    print(f"💾 CSV文件已保存: {csv_file}")
                
                return {
                    'success': True,
                    'message': f'成功导出去重数据',
                    'files': exported_files,
                    'stats': {
                        'original_count': len(all_data),
                        'deduplicated_count': len(deduplicated_data),
                        'removed_count': len(all_data) - len(deduplicated_data)
                    }
                }
                
        except Exception as e:
            print(f"❌ 导出去重数据时出错: {str(e)}")
            return {'success': False, 'message': f'导出失败: {str(e)}', 'files': []}
    
    def clean_duplicate_records(self, keep_strategy: str = "first"):
        """清理重复记录（物理删除）"""
        print(f"🗑️ 开始清理重复记录（保留策略: {keep_strategy}）...")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 获取所有记录
                cursor.execute("SELECT id, original_id FROM sentiment_results ORDER BY id")
                all_records = cursor.fetchall()
                
                # 按original_id分组
                original_id_groups = {}
                for record_id, original_id in all_records:
                    if original_id not in original_id_groups:
                        original_id_groups[original_id] = []
                    original_id_groups[original_id].append(record_id)
                
                # 找出要删除的记录
                records_to_delete = []
                for original_id, record_ids in original_id_groups.items():
                    if len(record_ids) > 1:
                        # 有重复，决定保留哪一条
                        if keep_strategy == "first":
                            keep_id = min(record_ids)
                        elif keep_strategy == "last":
                            keep_id = max(record_ids)
                        else:
                            keep_id = record_ids[0]
                        
                        # 其他的都要删除
                        for record_id in record_ids:
                            if record_id != keep_id:
                                records_to_delete.append(record_id)
                
                print(f"准备删除 {len(records_to_delete)} 条重复记录")
                
                if records_to_delete:
                    # 执行删除
                    placeholders = ','.join(['?'] * len(records_to_delete))
                    cursor.execute(f"DELETE FROM sentiment_results WHERE id IN ({placeholders})", 
                                 records_to_delete)
                    
                    conn.commit()
                    print(f"✅ 成功删除 {len(records_to_delete)} 条重复记录")
                else:
                    print("✅ 没有发现重复记录")
                
                return len(records_to_delete)
                
        except Exception as e:
            print(f"❌ 清理重复记录时出错: {str(e)}")
            return 0
    
    def run_all_fixes(self):
        """运行所有修复操作"""
        print("🚀 开始运行所有修复操作...")
        print("="*60)
        
        results = {}
        
        # 1. 修复空摘要
        print("步骤1: 修复空摘要")
        results['summary_fixes'] = self.fix_empty_summaries()
        print()
        
        # 2. 检测重复数据
        print("步骤2: 检测重复数据")
        results['duplicate_detection'] = self.detect_and_mark_duplicates()
        print()
        
        # 3. 导出去重数据
        print("步骤3: 导出去重数据")
        export_result = self.export_deduplicated_data(output_format="both")
        results['export_result'] = export_result
        print()
        
        # 4. 生成报告
        print("步骤4: 生成修复报告")
        print("="*60)
        print("📈 修复结果汇总:")
        print(f"   修复空摘要: {results['summary_fixes']} 条")
        print(f"   检测重复数据: {results['duplicate_detection']} 对")
        
        if export_result['success']:
            stats = export_result['stats']
            print(f"   导出统计:")
            print(f"     原始记录数: {stats['original_count']}")
            print(f"     去重后记录数: {stats['deduplicated_count']}")
            print(f"     删除重复记录数: {stats['removed_count']}")
            print(f"   导出文件: {export_result['files']}")
        else:
            print(f"   导出失败: {export_result['message']}")
        
        print("✅ 所有修复操作完成!")
        return results

def test_csv_deduplication():
    """测试CSV文件去重"""
    csv_file = r"C:\Users\anyut\Downloads\analysis_results_2025-08-26 (4).csv"
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV文件不存在: {csv_file}")
        return
    
    print("🧪 CSV文件去重测试")
    print("="*50)
    
    try:
        # 读取CSV
        df = pd.read_csv(csv_file, encoding='utf-8')
        print(f"📊 原始CSV文件: {len(df)} 条记录")
        
        # 检查字段
        if '原始ID' in df.columns:
            original_id_col = '原始ID'
        else:
            print("❌ 未找到'原始ID'字段")
            return
        
        # 统计重复
        duplicate_stats = df[original_id_col].value_counts()
        duplicates = duplicate_stats[duplicate_stats > 1]
        
        print(f"📈 重复情况:")
        print(f"   唯一original_id数: {len(duplicate_stats)}")
        print(f"   有重复的original_id数: {len(duplicates)}")
        print(f"   重复记录总数: {duplicates.sum()}")
        
        # 执行去重
        deduplicated_df = df.drop_duplicates(subset=[original_id_col], keep='first')
        
        print(f"\n✅ 去重结果:")
        print(f"   去重后记录数: {len(deduplicated_df)}")
        print(f"   删除重复记录数: {len(df) - len(deduplicated_df)}")
        
        # 保存去重文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"exports/csv_fixed_dedup_{timestamp}.csv"
        os.makedirs("exports", exist_ok=True)
        
        deduplicated_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"💾 修复后的CSV已保存: {output_file}")
        
    except Exception as e:
        print(f"❌ 处理CSV文件时出错: {str(e)}")

if __name__ == "__main__":
    print("🔧 舆情分析系统综合修复工具 V2.0")
    print("="*80)
    
    # 数据库修复
    fixer = ComprehensiveFixesV2()
    db_results = fixer.run_all_fixes()
    
    print("\n" + "="*80)
    
    # CSV文件去重测试
    test_csv_deduplication()
    
    print("\n🎉 所有修复和测试完成！")
