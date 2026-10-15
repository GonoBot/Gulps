import json
import math
import os
import re
import urllib.parse
import urllib.request

IMAGE_DIR = os.path.expanduser("~/storage/downloads/Images")
os.makedirs(IMAGE_DIR, exist_ok=True)

# Keep filenames conservative because Android/Linux limits filenames by bytes,
# and Unicode characters can use multiple UTF-8 bytes.
MAX_FILENAME_LENGTH = 60

IMAGE_EXTS = {
    "jpg", "jpeg", "png", "webp",
    "gif", "avif", "bmp", "tiff"
}

VIDEO_EXTS = {
    "mp4", "webm", "mkv", "mov",
    "m4v", "avi", "flv"
}


def clean_filename(name):
    name = str(name or "image")

    # Remove characters that are invalid in Linux/Android filenames.
    name = re.sub(r'[\\/:*?"<>|]', "", name)
    name = re.sub(r'[\x00-\x1f\x7f]', "", name)

    # Collapse whitespace.
    name = re.sub(r'\s+', " ", name).strip()

    return name or "image"


def make_filename(title, extension="jpg", number=None):
    title = clean_filename(title)

    extension = clean_filename(extension or "jpg").lower()

    if extension == "jpeg":
        extension = "jpg"

    if extension not in IMAGE_EXTS:
        extension = "jpg"

    prefix = f"{number} " if number is not None else ""

    # Leave room for prefix + dot + extension.
    max_title = (
        MAX_FILENAME_LENGTH
        - len(prefix)
        - len(extension)
        - 1
    )

    title = title[:max(1, max_title)].rstrip()

    if not title:
        title = "image"

    return f"{title}{prefix}.{extension}"


def _extension_from_url(url, default="jpg"):
    if not url:
        return default

    try:
        path = urllib.parse.urlparse(url).path.lower()
    except Exception:
        return default

    match = re.search(r'\.([a-z0-9]{2,5})$', path)

    if match:
        ext = match.group(1)

        if ext in IMAGE_EXTS:
            return "jpg" if ext == "jpeg" else ext

    return default


def _extension_from_mime(mime):
    if not mime:
        return None

    mime = str(mime).lower().split(";")[0].strip()

    mapping = {
        "image/jpeg": "jpg",
        "image/jpg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
        "image/gif": "gif",
        "image/avif": "avif",
        "image/bmp": "bmp",
        "image/tiff": "tiff",
    }

    return mapping.get(mime)


def _looks_like_image_url(url):
    if not url:
        return False

    url = str(url).lower()

    # Normal file extension.
    if _extension_from_url(url, None):
        return True

    # Common image CDN patterns where the extension is hidden.
    image_patterns = (
        "format=jpg",
        "format=jpeg",
        "format=png",
        "format=webp",
        "fm=jpg",
        "fm=jpeg",
        "fm=png",
        "fm=webp",
        "type=image",
        "image/",
    )

    return any(pattern in url for pattern in image_patterns)


def _get_thumbnail_url(entry):
    """
    Find the best image URL exposed by yt-dlp.

    Some extractors expose the actual image through `url`.
    Others expose it through `thumbnail` or `thumbnails`.
    """

    if not entry:
        return None

    # Direct media URL.
    url = entry.get("url")

    if url and _looks_like_image_url(url):
        return url

    # Explicit thumbnail.
    thumbnail = entry.get("thumbnail")

    if thumbnail and _looks_like_image_url(thumbnail):
        return thumbnail

    # Multiple thumbnails.
    thumbnails = entry.get("thumbnails") or []

    candidates = []

    for thumb in thumbnails:
        if not isinstance(thumb, dict):
            continue

        thumb_url = thumb.get("url")

        if not thumb_url:
            continue

        if _looks_like_image_url(thumb_url):
            candidates.append(thumb)

    if candidates:
        # Prefer the largest thumbnail.
        candidates.sort(
            key=lambda x: (
                x.get("width") or 0,
                x.get("height") or 0,
            ),
            reverse=True,
        )

        return candidates[0].get("url")

    return None


