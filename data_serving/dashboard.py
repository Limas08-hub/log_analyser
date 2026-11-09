from matplotlib import pyplot as pit
from data_storage.storage import failed_by_country, success_by_user, failed_invalid_user

TABLE = 't_log'
TOP = 10


def draw(results, key, title, color, n=TOP):
    results = results[:n]                      # keep only the top n
    pit.title(title, fontsize=12, fontweight='bold')
    if not results:
        pit.text(0.5, 0.5, 'no data', ha='center')
        pit.axis('off')
        return
    x = []
    y = []
    for row in results:
        x.append(str(row[key]))
        y.append(int(row['total']))

    pit.barh(x, y, height=0.6, color=color)
    pit.gca().invert_yaxis()                   # biggest bar on top
    for i in range(len(y)):
        pit.text(y[i], i, ' ' + str(y[i]), va='center', fontsize=9)   # value at the end of the bar
    pit.xlim(0, max(y) * 1.15)                 # room for the numbers
    pit.xlabel('attempts')
    pit.grid(axis='x', alpha=0.3)
    pit.gca().spines['top'].set_visible(False)
    pit.gca().spines['right'].set_visible(False)


def draw_donut(results, key, title, n=TOP):
    results = results[:n]                      # keep only the top n
    pit.title(title, fontsize=12, fontweight='bold')
    if not results:
        pit.text(0.5, 0.5, 'no data', ha='center')
        pit.axis('off')
        return
    x = []
    y = []
    for row in results:
        x.append(str(row[key]))
        y.append(int(row['total']))

    pit.pie(y, labels=x, startangle=90, wedgeprops=dict(width=0.4, edgecolor='white'))
    pit.text(0, 0, str(sum(y)) + '\nattempts', ha='center', va='center', fontweight='bold')   # total in the center


def graph_failed_by_country():
    draw(failed_by_country(TABLE), 'country', 'Failed attempts by country (top 10)', '#1abc9c')
    pit.show()


def graph_success_by_user():
    draw(success_by_user(TABLE), 'username', 'Successful attempts by user', '#f39c12')
    pit.show()


def graph_failed_invalid_user():
    draw_donut(failed_invalid_user(TABLE), 'username', 'Failed attempts with invalid user (top 10)')
    pit.show()


def dashboard():
    pit.figure(figsize=(18, 6))
    pit.suptitle('SSH log analyser', fontsize=16, fontweight='bold')

    pit.subplot(1, 3, 1)
    draw(failed_by_country(TABLE), 'country', 'Failed attempts by country (top 10)', '#1abc9c')

    pit.subplot(1, 3, 2)
    draw(success_by_user(TABLE), 'username', 'Successful attempts by user', '#f39c12')

    pit.subplot(1, 3, 3)
    draw_donut(failed_invalid_user(TABLE), 'username', 'Failed attempts with invalid user (top 10)')

    pit.tight_layout()
    pit.show()


if __name__ == '__main__':
    dashboard()