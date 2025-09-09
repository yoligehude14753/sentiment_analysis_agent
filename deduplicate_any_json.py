#!/usr/bin/env python3
"""通用JSON文件去重脚本 - 以原始ID进行去重，并自动导入数据库"""

import json
import os
import sys
from datetime import datetime

# 添加项目路径到sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from result_database_new import ResultDatabase
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    print("⚠️  警告：无法导入数据库模块，将跳过数据库导入功能")

def deduplicate_json_by_original_id(input_file_path, output_file_path=None, auto_import_db=True):
    """
    对JSON文件按原始ID进行去重，并可选择自动导入数据库
    
    Args:
        input_file_path: 输入JSON文件路径
        output_file_path: 输出JSON文件路径，如果为None则自动生成
        auto_import_db: 是否自动导入数据库，默认True
    
    Returns:
        str: 输出文件路径，失败时返回None
    """
    try:
        # 读取JSON文件
        print(f"📁 正在读取文件: {input_file_path}")
        with open(input_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            print("❌ 错误：JSON文件应该包含一个数组")
            return None
        
        print(f"📊 原始数据记录数: {len(data)}")
        
        # 按original_id进行去重，保留ID最小的记录
        unique_records = {}
        duplicates_count = 0
        missing_original_id_count = 0
        
        for record in data:
            if not isinstance(record, dict):
                continue
                
            original_id = record.get('original_id')
            if original_id is None:
                missing_original_id_count += 1
                continue
                
            if original_id not in unique_records:
                unique_records[original_id] = record
            else:
                # 如果已存在，比较ID，保留ID较小的记录
                existing_id = unique_records[original_id].get('id')
                current_id = record.get('id')
                
                # 处理ID为None的情况
                if existing_id is None:
                    existing_id = float('inf')
                if current_id is None:
                    current_id = float('inf')
                
                if current_id < existing_id:
                    unique_records[original_id] = record
                duplicates_count += 1
        
        # 转换为列表
        deduplicated_data = list(unique_records.values())
        
        print(f"✅ 去重后记录数: {len(deduplicated_data)}")
        print(f"🗑️  删除重复记录数: {duplicates_count}")
        if missing_original_id_count > 0:
            print(f"⚠️  缺少original_id的记录数: {missing_original_id_count}")
        
        # 生成输出文件名
        if output_file_path is None:
            input_dir = os.path.dirname(input_file_path)
            input_name = os.path.splitext(os.path.basename(input_file_path))[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file_path = os.path.join(input_dir, f"{input_name}_deduplicated_{timestamp}.json")
        
        # 保存去重后的数据
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(deduplicated_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 去重后的数据已保存到: {output_file_path}")
        
        # 自动导入数据库
        if auto_import_db and DATABASE_AVAILABLE:
            print("\n🔄 正在导入数据库...")
            import_result = import_to_database(deduplicated_data)
            if import_result['success']:
                print(f"✅ 数据库导入成功！导入记录数: {import_result['imported_count']}")
                if import_result['skipped_count'] > 0:
                    print(f"⚠️  跳过记录数: {import_result['skipped_count']}")
            else:
                print(f"❌ 数据库导入失败: {import_result['message']}")
        elif auto_import_db and not DATABASE_AVAILABLE:
            print("⚠️  数据库模块不可用，跳过数据库导入")
        
        # 显示去重统计
        print("\n" + "="*50)
        print("📈 去重统计")
        print("="*50)
        print(f"原始记录数: {len(data)}")
        print(f"去重后记录数: {len(deduplicated_data)}")
        print(f"删除重复记录数: {duplicates_count}")
        if len(data) > 0:
            print(f"去重率: {duplicates_count/len(data)*100:.2f}%")
        
        # 显示前几条记录的基本信息
        if deduplicated_data:
            print(f"\n📋 前{min(5, len(deduplicated_data))}条记录信息:")
            for i, record in enumerate(deduplicated_data[:5], 1):
                title = record.get('title', '无标题')
                if len(title) > 40:
                    title = title[:40] + "..."
                print(f"{i}. ID: {record.get('id', 'None')}, Original ID: {record.get('original_id')}, Title: {title}")
        
        return output_file_path
        
    except FileNotFoundError:
        print(f"❌ 文件未找到: {input_file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON格式错误: {e}")
        return None
    except Exception as e:
        print(f"❌ 处理过程中发生错误: {e}")
        return None

def import_to_database(data_records):
    """
    将去重后的数据导入到数据库
    
    Args:
        data_records: 数据记录列表
    
    Returns:
        dict: 导入结果
    """
    try:
        # 初始化数据库连接
        db_path = "data/analysis_results.db"
        result_db = ResultDatabase(db_path)
        
        imported_count = 0
        skipped_count = 0
        errors = []
        
        print(f"📊 开始导入 {len(data_records)} 条记录到数据库...")
        
        for i, record in enumerate(data_records, 1):
            try:
                # 检查记录是否已存在（基于original_id）
                if record.get('original_id') is not None:
                    # 检查是否已存在相同original_id的记录
                    existing_results = result_db.get_analysis_results_by_original_id(record['original_id'])
                    if existing_results and len(existing_results) > 0:
                        print(f"⏭️  跳过重复记录 (original_id: {record['original_id']})")
                        skipped_count += 1
                        continue
                
                # 准备保存数据
                save_data = {
                    'original_id': record.get('original_id'),
                    'title': record.get('title', '无标题'),
                    'content': record.get('content', '无内容'),
                    'summary': record.get('summary', '无摘要'),
                    'source': record.get('source', '未知来源'),
                    'publish_time': record.get('publish_time', '未知时间'),
                    'sentiment_level': record.get('sentiment_level', '未知'),
                    'sentiment_reason': record.get('sentiment_reason', '无原因'),
                    'companies': record.get('companies', ''),
                    'duplicate_id': record.get('duplicate_id', '无'),
                    'duplication_rate': record.get('duplication_rate', 0.0),
                    'processing_time': record.get('processing_time', 0),
                    'tag_results': record.get('tag_results', {})
                }
                
                # 保存到数据库
                save_result = result_db.save_analysis_result(save_data)
                
                if save_result['success']:
                    imported_count += 1
                    if i % 10 == 0:  # 每10条显示一次进度
                        print(f"✅ 已导入 {i}/{len(data_records)} 条记录")
                else:
                    errors.append(f"记录 {i} 保存失败: {save_result['message']}")
                    skipped_count += 1
                    
            except Exception as e:
                errors.append(f"记录 {i} 处理失败: {str(e)}")
                skipped_count += 1
        
        print(f"✅ 数据库导入完成！成功: {imported_count}, 跳过: {skipped_count}")
        
        if errors:
            print(f"⚠️  导入过程中有 {len(errors)} 个错误:")
            for error in errors[:5]:  # 只显示前5个错误
                print(f"   - {error}")
            if len(errors) > 5:
                print(f"   ... 还有 {len(errors) - 5} 个错误")
        
        return {
            'success': True,
            'imported_count': imported_count,
            'skipped_count': skipped_count,
            'error_count': len(errors),
            'errors': errors,
            'message': f'成功导入 {imported_count} 条记录，跳过 {skipped_count} 条记录'
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'数据库导入失败: {str(e)}',
            'imported_count': 0,
            'skipped_count': 0,
            'error_count': 0,
            'errors': [str(e)]
        }

def deduplicate_database_records():
    """
    直接对数据库中的记录进行去重，用于系统自动化流程
    
    Returns:
        dict: 去重结果
    """
    try:
        if not DATABASE_AVAILABLE:
            return {
                'success': False,
                'message': '数据库模块不可用',
                'duplicates_removed': 0
            }
        
        print("🔄 开始数据库自动去重...")
        
        # 初始化数据库连接
        db_path = "data/analysis_results.db"
        result_db = ResultDatabase(db_path)
        
        # 获取所有记录
        all_results = result_db.get_analysis_results(page=1, page_size=10000)  # 获取大量数据
        
        if not all_results['success']:
            return {
                'success': False,
                'message': f'获取数据库记录失败: {all_results.get("message", "未知错误")}',
                'duplicates_removed': 0
            }
        
        data_records = all_results['data']
        total_records = len(data_records)
        
        if total_records == 0:
            return {
                'success': True,
                'message': '数据库中没有记录需要去重',
                'duplicates_removed': 0
            }
        
        print(f"📊 数据库中共有 {total_records} 条记录")
        
        # 按original_id进行去重，保留ID最小的记录
        unique_records = {}
        duplicates_count = 0
        records_to_delete = []
        
        for record in data_records:
            original_id = record.get('original_id')
            if original_id is None:
                continue
                
            if original_id not in unique_records:
                unique_records[original_id] = record
            else:
                # 如果已存在，比较ID，保留ID较小的记录
                existing_id = unique_records[original_id].get('id')
                current_id = record.get('id')
                
                # 处理ID为None的情况
                if existing_id is None:
                    existing_id = float('inf')
                if current_id is None:
                    current_id = float('inf')
                
                if current_id < existing_id:
                    # 当前记录ID更小，替换现有记录
                    records_to_delete.append(unique_records[original_id])
                    unique_records[original_id] = record
                    duplicates_count += 1
                else:
                    # 现有记录ID更小，删除当前记录
                    records_to_delete.append(record)
                    duplicates_count += 1
        
        if duplicates_count == 0:
            return {
                'success': True,
                'message': '数据库中没有重复记录',
                'duplicates_removed': 0
            }
        
        print(f"✅ 发现 {duplicates_count} 条重复记录，开始删除...")
        
        # 删除重复记录
        deleted_count = 0
        for record in records_to_delete:
            try:
                # 这里需要实现删除记录的方法
                # 由于ResultDatabase没有直接的删除方法，我们需要扩展它
                delete_result = result_db.delete_analysis_result(record.get('id'))
                if delete_result['success']:
                    deleted_count += 1
                else:
                    print(f"⚠️  删除记录 {record.get('id')} 失败: {delete_result['message']}")
            except Exception as e:
                print(f"⚠️  删除记录 {record.get('id')} 时发生错误: {e}")
        
        print(f"🗑️  成功删除 {deleted_count} 条重复记录")
        
        return {
            'success': True,
            'message': f'数据库去重完成，删除 {deleted_count} 条重复记录',
            'duplicates_removed': deleted_count,
            'total_records': total_records,
            'unique_records': len(unique_records)
        }
        
    except Exception as e:
        error_msg = f'数据库去重过程中发生错误: {str(e)}'
        print(f"❌ {error_msg}")
        return {
            'success': False,
            'message': error_msg,
            'duplicates_removed': 0
        }

def auto_export_after_dedup():
    """
    在去重完成后自动导出数据，用于系统自动化流程
    
    Returns:
        dict: 导出结果
    """
    try:
        if not DATABASE_AVAILABLE:
            return {
                'success': False,
                'message': '数据库模块不可用',
                'export_file': None
            }
        
        print("📤 开始自动导出...")
        
        # 初始化数据库连接
        db_path = "data/analysis_results.db"
        result_db = ResultDatabase(db_path)
        
        # 获取所有记录
        all_results = result_db.get_analysis_results(page=1, page_size=10000)
        
        if not all_results['success']:
            return {
                'success': False,
                'message': f'获取数据库记录失败: {all_results.get("message", "未知错误")}',
                'export_file': None
            }
        
        data_records = all_results['data']
        total_records = len(data_records)
        
        if total_records == 0:
            return {
                'success': False,
                'message': '数据库中没有记录可导出',
                'export_file': None
            }
        
        print(f"📊 准备导出 {total_records} 条记录")
        
        # 生成导出文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_dir = "exports"
        
        # 确保导出目录存在
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
        
        export_file = os.path.join(export_dir, f"auto_export_after_dedup_{timestamp}.json")
        
        # 导出数据
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(data_records, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 自动导出完成！文件: {export_file}")
        print(f"📈 导出记录数: {total_records}")
        
        return {
            'success': True,
            'message': f'自动导出完成，共导出 {total_records} 条记录',
            'export_file': export_file,
            'total_records': total_records
        }
        
    except Exception as e:
        error_msg = f'自动导出过程中发生错误: {str(e)}'
        print(f"❌ {error_msg}")
        return {
            'success': False,
            'message': error_msg,
            'export_file': None
        }

def enhanced_export_data(export_format='json', include_metadata=True, filter_tags=None):
    """
    增强的数据导出功能，支持多种格式和选项
    
    Args:
        export_format: 导出格式 ('json', 'csv', 'excel')
        include_metadata: 是否包含元数据
        filter_tags: 过滤标签列表，如 ['同业竞争', '关联交易']
    
    Returns:
        dict: 导出结果
    """
    try:
        if not DATABASE_AVAILABLE:
            return {
                'success': False,
                'message': '数据库模块不可用',
                'export_file': None
            }
        
        print(f"📤 开始增强导出 (格式: {export_format})...")
        
        # 初始化数据库连接
        db_path = "data/analysis_results.db"
        result_db = ResultDatabase(db_path)
        
        # 获取所有记录
        all_results = result_db.get_analysis_results(page=1, page_size=10000)
        
        if not all_results['success']:
            return {
                'success': False,
                'message': f'获取数据库记录失败: {all_results.get("message", "未知错误")}',
                'export_file': None
            }
        
        data_records = all_results['data']
        total_records = len(data_records)
        
        if total_records == 0:
            return {
                'success': False,
                'message': '数据库中没有记录可导出',
                'export_file': None
            }
        
        # 应用标签过滤
        if filter_tags:
            filtered_records = []
            for record in data_records:
                for tag in filter_tags:
                    tag_field = f'tag_{tag}'
                    if tag_field in record and record[tag_field] == '是':
                        filtered_records.append(record)
                        break
            data_records = filtered_records
            print(f"🔍 标签过滤后记录数: {len(data_records)}")
        
        # 生成导出文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_dir = "exports"
        
        # 确保导出目录存在
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
        
        if export_format == 'json':
            export_file = os.path.join(export_dir, f"enhanced_export_{timestamp}.json")
            export_result = export_to_json(data_records, export_file, include_metadata)
        elif export_format == 'csv':
            export_file = os.path.join(export_dir, f"enhanced_export_{timestamp}.csv")
            export_result = export_to_csv(data_records, export_file, include_metadata)
        elif export_format == 'excel':
            export_file = os.path.join(export_dir, f"enhanced_export_{timestamp}.xlsx")
            export_result = export_to_excel(data_records, export_file, include_metadata)
        else:
            return {
                'success': False,
                'message': f'不支持的导出格式: {export_format}',
                'export_file': None
            }
        
        if export_result['success']:
            print(f"✅ 增强导出完成！文件: {export_file}")
            print(f"📈 导出记录数: {len(data_records)}")
            
            return {
                'success': True,
                'message': f'增强导出完成，共导出 {len(data_records)} 条记录',
                'export_file': export_file,
                'total_records': len(data_records),
                'format': export_format
            }
        else:
            return export_result
        
    except Exception as e:
        error_msg = f'增强导出过程中发生错误: {str(e)}'
        print(f"❌ {error_msg}")
        return {
            'success': False,
            'message': error_msg,
            'export_file': None
        }

def export_to_json(data_records, export_file, include_metadata=True):
    """导出为JSON格式"""
    try:
        export_data = {
            'export_info': {
                'export_time': datetime.now().isoformat(),
                'total_records': len(data_records),
                'format': 'json'
            } if include_metadata else {},
            'data': data_records
        }
        
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        return {'success': True, 'message': 'JSON导出成功'}
        
    except Exception as e:
        return {'success': False, 'message': f'JSON导出失败: {str(e)}'}

def export_to_csv(data_records, export_file, include_metadata=True):
    """导出为CSV格式"""
    try:
        import csv
        
        with open(export_file, 'w', encoding='utf-8', newline='') as f:
            if data_records:
                # 获取所有字段名
                fieldnames = list(data_records[0].keys())
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                # 写入数据
                for record in data_records:
                    writer.writerow(record)
        
        return {'success': True, 'message': 'CSV导出成功'}
        
    except Exception as e:
        return {'success': False, 'message': f'CSV导出失败: {str(e)}'}

def export_to_excel(data_records, export_file, include_metadata=True):
    """导出为Excel格式"""
    try:
        import pandas as pd
        
        # 转换为DataFrame
        df = pd.DataFrame(data_records)
        
        # 写入Excel文件
        with pd.ExcelWriter(export_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='分析结果', index=False)
            
            # 如果有元数据，创建元数据工作表
            if include_metadata:
                metadata_df = pd.DataFrame([{
                    '导出时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    '总记录数': len(data_records),
                    '导出格式': 'Excel'
                }])
                metadata_df.to_excel(writer, sheet_name='导出信息', index=False)
        
        return {'success': True, 'message': 'Excel导出成功'}
        
    except Exception as e:
        return {'success': False, 'message': f'Excel导出失败: {str(e)}'}

def main():
    """主函数"""
    print("🚀 JSON文件去重工具")
    print("="*50)
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        auto_import = True if len(sys.argv) <= 3 else (sys.argv[3].lower() != 'false')
    else:
        # 如果没有命令行参数，使用默认路径
        input_file = r"C:\Users\anyut\Downloads\analysis_results_2025-08-26 (4).json"
        output_file = None
        auto_import = True
        
        # 检查默认文件是否存在
        if not os.path.exists(input_file):
            print("❌ 默认文件不存在，请提供文件路径作为参数")
            print("使用方法: python deduplicate_any_json.py <输入文件路径> [输出文件路径] [是否导入数据库]")
            print("示例: python deduplicate_any_json.py data.json")
            print("示例: python deduplicate_any_json.py data.json output.json false")
            return
    
    print(f"输入文件: {input_file}")
    if output_file:
        print(f"输出文件: {output_file}")
    print(f"自动导入数据库: {'是' if auto_import else '否'}")
    
    # 执行去重
    output_file = deduplicate_json_by_original_id(input_file, output_file, auto_import)
    
    if output_file:
        print(f"\n🎉 去重完成！")
        print(f"输出文件: {output_file}")
        
        # 验证去重结果
        print("\n🔍 正在验证去重结果...")
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                final_data = json.load(f)
            
            # 检查是否还有重复的original_id
            original_ids = [record.get('original_id') for record in final_data if record.get('original_id') is not None]
            unique_original_ids = set(original_ids)
            
            if len(original_ids) == len(unique_original_ids):
                print("✅ 验证通过：没有重复的original_id")
            else:
                print("❌ 验证失败：仍然存在重复的original_id")
                
        except Exception as e:
            print(f"验证过程中发生错误: {e}")
    else:
        print("❌ 去重失败")

if __name__ == "__main__":
    main()
