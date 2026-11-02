import pymysql
from datetime import datetime
from data_processing import extract_transform
from data_processing import geolocation

TABLE = 't_log'
DATABASE = 'log_analyser'
YEAR = 2026            # syslog lines have no year
TOP_IPS_TO_LOCATE = 100  # ipinfo without a token is rate-limited

SETTINGS = dict(host="localhost", port=3306, user='root', password='',
                cursorclass=pymysql.cursors.DictCursor)

_connection = None


def get_connection():
    # connect only when needed (not at import), and create the database if it doesn't exist yet
    global _connection
    if _connection is None:
        try:
            server = pymysql.connect(**SETTINGS)
        except pymysql.err.OperationalError as e:
            raise SystemExit(f'Cannot reach MariaDB on {SETTINGS["host"]}:{SETTINGS["port"]} ({e}). Start the MariaDB server first.')
        cursor = server.cursor()
        cursor.execute('CREATE DATABASE IF NOT EXISTS ' + DATABASE)
        cursor.close()
        server.close()
        _connection = pymysql.connect(database=DATABASE, **SETTINGS)
    return _connection


def _cursor():
    return get_connection().cursor()


def create_table(name=TABLE):
    connection = get_connection()
    with _cursor() as cursor:
        # the table is rebuilt on every load, so running the load twice never doubles the data
        cursor.execute('DROP TABLE IF EXISTS ' + name)
        cursor.execute('CREATE TABLE ' + name +
                       ' ( id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,'
                       ' log_date DATETIME NOT NULL,'
                       ' hostname VARCHAR(100),'
                       ' service VARCHAR(50),'
                       ' pid INT,'
                       ' event_type VARCHAR(50),'
                       ' username VARCHAR(100),'
                       ' ip VARCHAR(45),'
                       ' port INT,'
                       ' attempts INT NOT NULL DEFAULT 1,'   # "message repeated 4 times" = 4 attempts
                       ' country VARCHAR(10),'
                       ' city VARCHAR(100),'
                       ' raw_line TEXT,'
                       ' INDEX (ip), INDEX (event_type)'
                       ')')
    connection.commit()


def count_logs():
    connection = get_connection()
    with _cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS total FROM information_schema.tables "
                       "WHERE table_schema = %s AND table_name = %s", (DATABASE, TABLE))
        if cursor.fetchone()['total'] == 0:
            return 0
        cursor.execute('SELECT COUNT(*) AS total FROM ' + TABLE)
        return cursor.fetchone()['total']


def insert_logs(rows, year=YEAR, batch=5000):
    connection = get_connection()
    values = []
    for row in rows:                      # every row, no limit
        result = extract_transform.extract_from_row(row)
        if result is None:
            continue
        log_date = datetime.strptime(f"{year} {result['month']} {result['day']} {result['time']}", '%Y %b %d %H:%M:%S')
        values.append((log_date, result['hostname'], result['service'], result['pid'], result['event_type'],
                       result['username'], result['ip'], result['port'], result['attempts'], row))

    with _cursor() as cursor:
        for i in range(0, len(values), batch):
            cursor.executemany(
                'INSERT INTO ' + TABLE + ' (log_date, hostname, service, pid, event_type, username, ip, port, attempts, raw_line)'
                ' VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                values[i:i + batch])
    connection.commit()
    return len(values)


def add_locations(n=TOP_IPS_TO_LOCATE):
    # locate the n IPs with the most failed passwords + every IP that logged in successfully
    connection = get_connection()
    with _cursor() as cursor:
        cursor.execute("SELECT ip, SUM(attempts) AS total FROM " + TABLE +
                       " WHERE event_type = 'Failed password' GROUP BY ip ORDER BY total DESC LIMIT %s", (n,))
        ips = [row['ip'] for row in cursor.fetchall()]
        cursor.execute("SELECT DISTINCT ip FROM " + TABLE + " WHERE event_type = 'Accepted'")
        ips += [row['ip'] for row in cursor.fetchall() if row['ip'] not in ips]

    locations = geolocation.get_locations(ips)
    with _cursor() as cursor:
        cursor.executemany('UPDATE ' + TABLE + ' SET country = %s, city = %s WHERE ip = %s',
                           [(loc['country'][:10], (loc.get('city') or None) and loc['city'][:100], ip)
                            for ip, loc in locations.items()])
    connection.commit()
    return len(locations)


def load(path='./data'):
    from data_ingestion import raw
    rows = raw.toRows(path)
    create_table()
    inserted = insert_logs(rows)
    print(f'{len(rows)} lines read, {inserted} rows inserted into {TABLE}')
    located = add_locations()
    print(f'{located} IPs located with ipinfo')


def _query(sql, params=None):
    connection = get_connection()
    with _cursor() as cursor:
        cursor.execute(sql, params)
        return cursor.fetchall()


def top_ips(n=10):
    return _query("SELECT ip, MAX(country) AS country, SUM(attempts) AS total FROM " + TABLE +
                  " WHERE event_type = 'Failed password' GROUP BY ip ORDER BY total DESC LIMIT %s", (n,))

def failed_by_user(n=10):
    return _query("SELECT username, SUM(attempts) AS total FROM " + TABLE +
                  " WHERE event_type = 'Failed password' GROUP BY username ORDER BY total DESC LIMIT %s", (n,))

def invalid_users(n=10):
    return _query("SELECT username, SUM(attempts) AS total FROM " + TABLE +
                  " WHERE event_type = 'Invalid user' GROUP BY username ORDER BY total DESC LIMIT %s", (n,))

def get_events_by_type():
    return _query('SELECT event_type, SUM(attempts) AS total FROM ' + TABLE +
                  ' WHERE event_type IS NOT NULL GROUP BY event_type ORDER BY total DESC')

def get_attempts_by_hour():
    return _query('SELECT HOUR(log_date) AS hour, SUM(attempts) AS total FROM ' + TABLE +
                  ' WHERE event_type IS NOT NULL GROUP BY hour ORDER BY hour')

def failed_by_day():
    return _query("SELECT DATE(log_date) AS day, SUM(attempts) AS total FROM " + TABLE +
                  " WHERE event_type = 'Failed password' GROUP BY day ORDER BY day")

def failed_by_country(n=10):
    return _query("SELECT country, SUM(attempts) AS total FROM " + TABLE +
                  " WHERE event_type = 'Failed password' AND country IS NOT NULL"
                  " GROUP BY country ORDER BY total DESC LIMIT %s", (n,))

def successful_logins():
    return _query("SELECT log_date, username, ip, country FROM " + TABLE +
                  " WHERE event_type = 'Accepted' ORDER BY log_date")

def summary():
    return _query("SELECT COUNT(*) AS lines_total,"
                  " SUM(CASE WHEN event_type = 'Failed password' THEN attempts ELSE 0 END) AS failed,"
                  " SUM(CASE WHEN event_type = 'Invalid user' THEN attempts ELSE 0 END) AS invalid,"
                  " SUM(CASE WHEN event_type = 'Accepted' THEN attempts ELSE 0 END) AS success,"
                  " COUNT(DISTINCT CASE WHEN event_type = 'Failed password' THEN ip END) AS attacking_ips"
                  " FROM " + TABLE)[0]
