import psycopg2
import psycopg2.extras
from datetime import datetime
from data_ingestion import raw
from data_processing import extract_transform, geolocation

TABLE = 't_log'
YEAR = 2026  # syslog lines have no year

connection = psycopg2.connect(
    host='localhost',
    port=5432,
    user='postgres',
    password='123456',    
    dbname='log_analyser',
    cursor_factory=psycopg2.extras.RealDictCursor
)


def create_table(name):
    with connection.cursor() as cursor:
        try:
            cursor.execute('CREATE TABLE IF NOT EXISTS ' + name +
                           ' (id SERIAL PRIMARY KEY,'
                           ' log_date TIMESTAMP NOT NULL, hostname VARCHAR(100),'
                           ' service VARCHAR(50), pid INT, event_type VARCHAR(50),'
                           ' username VARCHAR(100), ip VARCHAR(45), port INT,'
                           ' attempts INT NOT NULL DEFAULT 1,'
                           ' country VARCHAR(10), city VARCHAR(100), raw_line TEXT)')
            connection.commit()
        except psycopg2.Error as e:
            print(e)
            connection.rollback()


def clear_table(name):
    with connection.cursor() as cursor:
        try:
            cursor.execute('TRUNCATE TABLE ' + name)
            connection.commit()
        except psycopg2.Error as e:
            print(e)
            connection.rollback()


def to_tuple(result, row, year=YEAR):
    log_date = datetime.strptime(
        f"{year} {result['month']} {result['day']} {result['time']}", '%Y %b %d %H:%M:%S')
    return (log_date, result['hostname'], result['service'], result['pid'],
            result['event_type'], result['username'], result['ip'],
            result['port'], result['attempts'], row)


def load_all(table_name, logs):
    with connection.cursor() as cursor:
        try:
            cursor.executemany('INSERT INTO ' + table_name +
                               ' (log_date, hostname, service, pid, event_type,'
                               ' username, ip, port, attempts, raw_line)'
                               ' VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);', logs)
            connection.commit()
        except psycopg2.Error as e:
            print(e)
            connection.rollback()


def set_location(table_name, ip, country, city):
    with connection.cursor() as cursor:
        try:
            cursor.execute('UPDATE ' + table_name +
                           ' SET country=%s, city=%s WHERE ip=%s', (country, city, ip))
            connection.commit()
        except psycopg2.Error as e:
            print(e)
            connection.rollback()


def count_logs(table_name=TABLE):
    with connection.cursor() as cursor:
        try:
            cursor.execute('SELECT COUNT(*) AS total FROM ' + table_name)
            return cursor.fetchone()['total']
        except psycopg2.Error as e:
            print(e)
            connection.rollback()
            return 0


def ips_to_locate(table_name, n=100):
    ips = []
    with connection.cursor() as cursor:
        try:
            cursor.execute('SELECT ip, SUM(attempts) AS total FROM ' + table_name +
                           " WHERE event_type='Failed password'"
                           ' GROUP BY ip ORDER BY total DESC LIMIT %s', (n,))
            for row in cursor.fetchall():
                ips.append(row['ip'])
            cursor.execute('SELECT DISTINCT ip FROM ' + table_name + " WHERE event_type='Accepted'")
            for row in cursor.fetchall():
                if row['ip'] not in ips:
                    ips.append(row['ip'])
        except psycopg2.Error as e:
            print(e)
            connection.rollback()
    return ips


def load(path='./data'):
    rows = raw.toRows(path)
    clear_table(TABLE)
    logs = []
    for row in rows:
        result = extract_transform.extract_from_row(row)
        if result is not None:
            logs.append(to_tuple(result, row))
    load_all(TABLE, logs)

    locations = geolocation.get_locations(ips_to_locate(TABLE))
    for ip, loc in locations.items():
        set_location(TABLE, ip, loc['country'], loc.get('city'))


def failed_by_country(table_name):
    results = []
    with connection.cursor() as cursor:
        try:
            cursor.execute('SELECT country, SUM(attempts) AS total FROM ' + table_name +
                           " WHERE event_type='Failed password' AND country IS NOT NULL"
                           ' GROUP BY country ORDER BY total DESC')
            results = cursor.fetchall()
        except psycopg2.Error as e:
            print(e)
            connection.rollback()
    return results


def success_by_user(table_name):
    results = []
    with connection.cursor() as cursor:
        try:
            cursor.execute('SELECT username, SUM(attempts) AS total FROM ' + table_name +
                           " WHERE event_type='Accepted' GROUP BY username ORDER BY total DESC")
            results = cursor.fetchall()
        except psycopg2.Error as e:
            print(e)
            connection.rollback()
    return results


def failed_invalid_user(table_name):
    results = []
    with connection.cursor() as cursor:
        try:
            cursor.execute('SELECT username, SUM(attempts) AS total FROM ' + table_name +
                           " WHERE event_type='Invalid user' GROUP BY username ORDER BY total DESC")
            results = cursor.fetchall()
        except psycopg2.Error as e:
            print(e)
            connection.rollback()
    return results