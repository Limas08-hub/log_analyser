import re #import re to extract
#\s: espace

# "May 24 00:04:36 ns sshd[1350968]: Failed password for root from 45.148.10.147 port 8868 ssh2"
#  month day  time    host service pid   message
pattern = re.compile(r'^(\w{3})\s+(\d{1,2})\s+(\d{2}:\d{2}:\d{2})\s+(\S+)\s+([^\s\[:]+)(?:\[(\d+)\])?:\s(.*)$')

# event types we look for in the sshd messages
failed_pattern = re.compile(r'Failed \w+ for (?:invalid user )?(\S*) from (\d+\.\d+\.\d+\.\d+) port (\d+)')
accepted_pattern = re.compile(r'Accepted \w+ for (\S+) from (\d+\.\d+\.\d+\.\d+) port (\d+)')
invalid_pattern = re.compile(r'Invalid user (\S*)\s+from (\d+\.\d+\.\d+\.\d+)(?: port (\d+))?')
# "message repeated 4 times: [ Failed password ...]" = 4 attempts in one line
repeated_pattern = re.compile(r'message repeated (\d+) times')


def extract_from_row(row):
    match = re.search(pattern, row)
    if not match:
        return None
    month, day, time, hostname, service, pid, message = match.groups()

    result = {
        'month': month,
        'day': int(day),
        'time': time,
        'hostname': hostname,
        'service': service,
        'pid': int(pid) if pid else None,
        'event_type': None,
        'username': None,
        'ip': None,
        'port': None,
        'attempts': 1,
        'message': message,
    }

    for event_type, event_pattern in (('Failed password', failed_pattern),
                                      ('Accepted', accepted_pattern),
                                      ('Invalid user', invalid_pattern)):
        found = re.search(event_pattern, message)
        if found:
            result['event_type'] = event_type
            result['username'] = found.group(1) or '(empty)'
            result['ip'] = found.group(2)
            result['port'] = int(found.group(3)) if found.group(3) else None
            break

    repeated = re.search(repeated_pattern, message)
    if repeated and result['event_type']:
        result['attempts'] = int(repeated.group(1))

    return result
