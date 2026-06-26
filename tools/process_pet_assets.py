from pathlib import Path
import shutil

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "pets" / "pet-growth-sheet-source.png"
OUT_DIR = ROOT / "assets" / "pets"
SIZE = 512

SOURCE_STAGES = [
    ("egg", "pet-egg.png"),
    ("cracked", "pet-cracked.png"),
    ("hatched", "pet-hatched.png"),
    ("star", "pet-star.png"),
]

GROWTH_STAGES = [
    ("stage-01", "egg", 0.82, 0.92, 0),
    ("stage-02", "egg", 0.88, 1.02, 1),
    ("stage-03", "cracked", 0.9, 0.98, 1),
    ("stage-04", "cracked", 0.94, 1.06, 2),
    ("stage-05", "cracked", 0.98, 1.1, 2),
    ("stage-06", "hatched", 0.82, 0.96, 1),
    ("stage-07", "hatched", 0.88, 1.0, 1),
    ("stage-08", "hatched", 0.92, 1.04, 2),
    ("stage-09", "hatched", 0.96, 1.08, 2),
    ("stage-10", "hatched", 1.0, 1.12, 3),
    ("stage-11", "star", 0.82, 0.98, 2),
    ("stage-12", "star", 0.86, 1.02, 2),
    ("stage-13", "star", 0.9, 1.06, 3),
    ("stage-14", "star", 0.94, 1.1, 3),
    ("stage-15", "star", 0.98, 1.14, 4),
    ("stage-16", "star", 1.02, 1.18, 4),
    ("stage-17", "star", 1.06, 1.22, 5),
    ("stage-18", "star", 1.1, 1.25, 5),
    ("stage-19", "star", 1.14, 1.28, 6),
    ("stage-20", "star", 1.18, 1.32, 7),
]

SKINS = {
    "default": {"tint": (255, 255, 255), "strength": 0.0, "saturation": 1.0},
    "aqua": {"tint": (0, 210, 255), "strength": 0.28, "saturation": 1.18},
    "ember": {"tint": (255, 95, 35), "strength": 0.3, "saturation": 1.22},
    "blossom": {"tint": (255, 118, 188), "strength": 0.26, "saturation": 1.16},
    "cosmic": {"tint": (126, 87, 255), "strength": 0.34, "saturation": 1.28},
}


def remove_green_background(image):
    image = image.convert("RGBA")
    pixels = image.load()
    width, height = image.size

    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            is_green_screen = g > 150 and r < 120 and b < 130 and g > r * 1.35 and g > b * 1.35
            if is_green_screen:
                pixels[x, y] = (r, g, b, 0)
            elif g > 120 and r < 140 and b < 150:
                pixels[x, y] = (r, min(g, 120), b, a)

    return image


def crop_subject(image):
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if not bbox:
        return image

    left, top, right, bottom = bbox
    pad = 28
    return image.crop((
        max(left - pad, 0),
        max(top - pad, 0),
        min(right + pad, image.width),
        min(bottom + pad, image.height),
    ))


def keep_largest_alpha_component(image, threshold=12):
    image = image.convert("RGBA")
    alpha = image.getchannel("A")
    width, height = image.size
    alpha_pixels = alpha.load()
    visited = bytearray(width * height)
    components = []

    for start_y in range(height):
        for start_x in range(width):
            index = start_y * width + start_x
            if visited[index] or alpha_pixels[start_x, start_y] <= threshold:
                continue

            stack = [(start_x, start_y)]
            visited[index] = 1
            pixels = []

            while stack:
                x, y = stack.pop()
                pixels.append((x, y))
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if nx < 0 or ny < 0 or nx >= width or ny >= height:
                        continue
                    nindex = ny * width + nx
                    if visited[nindex] or alpha_pixels[nx, ny] <= threshold:
                        continue
                    visited[nindex] = 1
                    stack.append((nx, ny))

            components.append(pixels)

    if not components:
        return image

    keep = set(max(components, key=len))
    pixels = image.load()
    for y in range(height):
        for x in range(width):
            if alpha_pixels[x, y] > threshold and (x, y) not in keep:
                r, g, b, _ = pixels[x, y]
                pixels[x, y] = (r, g, b, 0)

    return image


