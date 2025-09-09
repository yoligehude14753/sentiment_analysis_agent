"""
正确的重复度修复脚本
使用合理的阈值设置
"""
import sqlite3
from text_deduplicator import SimHash
from typing import List, Dict, Tuple
import json

def calculate_hamming_distance(hash1: str, hash2: str) -> int:
    """计算两个SimHash的汉明距离"""
    try:
        # 转换为整数
        int1 = int(hash1, 16)
        int2 = int(hash2, 16)
        # 计算汉明距离
        return bin(int1 ^ int2).count('1')
    except ValueError:
        return 64  # 如果转换失败，返回最大距离

def find_similar_texts(target_simhash: str, all_texts: List[Dict], similarity_threshold: float = 0.75, max_hamming_distance: int = 16) -> List[Dict]:
    """查找与目标文本相似的文本（使用更严格的阈值）"""
    similar_texts = []
    
    for text_item in all_texts:
        if text_item['simhash'] != target_simhash:  # 不与自己比较
            hamming_dist = calculate_hamming_distance(target_simhash, text_item['simhash'])
            similarity = 1 - (hamming_dist / 64)  # 64位SimHash
            
            # 使用更严格的阈值
            if hamming_dist <= max_hamming_distance and similarity >= similarity_threshold:
                similar_texts.append({
                    'id': text_item['id'],
                    'title': text_item['title'],
                    'publish_time': text_item['publish_time'],
                    'hamming_distance': hamming_dist,
                    'similarity': round(similarity, 3)
                })
    
    # 按相似度排序
    similar_texts.sort(key=lambda x: x['similarity'], reverse=True)
    return similar_texts

