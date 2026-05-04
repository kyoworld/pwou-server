import os
import psycopg2

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL 환경변수가 설정되지 않았습니다.")

conn = psycopg2.connect(DATABASE_URL)
c = conn.cursor()

c.execute('SELECT COUNT(*) FROM submissions WHERE printed = 0 AND id > 0')
count = c.fetchone()[0]
print(f"printed=0 항목 {count}개 발견 (id > 0)")

c.execute('UPDATE submissions SET printed = 1 WHERE printed = 0 AND id > 0')
conn.commit()
print(f"{c.rowcount}개 → printed=1 업데이트 완료")

conn.close()
