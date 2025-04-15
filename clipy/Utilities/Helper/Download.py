import requests
import math 
from tqdm import tqdm 

#this file is used to download various files used by this script
#right now only the model weights are hosted at the link below 
#they are all hosted on my personal cloudflare account and can be downloaded really fast 
#I think they are 150MB in total and get downloaded when they are needed by the pipeline
#🎉 zero egress fees on cloudflare

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