def fix_duplicate_calculation_correct():
    """正确修复重复度计算"""
    print("=== 正确修复重复度计算 ===\n")
    
    # 连接数据库
    conn = sqlite3.connect('data/analysis_results.db')
    cursor = conn.cursor()
    
    # 获取所有记录
    cursor.execute('SELECT id, title, content, duplicate_id, publish_time FROM sentiment_results')
    rows = cursor.fetchall()
    
    print(f"正在处理 {len(rows)} 条记录...\n")
    print("使用阈值: 汉明距离≤16, 相似度≥75%\n")
    
    # 构建所有文本的SimHash列表
    all_texts = []
    for row in rows:
        record_id, title, content, duplicate_id, publish_time = row
        all_texts.append({
            'id': record_id,
            'title': title,
            'content': content,
            'simhash': duplicate_id,  # duplicate_id实际上存储的是SimHash
            'publish_time': publish_time
        })
    
    # 为每条记录重新计算重复度
    updated_count = 0
    high_duplicate_examples = []
    duplicate_pairs = []
    
    for i, record in enumerate(all_texts):
        record_id = record['id']
        simhash = record['simhash']
        
        if (i + 1) % 50 == 0:  # 每50条记录打印一次进度
            print(f"处理进度: {i+1}/{len(all_texts)} ({((i+1)/len(all_texts)*100):.1f}%)")
        
        # 查找相似文本
        similar_texts = find_similar_texts(simhash, all_texts)
        
        if similar_texts:
            # 找到最相似的文本
            best_match = similar_texts[0]
            
            # 计算重复度（使用最高相似度）
            duplication_rate = best_match['similarity']
            
            # 记录高重复度示例
            high_duplicate_examples.append({
                'id': record_id,
                'title': record['title'][:50],
                'duplication_rate': duplication_rate,
                'best_match_id': best_match['id'],
                'best_match_title': best_match['title'][:50],
                'hamming_distance': best_match['hamming_distance'],
                'publish_time': record['publish_time'],
                'best_match_publish_time': best_match['publish_time']
            })
            
            # 记录重复对（避免重复记录）
            pair_key = tuple(sorted([record_id, best_match['id']]))
            if pair_key not in [tuple(sorted([p['id1'], p['id2']])) for p in duplicate_pairs]:
                duplicate_pairs.append({
                    'id1': record_id,
                    'title1': record['title'][:50],
                    'id2': best_match['id'],
                    'title2': best_match['title'][:50],
                    'similarity': duplication_rate,
                    'hamming_distance': best_match['hamming_distance']
                })
            
        else:
            # 没有找到相似文本
            duplication_rate = 0.0
        
        # 更新数据库
        try:
            cursor.execute('''
                UPDATE sentiment_results 
                SET duplication_rate = ?
                WHERE id = ?
            ''', (duplication_rate, record_id))
            
            updated_count += 1
            
        except Exception as e:
            print(f"  - 记录 {record_id} 更新失败: {e}")
    
    # 提交更改
    conn.commit()
    print(f"\n更新完成！成功更新 {updated_count} 条记录")
    
    # 显示统计信息
    cursor.execute('SELECT COUNT(*) FROM sentiment_results WHERE duplication_rate > 0.75')
    high_duplicate_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM sentiment_results WHERE duplication_rate = 0')
    unique_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT AVG(duplication_rate) FROM sentiment_results WHERE duplication_rate > 0')
    avg_duplication_nonzero = cursor.fetchone()[0] or 0
    
    cursor.execute('SELECT AVG(duplication_rate) FROM sentiment_results')
    avg_duplication_all = cursor.fetchone()[0] or 0
    
    print(f"\n=== 统计信息 ===")
    print(f"高重复度文本 (>75%): {high_duplicate_count}")
    print(f"唯一文本 (0%): {unique_count}")
    print(f"有重复的文本平均重复度: {avg_duplication_nonzero:.3f}")
    print(f"所有文本平均重复度: {avg_duplication_all:.3f}")
    
    # 显示重复度分布
    print(f"\n=== 重复度分布 ===")
    ranges = [
        ("0% (唯一)", 0.0, 0.0),
        ("1-50%", 0.01, 0.5),
        ("51-75%", 0.51, 0.75),
        ("76-90%", 0.76, 0.9),
        ("91-100%", 0.91, 1.0)
    ]
    
    for range_name, min_val, max_val in ranges:
        if min_val == max_val:
            cursor.execute('SELECT COUNT(*) FROM sentiment_results WHERE duplication_rate = ?', (min_val,))
        else:
            cursor.execute('SELECT COUNT(*) FROM sentiment_results WHERE duplication_rate >= ? AND duplication_rate <= ?', (min_val, max_val))
        count = cursor.fetchone()[0]
        percentage = (count / len(rows)) * 100 if len(rows) > 0 else 0
        print(f"{range_name}: {count} 条 ({percentage:.1f}%)")
    
    # 显示高重复度示例
    if high_duplicate_examples:
        print(f"\n=== 高重复度示例（前10个）===")
        # 按重复度排序
        high_duplicate_examples.sort(key=lambda x: x['duplication_rate'], reverse=True)
        
        for example in high_duplicate_examples[:10]:
            print(f"\nID {example['id']}: {example['title']}...")
            print(f"重复度: {example['duplication_rate']}")
            print(f"最相似文本: ID {example['best_match_id']} - {example['best_match_title']}...")
            print(f"汉明距离: {example['hamming_distance']}")
            print(f"发布时间: {example['publish_time']} vs {example['best_match_publish_time']}")
    
    # 显示重复对
    if duplicate_pairs:
        print(f"\n=== 发现的重复对（前10个）===")
        duplicate_pairs.sort(key=lambda x: x['similarity'], reverse=True)
        
        for pair in duplicate_pairs[:10]:
            print(f"\n重复对 - 相似度: {pair['similarity']}")
            print(f"文本1: ID {pair['id1']} - {pair['title1']}...")
            print(f"文本2: ID {pair['id2']} - {pair['title2']}...")
            print(f"汉明距离: {pair['hamming_distance']}")
    
    print(f"\n总共发现 {len(duplicate_pairs)} 个重复对")
    
    conn.close()

if __name__ == "__main__":
    fix_duplicate_calculation_correct()

