def _entry_has_video(entry):
    if not entry:
        return False

    ext = str(entry.get("ext") or "").lower()

    if ext in VIDEO_EXTS:
        return True

    vcodec = str(entry.get("vcodec") or "").lower()

    if vcodec and vcodec != "none":
        return True

    formats = entry.get("formats") or []

    for fmt in formats:
        if not isinstance(fmt, dict):
            continue

        fmt_vcodec = str(fmt.get("vcodec") or "").lower()
        fmt_ext = str(fmt.get("ext") or "").lower()

        if fmt_vcodec and fmt_vcodec != "none":
            return True

        if fmt_ext in VIDEO_EXTS:
            return True

    return False


def _entry_has_audio(entry):
    if not entry:
        return False

    acodec = str(entry.get("acodec") or "").lower()

    return bool(acodec and acodec != "none")


def _entry_is_image(entry):
    """
    Determine whether a yt-dlp entry represents an image.

    We deliberately avoid treating video entries as images just because
    they contain thumbnails.
    """

    if not entry:
        return False

    ext = str(entry.get("ext") or "").lower()

    if ext in IMAGE_EXTS:
        return True

    mime = (
        entry.get("mime_type")
        or entry.get("mime")
        or entry.get("http_headers", {}).get("Content-Type")
    )

    if _extension_from_mime(mime):
        return True

    url = entry.get("url")

    if url and _looks_like_image_url(url):
        return True

    # If yt-dlp says this is definitely a video, don't classify its
    # thumbnail as the downloadable image.
    if _entry_has_video(entry):
        return False

    # A pure image entry can sometimes have no useful `ext` or MIME,
    # especially on social-media CDNs.
    thumbnail = _get_thumbnail_url(entry)

    if thumbnail and not _entry_has_audio(entry):
        return True

    return False


def get_image_entries(entries):
    """
    Split yt-dlp extracted entries into images and videos.

    This is intentionally generic so image posts from Instagram,
    X/Twitter, Pinterest, Reddit, etc. can be detected without
    maintaining a separate image module for every website.
    """

    images = []
    videos = []

    for entry in entries or []:
        if not entry:
            continue

        if _entry_is_image(entry):
            # Make a copy so we don't modify yt-dlp's original data.
            image = dict(entry)

            source = _get_thumbnail_url(image)

            if source:
                image["_image_url"] = source

                if not image.get("ext"):
                    image["ext"] = (
                        _extension_from_url(source)
                        or _extension_from_mime(image.get("mime_type"))
                        or "jpg"
                    )

            images.append(image)

        elif _entry_has_video(entry):
            videos.append(entry)

    return images, videos


def get_media_entries(url):
    """
    Extract media through yt-dlp.

    Returns:
        []    = extraction worked but no entries were returned
        None  = yt-dlp could not inspect the URL
        list  = extracted entries
    """

    import yt_dlp

    options = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": False,
        "ignore_no_formats_error": True,
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)

        if not info:
            return []

        entries = info.get("entries")

        if entries is not None:
            return [
                entry
                for entry in entries
                if entry
            ]

        return [info]

    except Exception as e:
        print(f"\n⚠️ Could not inspect media: {e}")
        return None


def _download_url(url, filename):
    if not url:
        print("\n❌ Image URL unavailable.")
        return False

    path = os.path.join(IMAGE_DIR, filename)

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 "
                "(Linux; Android 10) "
                "AppleWebKit/537.36 "
                "Chrome/151.0 Mobile Safari/537.36"
            ),
            "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            with open(path, "wb") as out:
                while True:
                    chunk = response.read(128 * 1024)

                    if not chunk:
                        break

                    out.write(chunk)

        # Don't accept an empty file as a successful download.
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            print("❌ Image download produced an empty file.")

            try:
                if os.path.exists(path):
                    os.remove(path)
            except OSError:
                pass

            return False

        print(f"✅ Saved: {filename}")
        return True

    except Exception as e:
        print(f"❌ Image download failed: {e}")

        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError:
            pass

        return False


def download_image_entry(entry, number=None):
    if not entry:
        return False

    # Prefer the image URL detected by get_image_entries().
    source_url = entry.get("_image_url")

    # Then try the normal yt-dlp media URL.
    if not source_url:
        source_url = entry.get("url")

    # Then explicit image/thumbnail fields.
    if not source_url:
        source_url = entry.get("thumbnail")

    if not source_url:
        source_url = _get_thumbnail_url(entry)

    if not source_url:
        print("\n❌ Image URL unavailable.")
        return False

    title = (
        entry.get("title")
        or entry.get("description")
        or entry.get("uploader")
        or "image"
    )

    ext = (
        _extension_from_url(source_url)
        or _extension_from_mime(entry.get("mime_type"))
        or entry.get("ext")
        or "jpg"
    )

    filename = make_filename(
        title,
        ext,
        number,
    )

    print(f"\n🖼️ Saving: {filename}")

    return _download_url(
        source_url,
        filename,
    )


