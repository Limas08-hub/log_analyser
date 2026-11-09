import os
import requests
from requests import Response

# optional: set IPINFO_TOKEN in the terminal to lift ipinfo's free rate limit
TOKEN = os.environ.get('IPINFO_TOKEN')


def get_location(ip):
    params = {'token': TOKEN} if TOKEN else None
    try:
        response: Response = requests.get("https://ipinfo.io/" + ip + "/json", params=params, timeout=10)
    except requests.RequestException:
        return {'ip': ip, 'country': 'Unknown', 'city': None}
    if response.status_code == 200:   # 200 means the request went through
        data = response.json()
        if data.get('bogon'):         # private address (10.x, 127.x ...) -> no country
            data['country'] = 'Private'
        data.setdefault('country', 'Unknown')
        data.setdefault('city', None)
        return data
    return {'ip': ip, 'country': 'Unknown', 'city': None}


def get_locations(ips):
    locations = {}
    for ip in ips:
        locations[ip] = get_location(ip)
    return locations


if __name__ == '__main__':
    print(get_location('109.199.110.135'))