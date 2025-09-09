#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
清空结果数据库中的所有内容
"""

import sqlite3
import os
from datetime import datetime

def clear_analysis_database():
    """清空分析结果数据库"""
    
    databases = [
        "data/analysis_results.db",
        "sentiment_results.db", 
        "sentiment_analysis.db"
    ]
    
    for db_path in databases:
        if not os.path.exists(db_path):
            print(f"⏭️  跳过不存在的数据库: {db_path}")
            continue
            
        print(f"\n🗑️  清空数据库: {db_path}")
        
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # 检查表是否存在
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='sentiment_results'
                """)
                
                if not cursor.fetchone():
                    print(f"  ⏭️  表 sentiment_results 不存在，跳过")
                    continue
                
                # 获取记录数量
                cursor.execute("SELECT COUNT(*) FROM sentiment_results")
                count = cursor.fetchone()[0]
                print(f"  📊 当前记录数: {count}")
                
                if count == 0:
                    print(f"  ✅ 数据库已经是空的")
                    continue
                
                # 删除所有数据
                cursor.execute("DELETE FROM sentiment_results")
                
                # 重置自增ID
                cursor.execute("DELETE FROM sqlite_sequence WHERE name='sentiment_results'")
                
                # 验证清空结果
                cursor.execute("SELECT COUNT(*) FROM sentiment_results")
                new_count = cursor.fetchone()[0]
                
                print(f"  ✅ 已删除 {count} 条记录")
                print(f"  ✅ 清空后记录数: {new_count}")
                print(f"  ✅ 自增ID已重置")
                
                # 提交更改
                conn.commit()
                
        except Exception as e:
            print(f"  ❌ 清空数据库失败: {e}")

def clear_all_databases():
    """清空所有相关数据库"""
    print("🧹 开始清空所有数据库...")
    
    # 清空分析结果数据库
    clear_analysis_database()
    
    # 清空其他可能的表
    print("\n🔍 检查其他表...")
    
    db_path = "data/analysis_results.db"
    if os.path.exists(db_path):
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # 获取所有表名
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name != 'sqlite_sequence'
                """)
                
                tables = cursor.fetchall()
                
                for table in tables:
                    table_name = table[0]
                    if table_name != 'sentiment_results':
                        print(f"  📋 发现其他表: {table_name}")
                        
                        # 检查记录数
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        count = cursor.fetchone()[0]
                        print(f"    - 记录数: {count}")
                        
                        if count > 0:
                            # 清空表
                            cursor.execute(f"DELETE FROM {table_name}")
                            cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table_name}'")
                            print(f"    ✅ 已清空表 {table_name}")
                
                conn.commit()
                
        except Exception as e:
            print(f"  ❌ 检查其他表失败: {e}")

def verify_database_clean():
    """验证数据库是否已清空"""
    print("\n🔍 验证数据库清空结果...")
    
    db_path = "data/analysis_results.db"
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # 检查主表
            cursor.execute("SELECT COUNT(*) FROM sentiment_results")
            main_count = cursor.fetchone()[0]
            
            # 检查其他表
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name != 'sqlite_sequence'
            """)
            
            tables = cursor.fetchall()
            total_records = 0
            
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                total_records += count
                print(f"  📊 {table_name}: {count} 条记录")
            
            print(f"\n📈 总计记录数: {total_records}")
            
            if total_records == 0:
                print("✅ 所有数据库都已成功清空!")
            else:
                print("⚠️  仍有数据未清空")
                
    except Exception as e:
        print(f"❌ 验证失败: {e}")

if __name__ == "__main__":
    print("🧹 数据库清空工具")
    print("=" * 50)
    
    # 清空所有数据库
    clear_all_databases()
    
    # 验证清空结果
    verify_database_clean()
    
    print("\n✅ 数据库清空操作完成!")
    print("\n💡 提示:")
    print("  - 所有测试数据已被删除")
    print("  - 数据库表结构保持不变")
    print("  - 可以重新开始数据收集和分析")