def choose_image_entries(images):
    if not images:
        print("\n❌ No downloadable images were detected.")
        return False

    shown = images[:15]

    if len(images) > 15:
        print("\nFound more than 15 images; showing the first 15.")
    else:
        print(f"\nFound {len(shown)} image(s).")

    for i, entry in enumerate(shown, 1):
        title = (
            entry.get("title")
            or entry.get("description")
            or f"Image {i}"
        )

        print(f"{i}. {title}")

    print("A. Download all")
    print("Q. Cancel")

    while True:
        choice = input(
            f"\nChoose image (1-{len(shown)}) or A for all: "
        ).strip().lower()

        if choice == "a":
            success = 0

            for i, entry in enumerate(shown, 1):
                if download_image_entry(entry, i):
                    success += 1

            print(
                f"\n✅ Finished: "
                f"{success}/{len(shown)} images"
            )

            print(f"📁 Folder: {IMAGE_DIR}")

            return success > 0

        if choice == "q":
            print("\n❌ Cancelled.")
            return False

        try:
            number = int(choice)
        except ValueError:
            print("❌ Invalid choice.")
            continue

        if 1 <= number <= len(shown):
            return download_image_entry(
                shown[number - 1],
                number,
            )

        print(
            f"❌ Enter a number from 1 to "
            f"{len(shown)}, A, or Q."
        )


# ---------------------------------------------------------
# X / TWITTER PUBLIC IMAGE FALLBACK
# ---------------------------------------------------------

def _twitter_id(url):
    match = re.search(
        r"(?:twitter\.com|x\.com)/[^/]+/status/(\d+)",
        url,
        re.I,
    )

    return match.group(1) if match else None


def _base36(number):
    chars = "0123456789abcdefghijklmnopqrstuvwxyz"

    if number == 0:
        return "0"

    result = ""

    while number:
        number, rem = divmod(number, 36)
        result = chars[rem] + result

    return result


def _twitter_token(tweet_id):
    value = (
        int(tweet_id)
        / 1_000_000_000_000_000
    ) * math.pi

    raw = _base36(
        int(value * 1_000_000)
    )

    return raw.lstrip("0") or "0"


def _twitter_syndication(tweet_id):
    urls = [
        (
            "https://cdn.syndication.twimg.com/"
            f"tweet-result?id={tweet_id}&token=0"
        ),
        (
            "https://cdn.syndication.twimg.com/"
            f"tweet-result?id={tweet_id}"
            f"&token={urllib.parse.quote(_twitter_token(tweet_id))}"
        ),
    ]

    for api_url in urls:
        try:
            req = urllib.request.Request(
                api_url,
                headers={
                    "User-Agent": "Mozilla/5.0"
                },
            )

            with urllib.request.urlopen(
                req,
                timeout=15,
            ) as response:

                if response.status != 200:
                    continue

                return json.loads(
                    response.read().decode("utf-8")
                )

        except Exception:
            continue

    return None


def download_twitter_images(url):
    """
    Public X/Twitter photo fallback.

    Returns:
        True  = photos found/downloaded
        False = no photos found
        None  = fallback could not be queried
    """

    tweet_id = _twitter_id(url)

    if not tweet_id:
        return False

    data = _twitter_syndication(tweet_id)

    if not data:
        return None

    media = data.get("mediaDetails") or []

    photos = [
        media_item
        for media_item in media
        if (
            media_item.get("type") == "photo"
            and media_item.get("media_url_https")
        )
    ]

    if not photos:
        return False

    title = (
        data.get("text")
        or f"X image {tweet_id}"
    )

    print(
        f"\n🖼️ Found "
        f"{len(photos)} X image(s)."
    )

    entries = []

    for photo in photos:
        image_url = photo.get(
            "media_url_https"
        )

        entries.append({
            "title": title,
            "id": tweet_id,
            "ext": _extension_from_url(
                image_url
            ),
            "url": image_url,
            "_image_url": image_url,
        })

    return choose_image_entries(entries)
