#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
检查数据库表结构
"""

import sqlite3
import os

def check_database_structure():
    """检查数据库表结构"""
    print("=== 检查数据库表结构 ===")
    
    # 检查结果数据库
    result_db_path = "data/analysis_results.db"
    if os.path.exists(result_db_path):
        print(f"\n📊 检查结果数据库: {result_db_path}")
        try:
            with sqlite3.connect(result_db_path) as conn:
                cursor = conn.cursor()
                
                # 获取所有表
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                print(f"✅ 数据库中的表: {[table[0] for table in tables]}")
                
                for table in tables:
                    table_name = table[0]
                    print(f"\n📋 表: {table_name}")
                    
                    # 获取表结构
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()
                    
                    print("  列结构:")
                    for col in columns:
                        col_id, col_name, col_type, not_null, default_val, pk = col
                        print(f"    {col_name}: {col_type} {'NOT NULL' if not_null else 'NULL'} {'PRIMARY KEY' if pk else ''}")
                    
                    # 获取记录数
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    print(f"  记录数: {count}")
                    
                    # 获取示例数据
                    if count > 0:
                        cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
                        sample = cursor.fetchone()
                        print(f"  示例数据: {sample}")
                        
        except Exception as e:
            print(f"❌ 检查结果数据库失败: {e}")
    else:
        print(f"❌ 结果数据库不存在: {result_db_path}")
    
    # 检查舆情数据库
    sentiment_db_path = "data/sentiment_analysis.db"
    if os.path.exists(sentiment_db_path):
        print(f"\n📊 检查舆情数据库: {sentiment_db_path}")
        try:
            with sqlite3.connect(sentiment_db_path) as conn:
                cursor = conn.cursor()
                
                # 获取所有表
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                print(f"✅ 数据库中的表: {[table[0] for table in tables]}")
                
                for table in tables:
                    table_name = table[0]
                    print(f"\n📋 表: {table_name}")
                    
                    # 获取表结构
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()
                    
                    print("  列结构:")
                    for col in columns:
                        col_id, col_name, col_type, not_null, default_val, pk = col
                        print(f"    {col_name}: {col_type} {'NOT NULL' if not_null else 'NULL'} {'PRIMARY KEY' if pk else ''}")
                    
                    # 获取记录数
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    print(f"  记录数: {count}")
                    
        except Exception as e:
            print(f"❌ 检查舆情数据库失败: {e}")
    else:
        print(f"❌ 舆情数据库不存在: {sentiment_db_path}")

def check_table_compatibility():
    """检查表兼容性"""
    print("\n=== 检查表兼容性 ===")
    
    result_db_path = "data/analysis_results.db"
    if os.path.exists(result_db_path):
        try:
            with sqlite3.connect(result_db_path) as conn:
                cursor = conn.cursor()
                
                # 检查是否有 sentiment_results 表
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sentiment_results'")
                has_table = cursor.fetchone()
                
                if has_table:
                    print("✅ sentiment_results 表存在")
                    
                    # 检查是否有 query_text 列
                    cursor.execute("PRAGMA table_info(sentiment_results)")
                    columns = cursor.fetchall()
                    column_names = [col[1] for col in columns]
                    
                    if 'query_text' in column_names:
                        print("✅ query_text 列存在")
                    else:
                        print("❌ query_text 列缺失")
                        print(f"  现有列: {column_names}")
                        
                        # 尝试添加缺失的列
                        try:
                            cursor.execute("ALTER TABLE sentiment_results ADD COLUMN query_text TEXT")
                            conn.commit()
                            print("✅ 已添加 query_text 列")
                        except Exception as e:
                            print(f"❌ 添加 query_text 列失败: {e}")
                else:
                    print("❌ sentiment_results 表不存在")
                    print("  现有表:")
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()
                    for table in tables:
                        print(f"    - {table[0]}")
                        
        except Exception as e:
            print(f"❌ 检查表兼容性失败: {e}")

if __name__ == "__main__":
    check_database_structure()
    check_table_compatibility()
