import pymysql
from datetime import datetime
from data_ingestion import raw
from data_processing import extract_transform, geolocation

TABLE = 't_log'
YEAR = 2026  # syslog lines have no year

connection = pymysql.Connection(
    host='localhost',
    port=3306,
    user='root',
    password='',
    cursorclass=pymysql.cursors.DictCursor,
    database='log_analyser'
)


def create_table(name):
    with connection.cursor() as cursor:
        try:
            cursor.execute('CREATE TABLE IF NOT EXISTS ' + name +
                           ' (id int auto_increment primary key not null,'
                           ' log_date datetime not null, hostname varchar(100),'
                           ' service varchar(50), pid int, event_type varchar(50),'
                           ' username varchar(100), ip varchar(45), port int,'
                           ' attempts int not null default 1,'
                           ' country varchar(10), city varchar(100), raw_line text)')
            connection.commit()
        except pymysql.Error as e:
            print(e)
            connection.rollback()


def clear_table(name):
    with connection.cursor() as cursor:
        try:
            cursor.execute('TRUNCATE TABLE ' + name)
            connection.commit()
        except pymysql.Error as e:
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
        except pymysql.Error as e:
            print(e)
            connection.rollback()


def set_location(table_name, ip, country, city):
    with connection.cursor() as cursor:
        try:
            cursor.execute('UPDATE ' + table_name +
                           ' SET country=%s, city=%s WHERE ip=%s', (country, city, ip))
            connection.commit()
        except pymysql.Error as e:
            print(e)
            connection.rollback()


def count_logs(table_name=TABLE):
    with connection.cursor() as cursor:
        try:
            cursor.execute('SELECT COUNT(*) AS total FROM ' + table_name)
            return cursor.fetchone()['total']
        except pymysql.Error as e:
            print(e)
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
        except pymysql.Error as e:
            print(e)
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
        except pymysql.Error as e:
            print(e)
    return results


def success_by_user(table_name):
    results = []
    with connection.cursor() as cursor:
        try:
            cursor.execute('SELECT username, SUM(attempts) AS total FROM ' + table_name +
                           " WHERE event_type='Accepted' GROUP BY username ORDER BY total DESC")
            results = cursor.fetchall()
        except pymysql.Error as e:
            print(e)
    return results


def failed_invalid_user(table_name):
    results = []
    with connection.cursor() as cursor:
        try:
            cursor.execute('SELECT username, SUM(attempts) AS total FROM ' + table_name +
                           " WHERE event_type='Invalid user' GROUP BY username ORDER BY total DESC")
            results = cursor.fetchall()
        except pymysql.Error as e:
            print(e)
    return results