def fit_square(image, size=SIZE, margin=48):
    image = image.copy()
    image.thumbnail((size - margin, size - margin), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.alpha_composite(image, ((size - image.width) // 2, (size - image.height) // 2))
    return canvas


def make_source_stage_images():
    sheet = Image.open(SOURCE)
    stage_width = sheet.width // len(SOURCE_STAGES)
    source_images = {}

    for index, (stage_key, filename) in enumerate(SOURCE_STAGES):
        left = index * stage_width
        right = sheet.width if index == len(SOURCE_STAGES) - 1 else (index + 1) * stage_width
        tile = sheet.crop((left, 0, right, sheet.height))
        tile = remove_green_background(tile)
        tile = keep_largest_alpha_component(tile)
        tile = crop_subject(tile)
        tile = fit_square(tile)
        tile.save(OUT_DIR / filename)
        source_images[stage_key] = tile

    return source_images


def scale_on_canvas(image, scale):
    new_size = max(1, int(SIZE * scale))
    scaled = image.resize((new_size, new_size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    canvas.alpha_composite(scaled, ((SIZE - new_size) // 2, (SIZE - new_size) // 2))
    return canvas


def add_glow(image, strength):
    if strength <= 0:
        return image

    alpha = image.getchannel("A")
    glow = Image.new("RGBA", image.size, (255, 210, 85, 0))
    glow_alpha = alpha.filter(ImageFilter.GaussianBlur(8 + strength))
    glow_alpha = glow_alpha.point(lambda value: int(value * min(0.28, 0.04 * strength)))
    glow.putalpha(glow_alpha)
    result = Image.alpha_composite(glow, image)
    return result


def add_stage_marks(image, count):
    if count <= 0:
        return image

    result = image.copy()
    draw = ImageDraw.Draw(result)
    positions = [
        (372, 112), (112, 132), (404, 242), (98, 274),
        (342, 374), (178, 392), (256, 84),
    ]
    for index in range(min(count, len(positions))):
        x, y = positions[index]
        radius = 8 + (index % 3)
        color = (255, 218, 80, 230)
        draw.polygon([
            (x, y - radius),
            (x + radius // 2, y - radius // 2),
            (x + radius, y),
            (x + radius // 2, y + radius // 2),
            (x, y + radius),
            (x - radius // 2, y + radius // 2),
            (x - radius, y),
            (x - radius // 2, y - radius // 2),
        ], fill=color)
    return result


def make_growth_stage(base_image, scale, brightness, marks):
    image = scale_on_canvas(base_image, scale)
    alpha = image.getchannel("A")
    image = ImageEnhance.Brightness(image.convert("RGB")).enhance(brightness).convert("RGBA")
    image.putalpha(alpha)
    image = add_glow(image, marks)
    image = add_stage_marks(image, marks)
    return image


def apply_skin(image, skin):
    settings = SKINS[skin]
    result = image.copy().convert("RGBA")

    if settings["strength"] > 0:
        tint = Image.new("RGBA", result.size, (*settings["tint"], 255))
        alpha = result.getchannel("A")
        result = Image.blend(result, tint, settings["strength"])
        result.putalpha(alpha)

    if settings["saturation"] != 1.0:
        alpha = result.getchannel("A")
        result = ImageEnhance.Color(result.convert("RGB")).enhance(settings["saturation"]).convert("RGBA")
        result.putalpha(alpha)

    return result


def make_animation_frame(image, frame):
    if frame == 1:
        return image.copy()
    elif frame == 2:
        transformed = image.resize((500, 520), Image.Resampling.LANCZOS).rotate(-2, resample=Image.Resampling.BICUBIC, expand=True)
        y_offset = -10
    else:
        transformed = image.resize((520, 500), Image.Resampling.LANCZOS).rotate(2, resample=Image.Resampling.BICUBIC, expand=True)
        y_offset = 10

    large_canvas = Image.new("RGBA", (SIZE * 2, SIZE * 2), (0, 0, 0, 0))
    large_canvas.alpha_composite(
        transformed,
        ((large_canvas.width - transformed.width) // 2, (large_canvas.height - transformed.height) // 2 + y_offset),
    )
    left = (large_canvas.width - SIZE) // 2
    top = (large_canvas.height - SIZE) // 2
    return large_canvas.crop((left, top, left + SIZE, top + SIZE))


def write_skin_frames(stage_key, base_image):
    for skin in SKINS:
        skinned = apply_skin(base_image, skin)
        stage_dir = OUT_DIR / "skins" / skin / stage_key
        stage_dir.mkdir(parents=True, exist_ok=True)
        for frame in range(1, 4):
            make_animation_frame(skinned, frame).save(stage_dir / f"frame-{frame}.png")


def main():
    skins_dir = OUT_DIR / "skins"
    if skins_dir.exists():
        shutil.rmtree(skins_dir)

    source_images = make_source_stage_images()
    for stage_key, source_key, scale, brightness, marks in GROWTH_STAGES:
        stage_image = make_growth_stage(source_images[source_key], scale, brightness, marks)
        stage_image.save(OUT_DIR / f"{stage_key}.png")
        write_skin_frames(stage_key, stage_image)


if __name__ == "__main__":
    main()
