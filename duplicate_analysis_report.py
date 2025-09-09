"""
重复度分析报告生成器
生成完整的重复检测分析报告
"""
import sqlite3
import json
from datetime import datetime

def generate_duplicate_analysis_report():
    """生成重复度分析报告"""
    print("=== 重复度分析报告 ===")
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 连接数据库
    conn = sqlite3.connect('data/analysis_results.db')
    cursor = conn.cursor()
    
    # 获取总体统计
    cursor.execute('SELECT COUNT(*) FROM sentiment_results')
    total_records = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM sentiment_results WHERE duplication_rate = 0')
    unique_records = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM sentiment_results WHERE duplication_rate > 0')
    duplicate_records = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM sentiment_results WHERE duplication_rate >= 0.75')
    high_duplicate_records = cursor.fetchone()[0]
    
    cursor.execute('SELECT AVG(duplication_rate) FROM sentiment_results WHERE duplication_rate > 0')
    avg_duplicate_rate = cursor.fetchone()[0] or 0
    
    print(f"\n📊 总体统计:")
    print(f"  总记录数: {total_records}")
    print(f"  唯一记录: {unique_records} ({unique_records/total_records*100:.1f}%)")
    print(f"  有重复记录: {duplicate_records} ({duplicate_records/total_records*100:.1f}%)")
    print(f"  高重复度记录 (≥75%): {high_duplicate_records} ({high_duplicate_records/total_records*100:.1f}%)")
    print(f"  重复记录平均重复度: {avg_duplicate_rate:.1f}%")
    
    # 重复度分布
    print(f"\n📈 重复度分布:")
    ranges = [
        ("唯一 (0%)", 0.0, 0.0),
        ("低重复 (1-50%)", 0.01, 0.5),
        ("中重复 (51-75%)", 0.51, 0.75),
        ("高重复 (76-90%)", 0.76, 0.9),
        ("极高重复 (91-100%)", 0.91, 1.0)
    ]
    
    for range_name, min_val, max_val in ranges:
        if min_val == max_val:
            cursor.execute('SELECT COUNT(*) FROM sentiment_results WHERE duplication_rate = ?', (min_val,))
        else:
            cursor.execute('SELECT COUNT(*) FROM sentiment_results WHERE duplication_rate >= ? AND duplication_rate <= ?', (min_val, max_val))
        count = cursor.fetchone()[0]
        percentage = (count / total_records) * 100 if total_records > 0 else 0
        print(f"  {range_name}: {count} 条 ({percentage:.1f}%)")
    
    # 高重复度案例详细分析
    cursor.execute('''
        SELECT id, title, duplication_rate, publish_time, content
        FROM sentiment_results 
        WHERE duplication_rate >= 0.75 
        ORDER BY duplication_rate DESC
    ''')
    high_dup_records = cursor.fetchall()
    
    if high_dup_records:
        print(f"\n🔍 高重复度案例分析:")
        
        for record in high_dup_records:
            record_id, title, dup_rate, publish_time, content = record
            print(f"\n  📋 记录 ID {record_id}:")
            print(f"     标题: {title}")
            print(f"     重复度: {dup_rate*100:.1f}%")
            print(f"     发布时间: {publish_time}")
            
            # 分析内容特征
            if content:
                content_preview = content[:100].replace('\n', ' ').replace('\r', ' ')
                print(f"     内容预览: {content_preview}...")
                
                # 分析是否为HTML内容
                if content.strip().startswith('<!doctype') or content.strip().startswith('<html'):
                    print(f"     内容类型: HTML格式")
                elif 'http' in content.lower():
                    print(f"     内容类型: 包含链接")
                else:
                    print(f"     内容类型: 纯文本")
    
    # 查找具体的重复对
    print(f"\n🔗 重复文本对分析:")
    
    # 通过重复度找到配对的文本
    cursor.execute('''
        SELECT r1.id, r1.title, r1.duplication_rate, r1.publish_time,
               r2.id, r2.title, r2.duplication_rate, r2.publish_time
        FROM sentiment_results r1
        JOIN sentiment_results r2 ON r1.duplication_rate = r2.duplication_rate 
        WHERE r1.duplication_rate >= 0.75 AND r1.id < r2.id
        ORDER BY r1.duplication_rate DESC
    ''')
    
    duplicate_pairs = cursor.fetchall()
    
    if duplicate_pairs:
        for i, pair in enumerate(duplicate_pairs, 1):
            id1, title1, rate1, time1, id2, title2, rate2, time2 = pair
            print(f"\n  {i}. 重复对 (相似度: {rate1*100:.1f}%):")
            print(f"     文本A: ID {id1} - {title1}")
            print(f"     时间A: {time1}")
            print(f"     文本B: ID {id2} - {title2}")
            print(f"     时间B: {time2}")
            
            # 计算时间差
            try:
                time1_obj = datetime.strptime(time1, '%Y-%m-%d %H:%M:%S')
                time2_obj = datetime.strptime(time2, '%Y-%m-%d %H:%M:%S')
                time_diff = abs((time2_obj - time1_obj).total_seconds() / 3600)  # 小时
                print(f"     时间间隔: {time_diff:.1f} 小时")
            except:
                print(f"     时间间隔: 无法计算")
    
    # 时间分布分析
    print(f"\n📅 重复文本的时间分布:")
    cursor.execute('''
        SELECT DATE(publish_time) as date, COUNT(*) as count
        FROM sentiment_results 
        WHERE duplication_rate > 0
        GROUP BY DATE(publish_time)
        ORDER BY date
    ''')
    
    date_distribution = cursor.fetchall()
    for date, count in date_distribution:
        print(f"  {date}: {count} 条重复文本")
    
    # 建议和总结
    print(f"\n💡 分析结论和建议:")
    
    duplicate_ratio = duplicate_records / total_records if total_records > 0 else 0
    
    if duplicate_ratio < 0.05:
        print(f"  ✅ 重复率很低 ({duplicate_ratio*100:.1f}%)，数据质量良好")
    elif duplicate_ratio < 0.15:
        print(f"  ⚠️  重复率适中 ({duplicate_ratio*100:.1f}%)，建议关注重复来源")
    else:
        print(f"  🚨 重复率较高 ({duplicate_ratio*100:.1f}%)，需要加强数据清洗")
    
    if high_duplicate_records > 0:
        print(f"  📌 发现 {high_duplicate_records} 条高重复度文本，建议检查:")
        print(f"     - 是否为同一事件的不同报道")
        print(f"     - 是否为模板化内容（如公告、报告等）")
        print(f"     - 是否需要在采集时进行去重")
    
    print(f"\n🔧 技术参数:")
    print(f"  - 相似度阈值: ≥75%")
    print(f"  - 汉明距离阈值: ≤16")
    print(f"  - SimHash算法: 64位，窗口大小6")
    print(f"  - 检测精度: 高（避免误判）")
    
    conn.close()
    print(f"\n报告生成完成！")

if __name__ == "__main__":
    generate_duplicate_analysis_report()

















