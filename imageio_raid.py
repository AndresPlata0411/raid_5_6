"""Conversion helpers between RGB images and RAID byte streams."""
from io import BytesIO

from PIL import Image, ImageOps


def load_image(source, max_side=900):
    """Open an image, apply EXIF orientation, resize if needed, and return RGB + metadata."""
    image = ImageOps.exif_transpose(Image.open(source)).convert("RGB")
    original_size = image.size
    image.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    return image, original_size


def image_bytes(image):
    image = image.convert("RGB")
    return image.tobytes(), image.width, image.height


def bytes_image(data, width, height):
    expected = width * height * 3
    if len(data) != expected:
        raise ValueError(f"Se esperaban {expected} bytes RGB y llegaron {len(data)}")
    return Image.frombytes("RGB", (width, height), data)


def png_base64(image):
    import base64
    buffer = BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return base64.b64encode(buffer.getvalue()).decode("ascii")
