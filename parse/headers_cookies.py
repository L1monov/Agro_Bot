import requests

def get_auth_token():
    url = "https://pub.fsa.gov.ru/login"
    headers = {
        "Origin": "https://pub.fsa.gov.ru",
        "Content-Type": "application/json"
    }
    data = {
        "username": "anonymous",
        "password": "hrgesf7HDR67Bd"
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        auth_header = response.headers.get("Authorization")
        print("Bearer token:", auth_header)
        return auth_header
    else:
        print("HTTP request failed with status code:", response.status_code)
        print("Response:", response.text)
        return None


headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'ru,en;q=0.9',
        'Authorization': get_auth_token(),
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json',
        # 'Cookie': '_ym_uid=1714423697486130793; _ym_d=1745056371; PHPSESSID=GYulIUKK2UiEsf06nBBvlfRNfi6hmaRQ; BITRIX_CONVERSION_CONTEXT_s1=%7B%22ID%22%3A1%2C%22EXPIRE%22%3A1746392340%2C%22UNIQUE%22%3A%5B%22conversion_visit_day%22%5D%7D; session-cookie=183c5908ded3da6b745f292e80267f93f43e7d58b3929b7a299ce628ff4183e98fde29158374de378577211da42f500a; _ym_isad=1',
        'Origin': 'https://pub.fsa.gov.ru',
        'Pragma': 'no-cache',
        'Referer': 'https://pub.fsa.gov.ru/rds/declaration',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 YaBrowser/25.2.0.0 Safari/537.36',
        'X-Ajax-Token': 'bc529d9861f0ccfbf9843f9bc9eebf0982b275b754eb45c603b22503a2ae2cd0',
        'X-Requested-With': 'XMLHttpRequest',
        'lkId': '',
        'orgId': '',
        'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "YaBrowser";v="25.2", "Yowser";v="2.5"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
cookies = {
    '_ym_uid': '1714423697486130793',
    '_ym_d': '1745056371',
    'PHPSESSID': 'GYulIUKK2UiEsf06nBBvlfRNfi6hmaRQ',
    'BITRIX_CONVERSION_CONTEXT_s1': '%7B%22ID%22%3A1%2C%22EXPIRE%22%3A1746392340%2C%22UNIQUE%22%3A%5B%22conversion_visit_day%22%5D%7D',
    'session-cookie': '183c5908ded3da6b745f292e80267f93f43e7d58b3929b7a299ce628ff4183e98fde29158374de378577211da42f500a',
    '_ym_isad': '1',
}