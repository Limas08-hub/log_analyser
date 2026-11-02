from matplotlib import pyplot as pit
from data_storage import storage


def no_data(title):
    pit.text(0.5, 0.5, 'no data', ha='center')
    pit.title(title)


def graph_top_ips():
    results = storage.top_ips()
    if not results:
        return no_data('Top IPs')
    x = [f"{row['ip']} ({row['country'] or '?'})" for row in results]
    y = [int(row['total']) for row in results]
    pit.barh(x, y, color='green')
    pit.title('Top 10 IPs (failed passwords)')
    pit.xlabel('attempts')
    pit.gca().invert_yaxis()   # biggest on top


def graph_event_types():
    results = storage.get_events_by_type()
    pit.title('Event types')
    if not results:
        return no_data('Event types')
    labels = [f"{row['event_type']} ({int(row['total'])})" for row in results]
    values = [int(row['total']) for row in results]
    pit.pie(values, labels=labels, autopct='%1.0f%%')


def graph_failed_by_user():
    results = storage.failed_by_user()
    pit.title('Failed passwords by user (top 10)')
    if not results:
        return no_data('Failed passwords by user')
    x = [row['username'] for row in results]
    y = [int(row['total']) for row in results]
    pit.bar(x, y, width=0.4, color='red')
    pit.xticks(rotation=45)


def graph_invalid_users():
    results = storage.invalid_users()
    pit.title('Invalid usernames (top 10)')
    if not results:
        return no_data('Invalid usernames')
    x = [row['username'] for row in results]
    y = [int(row['total']) for row in results]
    pit.bar(x, y, width=0.4, color='purple')
    pit.xticks(rotation=45)


def graph_by_hour():
    results = {row['hour']: int(row['total']) for row in storage.get_attempts_by_hour()}
    x = list(range(24))
    y = [results.get(h, 0) for h in x]   # 0 for hours without events
    pit.plot(x, y, 'go-', label='events')
    pit.title('Events per hour')
    pit.xlabel('hour')
    pit.xlim(0, 23)
    pit.legend()


def graph_by_day():
    results = storage.failed_by_day()
    if not results:
        return no_data('Failed passwords per day')
    x = [row['day'].strftime('%b %d') for row in results]
    y = [int(row['total']) for row in results]
    pit.plot(x, y, 'ro-')
    pit.title('Failed passwords per day')
    pit.xticks(rotation=60, fontsize=7)


def graph_by_country():
    results = storage.failed_by_country()
    if not results:
        return no_data('Failed passwords by country')
    x = [row['country'] for row in results]
    y = [int(row['total']) for row in results]
    pit.barh(x, y, color='steelblue')
    pit.title(f'Failed passwords by country (top {storage.TOP_IPS_TO_LOCATE} IPs)')
    pit.xlabel('attempts')
    pit.gca().invert_yaxis()


def graph_summary():
    s = storage.summary()
    lines = [
        f"log lines        : {s['lines_total']}",
        f"failed passwords : {int(s['failed'] or 0)}",
        f"invalid users    : {int(s['invalid'] or 0)}",
        f"successful logins: {int(s['success'] or 0)}",
        f"attacking IPs    : {s['attacking_ips']}",
        '',
        'successful logins:',
    ]
    for row in storage.successful_logins():
        lines.append(f"  {row['log_date']:%b %d %H:%M}  {row['username']}  {row['ip']} ({row['country']})")
    pit.axis('off')
    pit.title('Summary')
    pit.text(0, 1, '\n'.join(lines), va='top', family='monospace', fontsize=9)


def dashboard():
    pit.figure(figsize=(22, 10))
    pit.suptitle('SSH log analyser')

    graphs = [graph_top_ips, graph_event_types, graph_failed_by_user, graph_by_hour,
              graph_by_day, graph_by_country, graph_invalid_users, graph_summary]
    for index, graph in enumerate(graphs, start=1):
        pit.subplot(2, 4, index)   # 2 rows, 4 columns
        graph()

    pit.tight_layout()
    pit.show()
