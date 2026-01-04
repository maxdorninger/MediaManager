from pathlib import Path
from uuid import UUID

from PIL import Image
import requests


def get_year_from_date(first_air_date: str | None) -> int | None:
    if first_air_date:
        return int(first_air_date.split("-")[0])
    else:
        return None


def download_poster_image(storage_path: Path, poster_url: str, id: UUID) -> bool:
    res = requests.get(poster_url, stream=True)

    if res.status_code == 200:
        image_file_path = storage_path.joinpath(str(id)).with_suffix("jpg")
        image_file_path.write_bytes(res.content)

        original_image = Image.open(image_file_path)
        original_image.save(image_file_path.with_suffix(".avif"), quality=50)
        original_image.save(image_file_path.with_suffix(".webp"), quality=50)
        return True
    else:
        return False
