import sys
from data_storage.storage import connection, TABLE, create_table, count_logs, load
from data_serving import dashboard

if __name__ == '__main__':
    with connection:
        create_table(TABLE)
        # première exécution (table vide) ou "python main.py reload"
        if count_logs() == 0 or 'reload' in sys.argv:
            load('./data')
        dashboard.dashboard()