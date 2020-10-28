import os
import time

import requests

SESSION = requests.session()
BASE_URL = None

CONTAINER_LIST = []
PRODUCT_LIST = []

FILE_BASE = 'G:\\'
FILE = None

def make_request(url: str) -> dict:
    response = SESSION.get(url)
    while response.status_code != 200:
        print('REQUEST FAILED. RETRYING in 5s...')

        time.sleep(5)
        response = SESSION.get(url)

    return response.json()


def parse_result(data: dict, is_product: bool = False) -> None:
    for item in data['data']['relationships']['children']['data']:
        item_type = item['type']
        item_id = item['id']

        if item_type == 'container':
            traverse_container(item_id)
        elif item_type == 'storefront':
            traverse_storefront(item_id)
        elif item_type == 'game':
            add_product(item_id)
            if not is_product:
                traverse_container(item_id, is_product=True)
        else:
            add_product(item_id)


def traverse_storefront(storefront_id: str) -> None:
    print(f'Found storefront {storefront_id}' + 20 * ' ', end='\r')

    data = make_request(f'{BASE_URL}/storefront/{storefront_id}')

    parse_result(data)


def traverse_container(container_id: str, is_product: bool = False) -> None:
    print(f'---- Found container {container_id}' + 10 * ' ', end='\r')

    global CONTAINER_LIST
    if container_id in CONTAINER_LIST:
        return

    current_offset = 0
    page_size = 250

    data = make_request(f'{BASE_URL}/container/{container_id}?size={page_size}&start={current_offset}')
    children = data['data']['relationships']['children']['data']

    while len(children) > 0:
        parse_result(data, is_product)

        current_offset += page_size
        data = make_request(f'{BASE_URL}/container/{container_id}?size=100&start={current_offset}')
        children = data['data']['relationships']['children']['data']

    CONTAINER_LIST.append(container_id)


def add_product(product_id: str) -> None:
    print(f'-------- Found product {product_id}', end='\r')

    global PRODUCT_LIST, FILE
    if product_id not in PRODUCT_LIST:
        PRODUCT_LIST.append(product_id)
        FILE.write(product_id + '\n')


def fetch_product(product_id: str) -> None:
    data = make_request(f'{BASE_URL}/resolve/{product_id}')


if __name__ == "__main__":
    locale = input('Locale (format: en-gb): ')
    language_code = locale[:2]
    country_code = locale[-2:]

    BASE_URL = f'https://store.playstation.com/valkyrie-api/{language_code}/{country_code}/999'
    FILE = open(os.path.join(FILE_BASE, f'{locale}.txt'), 'w')

    session_data = SESSION.post(
        url='https://store.playstation.com/kamaji/api/valkyrie_storefront/00_09_000/user/session',
        data={
            'country_code': country_code.upper(),
            'language_code': language_code,
        }
    ).json()

    stores_data = SESSION.get(url=session_data['data']['sessionUrl'] + 'user/stores').json()
    base_storefront = stores_data['data']['base_url'].split('/')[-1]

    traverse_storefront(base_storefront)

    FILE.close()
