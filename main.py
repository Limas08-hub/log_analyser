import sys
from data_storage import storage
from data_serving import dashboard

if __name__ == '__main__':
    # first run (empty table) or "uv run main.py reload": read ALL the logs -> MySQL -> ipinfo
    if storage.count_logs() == 0 or 'reload' in sys.argv:
        storage.load('./data')
    dashboard.dashboard()
