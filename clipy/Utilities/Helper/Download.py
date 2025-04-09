import requests
import math 
from tqdm import tqdm 

cf_link = "https://files.quettacompute.com/"

def download_cf(remote_name, local_name):
    url = cf_link + remote_name
    head = requests.head(url)
    file_size = int(head.headers.get('Content-Length', 0))  
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(local_name, 'wb') as f:
        chunk_size = 8192
        pbar = tqdm(total=file_size,unit="B",unit_scale=True)
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
            pbar.update(len(chunk))


