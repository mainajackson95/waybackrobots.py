import requests
import re
import sys
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def robots(host):
    try:
        url = f'https://web.archive.org/cdx/search/cdx?url={host}/robots.txt&output=json&fl=timestamp,original&filter=statuscode:200&collapse=digest'
        logging.info(f'Fetching robots.txt snapshots from {url}')
        response = requests.get(url)
        response.raise_for_status()
        results = response.json()
        if len(results) == 0:
            logging.warning('No robots.txt snapshots found.')
            return []
        # Remove the header row
        results.pop(0)
        return results
    except requests.exceptions.RequestException as e:
        logging.error(f'An error occurred while fetching robots.txt snapshots: {e}')
        return []

def getpaths(snapshot):
    timestamp, original_url = snapshot
    url = f'https://web.archive.org/web/{timestamp}/{original_url}'
    try:
        logging.info(f'Fetching {url}')
        response = requests.get(url)
        response.raise_for_status()
        robotstext = response.text
        if 'Disallow:' in robotstext:
            # Extract paths from Disallow directives
            paths = re.findall(r'Disallow:\s*(.+)', robotstext, re.IGNORECASE)
            logging.info(f'Found {len(paths)} paths in {url}')
            return paths
        else:
            logging.info(f'No Disallow directives found in {url}')
            return []
    except requests.exceptions.RequestException as e:
        logging.error(f'An error occurred while fetching {url}: {e}')
        return []

if __name__ == '__main__':
    if len(sys.argv) < 2:
        logging.error('Usage:\n\tpython3 waybackrobots.py <domain-name>')
        sys.exit(1)

    host = sys.argv[1]
    snapshots = robots(host)
    logging.info(f'Found {len(snapshots)} unique snapshots')
    if len(snapshots) == 0:
        logging.info('No snapshots to process. Exiting.')
        sys.exit(0)
    logging.info('Processing snapshots...')
    unique_paths = set()
    for snapshot in snapshots:
        time.sleep(1)  # Delay to avoid rate limiting
        paths = getpaths(snapshot)
        if paths:
            unique_paths.update(paths)
    filename = f'{host}-robots.txt'
    with open(filename, 'w') as f:
        f.write('\n'.join(unique_paths))
    logging.info(f'[*] Saved {len(unique_paths)} unique paths to {filename}')
