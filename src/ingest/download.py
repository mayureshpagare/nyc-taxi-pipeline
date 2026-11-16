import logging
from pathlib import Path

import requests

log = logging.getLogger(__name__)
CHUNK_SIZE = 1024 * 1024  # 1MB

def build_url(url_template:str, year:int, month:int) -> str:
    # {month:02d} in the template needs an int: 1 -> "01"
    return url_template.format(year=year, month=month)

def landing_file_path(landing_root: Path, dataset:str, year:int, month:int,url:str) -> Path:
    file_name = url.rsplit("/",1)[-1]
    return landing_root / dataset / f"{year:04d}" / f"{month:02d}" / file_name

def download_file(url:str, target:Path, timeout:int) -> int:
    target.parent.mkdir(parents=True,exist_ok=True)
    temp = target.with_name(target.name + ".part")

    try:
        with requests.get(url, stream=True, timeout=timeout) as response:
            response.raise_for_status()
            expected = int(response.headers.get("Content-Length", 0))

            written = 0
            with open(temp,"wb") as f:
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    f.write(chunk)
                    written += len(chunk)

        if expected and written != expected:
            raise IOError(f"Incomplete Download : got {written} of {expected} bytes")

        temp.replace(target)
        return written
    except BaseException:
        temp.unlink(missing_ok=True)
        raise