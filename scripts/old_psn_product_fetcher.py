import os
import time
import argparse
import sys
import pathlib

import requests
import arrow
'''

made by `Landcross#5410`

modified slightly by mgrandi

'''

SESSION = requests.session()
BASE_URL = None

CONTAINER_LIST = []
PRODUCT_LIST = []

FILE_BASE = '.'

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
        elif item_type in ['game', 'film', 'tv-series', 'tv-season']:
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


def main(args):

    language_code = args.region_language
    country_code = args.region_country

    start_time = arrow.utcnow()

    print("language code: `{}`, country code: `{}`".format(language_code, country_code))
    print("starting at `{}`".format(start_time))

    global BASE_URL, FILE, FILE_BASE

    FILE_BASE = str(args.output_file_directory)
    BASE_URL = f'https://store.playstation.com/valkyrie-api/{language_code}/{country_code}/999'
    FILE = open(os.path.join(FILE_BASE, f'{language_code}-{country_code}.txt'), 'w')

    tmpres = SESSION.post(
        url='https://store.playstation.com/kamaji/api/valkyrie_storefront/00_09_000/user/session',
        data={
            'country_code': country_code.upper(),
            'language_code': language_code,
        }
    )

    session_data = tmpres.json()

    stores_data = SESSION.get(url=session_data['data']['sessionUrl'] + 'user/stores').json()
    base_storefront = stores_data['data']['base_url'].split('/')[-1]

    traverse_storefront(base_storefront)

    FILE.close()


    end_time = arrow.utcnow()
    print("finished at `{}`".format(end_time))

    elapsed_time = end_time - start_time
    print("elapsed time: `{}`".format(elapsed_time))


def isDirectoryType(filePath):
    ''' see if the file path given to us by argparse is a directory
    @param filePath - the filepath we get from argparse
    @return the filepath as a pathlib.Path() if it is a directory, else we raise a ArgumentTypeError'''

    path_maybe = pathlib.Path(filePath)
    path_resolved = None

    # try and resolve the path
    try:
        path_resolved = path_maybe.resolve(strict=True).expanduser()

    except Exception as e:
        raise argparse.ArgumentTypeError("Failed to parse `{}` as a path: `{}`".format(filePath, e))

    # double check to see if its a file
    if not path_resolved.is_dir():
        raise argparse.ArgumentTypeError("The path `{}` is not a directory!".format(path_resolved))

    return path_resolved


if __name__ == "__main__":

    parser = argparse.ArgumentParser("old_psn_product_fetcher")

    parser.add_argument("region_language", help="the region language, aka the `en` in `en-US`")
    parser.add_argument("region_country", help="the region country, aka the `US` in `en-US`")
    parser.add_argument("--output_file_directory", type=isDirectoryType, default=".",
        help="where to write the resulting file to, defaults to current directory")


    parsed_args = parser.parse_args()


    try:

        main(parsed_args)

    except Exception as e:
        print("something went wrong!: {}".format(e))
        sys.exit(1)

    print("done!")

