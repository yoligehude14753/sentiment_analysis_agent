import sqlite3

conn = sqlite3.connect('data/analysis_results.db')
cursor = conn.cursor()

# 检查表结构
cursor.execute("PRAGMA table_info(sentiment_results)")
columns = cursor.fetchall()
print('表结构:')
for col in columns:
    print(f'  {col[1]} ({col[2]})')

# 检查记录总数
cursor.execute('SELECT COUNT(*) FROM sentiment_results')
total_count = cursor.fetchone()[0]
print(f'\n记录总数: {total_count}')

# 查看所有记录
if total_count > 0:
    cursor.execute('SELECT id, title FROM sentiment_results ORDER BY id')
    rows = cursor.fetchall()
    print('\n现有记录:')
    for row in rows:
        print(f'  ID {row[0]}: {row[1]}')
else:
    print('\n数据库中没有记录')

conn.close()






