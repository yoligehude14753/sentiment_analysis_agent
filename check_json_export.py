#!/usr/bin/env python3
"""检查JSON导出重复数据问题"""

import sqlite3
import requests
import json

def check_database():
    """检查数据库中的数据"""
    print("="*60)
    print("检查数据库中的数据")
    print("="*60)
    
    conn = sqlite3.connect('data/analysis_results.db')
    cursor = conn.cursor()
    
    # 查看表结构
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("数据库中的表:")
    for table in tables:
        print(f"- {table[0]}")
    
    # 查看analysis_results表的结构
    cursor.execute("PRAGMA table_info(analysis_results)")
    columns = cursor.fetchall()
    print(f"\nanalysis_results表结构:")
    for col in columns:
        print(f"- {col[1]} ({col[2]})")
    
    # 查看analysis_results表的数据
    cursor.execute("SELECT * FROM analysis_results")
    results = cursor.fetchall()
    
    print(f"\nanalysis_results表中的数据 (共{len(results)}条):")
    if results:
        # 获取列名
        cursor.execute("PRAGMA table_info(analysis_results)")
        column_info = cursor.fetchall()
        column_names = [col[1] for col in column_info]
        
        for i, row in enumerate(results):
            print(f"记录 {i+1}:")
            for j, value in enumerate(row):
                if column_names[j] in ['title', 'content', 'summary']:
                    display_value = str(value)[:50] + "..." if value and len(str(value)) > 50 else value
                else:
                    display_value = value
                print(f"  {column_names[j]}: {display_value}")
            print()
    
    conn.close()

def test_json_export():
    """测试JSON导出功能"""
    print("="*60)
    print("测试JSON导出功能")
    print("="*60)
    
    # 准备导出请求
    export_request = {
        "format": "json",
        "options": {
            "original": True,
            "sentiment": True,
            "tags": False,  # 简化输出
            "companies": True,
            "duplication": True,
            "processingTime": False
        }
    }
    
    try:
        response = requests.post("http://localhost:8000/api/results/export", 
                               json=export_request, timeout=30)
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            # 保存响应到文件
            with open("debug_json_export.json", "wb") as f:
                f.write(response.content)
            
            # 解析JSON查看内容
            json_data = response.json()
            print(f"导出的JSON数据条数: {len(json_data)}")
            
            # 检查是否有重复数据
            original_ids = []
            for i, item in enumerate(json_data):
                original_id = item.get('original_id')
                original_ids.append(original_id)
                print(f"记录 {i+1}: original_id={original_id}, title={item.get('title', '')[:50]}...")
            
            # 检测重复
            unique_ids = set(original_ids)
            if len(original_ids) != len(unique_ids):
                print(f"\n⚠️  发现重复数据!")
                print(f"总记录数: {len(original_ids)}")
                print(f"唯一ID数: {len(unique_ids)}")
                
                # 找出重复的ID
                from collections import Counter
                id_counts = Counter(original_ids)
                duplicates = {id_val: count for id_val, count in id_counts.items() if count > 1}
                print("重复的original_id:")
                for id_val, count in duplicates.items():
                    print(f"  {id_val}: 出现 {count} 次")
            else:
                print("✓ 没有发现重复数据")
                
        else:
            print(f"导出失败: {response.text}")
            
    except Exception as e:
        print(f"请求失败: {str(e)}")

if __name__ == "__main__":
    check_database()
    test_json_export()
