from datetime import datetime


def select_id(cur, url):
    cur.execute("""
                SELECT id
                FROM urls
                WHERE name = %s;
                """,
                (url,))
    return cur.fetchone()


def insert_url(cur, url):
    cur.execute("""
                INSERT INTO urls
                (name, created_at)
                VALUES (%s, %s)
                RETURNING id;
                """,
                (url, datetime.now()))
    return cur.fetchone()[0]


def select_url(cur, url_id):
    cur.execute("""
                SELECT * 
                FROM urls 
                WHERE id = %s;
                """,
                (url_id,))
    return cur.fetchone()


def select_checks(cur, url_id):
    cur.execute("""
                SELECT
                url_checks.id, 
                url_checks.status_code, 
                url_checks.h1, 
                url_checks.title, 
                url_checks.description, 
                url_checks.created_at 
                FROM url_checks 
                JOIN urls 
                ON urls.id = url_id 
                WHERE urls.id = %s;
                """,
                (url_id,))
    return cur.fetchall()


def select_last_checks(cur):
    cur.execute("""
                SELECT 
                urls.id, 
                urls.name, 
                MAX(url_checks.created_at) 
                FROM urls 
                LEFT JOIN url_checks 
                ON urls.id = url_checks.url_id 
                GROUP BY urls.id, urls.name 
                ORDER BY urls.created_at 
                DESC;
                """)
    return cur.fetchall()


def select_status_code(cur, url):
    cur.execute("""
                SELECT status_code 
                FROM url_checks 
                WHERE url_id = %s AND created_at = %s
                """,
                (url[0], url[2]))
    return cur.fetchone()


def select_name(cur, url_id):
    cur.execute("""
                SELECT name 
                FROM urls 
                WHERE id = %s
                """,
                (url_id,))
    return cur.fetchone()[0]


def insert_check(cur, url_id, status_code, h1, title, meta):
    cur.execute("""
                INSERT INTO url_checks 
                (url_id, status_code, h1, title, description, created_at) 
                VALUES (%s, %s, %s, %s, %s, %s);
                """,
                (url_id, status_code, h1, title, meta, datetime.now()))
