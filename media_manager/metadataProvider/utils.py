from uuid import UUID

from PIL import Image
import requests


def get_year_from_date(first_air_date: str | None) -> int | None:
    if first_air_date:
        return int(first_air_date.split("-")[0])
    else:
        return None


def download_poster_image(storage_path=None, poster_url=None, id: UUID = None) -> bool:
    res = requests.get(poster_url, stream=True)
    if res.status_code == 200:
        image_file_path = storage_path.joinpath(str(id))
        with open(str(image_file_path) + ".jpg", "wb") as f:
            f.write(res.content)

        original_image = Image.open(str(image_file_path) + ".jpg")
        original_image.save(str(image_file_path) + ".avif", quality=50)
        original_image.save(str(image_file_path) + ".webp", quality=50)
        return True
    else:
        return False
