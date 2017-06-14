import asyncio
import json

import aiohttp
import async_timeout

from parse import parse

errors = {}
data = []

try:
    with open('data.json', 'r') as infile:
        data = json.load(infile)['nodes']
except:
    pass

existing = set(x['id'] for x in data)

sem = asyncio.BoundedSemaphore(5)
loop = asyncio.get_event_loop()

id_min = 1
id_max = 216676


async def fetch(session, url):
    with async_timeout.timeout(10):
        async with session.get(url) as response:
            print('fetching {}'.format(url))
            return await response.text()


async def fetch_by_id(session, mgp_id):
    async with sem:
        url = 'https://genealogy.math.ndsu.nodak.edu/id.php?id={}'.format(mgp_id)
        raw_html = await fetch(session, url)

        if 'You have specified an ID that does not exist in the database.' in raw_html:
            print('bad id={}'.format(mgp_id))
            return

        failed = False
        info_dict = {}

        try:
            info_dict = parse(mgp_id, raw_html)
        except Exception as e:
            print('Failed to parse id={}'.format(mgp_id))
            failed = e
        finally:
            if failed:
                errors[mgp_id] = failed
            else:
                data.append(info_dict)


async def main():
    async with aiohttp.ClientSession(loop=loop) as session:
        await asyncio.wait([
            fetch_by_id(session, i) for i in range(id_min, 1 + id_max) if i not in existing
        ])


loop.run_until_complete(main())

with open('errors.txt', 'w') as outfile:
    for i, error in errors.items():
        outfile.write('{},{}\n'.format(i, error))

with open('data.json', 'w') as outfile:
    json.dump({'nodes': data}, outfile)