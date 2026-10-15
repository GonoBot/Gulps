import yt_dlp
import os
import re
import uuid


# ==========================================
# DOWNLOAD FOLDERS
# ==========================================

VIDEO_DIR = os.path.expanduser(
    "~/storage/downloads/Videos"
)

AUDIO_DIR = os.path.expanduser(
    "~/storage/downloads/Py audio"
)

# Create folders automatically if missing
os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)

# Keep existing name used by video functions
DOWNLOAD_DIR = VIDEO_DIR


# ==========================================
# SAFE FILENAME
# ==========================================

MAX_FILENAME_LENGTH = 100


def clean_filename(name):

    name = str(name or "video")

    # Remove characters that are unsafe in filenames
    name = re.sub(
        r'[\\/:*?"<>|]',
        "",
        name
    )

    # Remove control characters
    name = re.sub(
        r'[\x00-\x1f\x7f]',
        "",
        name
    )

    # Replace repeated whitespace
    name = re.sub(
        r'\s+',
        " ",
        name
    ).strip()

    return name or "video"


def safe_filename(info, original_ext, quality=None):
    """Return a short filename using the title only.

    The old V6.5 filename included the video ID and quality, which could
    make long social-media titles exceed Android/Termux path limits.
    V7 intentionally keeps only a shortened title plus the extension.
    """

    title = clean_filename(
        info.get("title", "video")
    )

    extension = clean_filename(
        original_ext or "mp4"
    )

    # Keep the complete filename comfortably below common Android limits.
    max_title_length = MAX_FILENAME_LENGTH - len(extension) - 1

    if len(title) > max_title_length:
        title = title[:max_title_length].rstrip()

    return f"{title}.{extension}"


# ==========================================
# OUTPUT TEMPLATE
# ==========================================

def prepare_filename(
    info,
    quality=None
):

    extension = info.get(
        "ext",
        "mp4"
    )

    filename = safe_filename(
        info,
        extension,
        quality
    )

    return os.path.join(
        DOWNLOAD_DIR,
        filename
    )


# ==========================================
# SHORT TEMPORARY OUTPUT PATH
# ==========================================

def make_temp_path(directory, extension="mp4"):
    """Use a very short filename while yt-dlp/FFmpeg work.

    HLS fragment names are derived from the output template. Keeping this
    temporary path short prevents long social-media titles from reappearing
    in .part-FragN.part filenames.
    """
    extension = clean_filename(extension or "mp4")
    return os.path.join(directory, f"v7_{uuid.uuid4().hex[:8]}.{extension}")


def rename_finished_file(temp_path, final_path):
    """Rename the completed temporary file to the user-facing filename."""
    candidates = [temp_path]
    root, _ = os.path.splitext(temp_path)
    for ext in (".mp4", ".webm", ".mkv", ".mov", ".m4v", ".mp3"):
        candidates.append(root + ext)

    source = next((p for p in candidates if os.path.isfile(p)), None)
    if not source:
        return False

    final_path = os.path.abspath(final_path)
    if os.path.abspath(source) == final_path:
        return True

    base, ext = os.path.splitext(final_path)
    candidate = final_path
    counter = 2
    while os.path.exists(candidate):
        candidate = f"{base} ({counter}){ext}"
        counter += 1

    os.replace(source, candidate)
    return True


# ==========================================
# PROGRESS
# ==========================================

def show_progress(data):

    if data["status"] == "downloading":

        percent = data.get(
            "_percent_str",
            ""
        ).strip()

        speed = data.get(
            "_speed_str",
            ""
        ).strip()

        eta = data.get(
            "_eta_str",
            ""
        ).strip()

        print(
            f"\r⬇️ {percent} | "
            f"{speed} | ETA {eta}",
            end="",
            flush=True
        )

    elif data["status"] == "finished":

        print(
            "\n🔄 Processing file..."
        )


# ==========================================
# VIDEO FORMAT
# ==========================================

def get_video_format(
    quality,
    orientation="horizontal"
):

    # ======================================
    # VERTICAL VIDEO
    # ======================================

    if orientation == "vertical":

        if quality == "1080":

            return (
                "bestvideo[width<=1080]+bestaudio/"
                "best[width<=1080]"
            )

        elif quality == "720":

            return (
                "bestvideo[width<=720]+bestaudio/"
                "best[width<=720]"
            )

        elif quality == "480":

            return (
                "bestvideo[width<=480]+bestaudio/"
                "best[width<=480]"
            )

        else:

            return (
                "bestvideo*+bestaudio/"
                "best"
            )


    # ======================================
    # HORIZONTAL VIDEO
    # ======================================

    if quality == "1080":

        return (
            "bestvideo[height<=1080]+bestaudio/"
            "best[height<=1080]"
        )

    elif quality == "720":

        return (
            "bestvideo[height<=720]+bestaudio/"
            "best[height<=720]"
        )

    elif quality == "480":

        return (
            "bestvideo[height<=480]+bestaudio/"
            "best[height<=480]"
        )

    else:

        return (
            "bestvideo*+bestaudio/"
            "best"
        )


# ==========================================
# MULTI-VIDEO ENTRY EXTRACTION
# ==========================================

def get_video_entries(url):
    """
    Extract video entries without downloading.

    A normal single video returns one item.
    Multi-video posts return individual entries.
    """

    options = {
        "noplaylist": False,
        "quiet": True,
        "no_warnings": True,
    }

    try:

        with yt_dlp.YoutubeDL(
            options
        ) as ydl:

            info = ydl.extract_info(
                url,
                download=False
            )

        if not info:
            return []

        entries = info.get(
            "entries"
        )

        # Normal single video
        if entries is None:

            if (
                info.get("_type")
                == "video"
                or info.get("url")
            ):
                return [info]

            return []

        result = []

        for entry in entries:

            if not entry:
                continue

            # Nested entries
            if entry.get("entries"):

                for nested in (
                    entry.get("entries")
                    or []
                ):

                    if nested:
                        result.append(
                            nested
                        )

            else:

                result.append(
                    entry
                )

        return result

    except Exception as e:

        print(
            "\n⚠️ Could not inspect the URL as video media."
        )
        print(
            "Info:",
            e
        )
        return None


# ==========================================
# MULTI-VIDEO DOWNLOAD
# ==========================================

def _download_selected_entries(
    url,
    quality,
    selected_entries
):

    for index, entry in enumerate(
        selected_entries,
        1
    ):

        print(
            f"\n========== Video "
            f"{index}/{len(selected_entries)} "
            f"=========="
        )

        video_url = entry.get(
            "url"
        )

        if not video_url:

            print(
                f"❌ No direct video URL "
                f"found for video {index}."
            )

            continue

        # ==================================
        # DETECT ORIENTATION
        # ==================================

        width = entry.get(
            "width"
        )

        height = entry.get(
            "height"
        )

        if (
            width
            and height
            and height > width
        ):

            orientation = "vertical"

        else:

            orientation = "horizontal"

        # ==================================
        # SELECT FORMAT
        # ==================================

        if "snapchat.com" in url.lower():

            selected_format = "0"

        else:

            selected_format = (
                get_video_format(
                    quality,
                    orientation
                )
            )

        # ==================================
        # FILENAME
        # ==================================

        extension = entry.get(
            "ext",
            "mp4"
        )

        final_filename = safe_filename(
            entry,
            "mp4",
            None
        )
        final_path = os.path.join(DOWNLOAD_DIR, final_filename)
        temp_path = make_temp_path(DOWNLOAD_DIR, "mp4")

        print(
            f"📁 Saving as: "
            f"{os.path.basename(final_path)}"
        )

        # ==================================
        # OPTIONS
        # ==================================

        options = {

            "format": selected_format,

            "outtmpl": temp_path,

            "noplaylist": True,

            "merge_output_format": "mp4",

            "progress_hooks": [
                show_progress
            ],

            "restrictfilenames": True,
            "noprogress": False,

        }

        try:

            with yt_dlp.YoutubeDL(
                options
            ) as ydl:

                ydl.download([
                    video_url
                ])

            if not rename_finished_file(temp_path, final_path):
                print("❌ Download completed but the output file was not found.")

        except Exception as e:

            print(
                f"\n❌ Video {index} failed."
            )

            print(
                "Error:",
                e
            )

    return True


# ==========================================
# VIDEO DOWNLOAD
# ==========================================

def download_video(
    url,
    quality="best",
    selected_entries=None
):

    # ======================================
    # MULTI-VIDEO
    # ======================================

    if selected_entries:

        return _download_selected_entries(
            url,
            quality,
            selected_entries
        )

    is_snapchat = (
        "snapchat.com"
        in url.lower()
    )

    try:

        # ==================================
        # EXTRACT INFORMATION
        # ==================================

        info_options = {
            "noplaylist": True
        }

        with yt_dlp.YoutubeDL(
            info_options
        ) as ydl:

            info = ydl.extract_info(
                url,
                download=False
            )

        # ==================================
        # SNAPCHAT
        # ==================================

        if is_snapchat:

            selected_format = "0"

        else:

            # ==================================
            # DETECT ORIENTATION
            # ==================================

            width = info.get(
                "width"
            )

            height = info.get(
                "height"
            )

            if width and height:

                if height > width:

                    orientation = "vertical"

                else:

                    orientation = "horizontal"

            else:

                orientation = "horizontal"

            print(
                f"📐 Video: "
                f"{orientation}"
            )

            # ==================================
            # SELECT QUALITY
            # ==================================

            selected_format = (
                get_video_format(
                    quality,
                    orientation
                )
            )

            # ==================================
            # CHECK VIDEO FORMATS
            # ==================================

            formats = info.get(
                "formats",
                []
            )

            video_formats = [
                f
                for f in formats
                if f.get("vcodec")
                not in (
                    None,
                    "none"
                )
            ]

            if not video_formats:
                print(
                    "\n⚠️ No video format was exposed during "
                    "pre-check. Letting yt-dlp attempt the URL directly."
                )

        # ==================================
        # DOWNLOAD OPTIONS
        # ==================================

        options = {

            "format": selected_format,

            "outtmpl": os.path.join(
                DOWNLOAD_DIR,
                "%(title)s "
                "[%(id)s].%(ext)s"
            ),

            "noplaylist": True,

            "merge_output_format": "mp4",

            "progress_hooks": [
                show_progress
            ],

            "restrictfilenames": True,
            "noprogress": False,

        }

        # ==================================
        # SAFE FILENAME
        # ==================================

        final_filename = safe_filename(info, "mp4", None)
        final_path = os.path.join(DOWNLOAD_DIR, final_filename)
        temp_path = make_temp_path(DOWNLOAD_DIR, "mp4")

        print(
            f"📁 Saving as: "
            f"{os.path.basename(final_path)}"
        )

        options["outtmpl"] = temp_path

        # ==================================
        # DOWNLOAD
        # ==================================

        with yt_dlp.YoutubeDL(
            options
        ) as ydl:

            ydl.download([
                url
            ])

        if not rename_finished_file(temp_path, final_path):
            print("❌ Download completed but the output file was not found.")

    except Exception as e:

        print(
            "\n❌ Download failed."
        )

        print(
            "Error:",
            e
        )

        return False

    return True


# ==========================================
# AUDIO DOWNLOAD
# ==========================================

def download_audio(url):

    try:

        # ==================================
        # EXTRACT INFORMATION
        # ==================================

        info_options = {
            "noplaylist": True
        }

        with yt_dlp.YoutubeDL(
            info_options
        ) as ydl:

            info = ydl.extract_info(
                url,
                download=False
            )

        # ==================================
        # AUDIO FILENAME
        # ==================================

        final_filename = safe_filename(info, "mp3", None)
        final_path = os.path.join(AUDIO_DIR, final_filename)
        temp_path = make_temp_path(AUDIO_DIR, "mp3")

        print(
            f"📁 Saving as: "
            f"{os.path.basename(final_path)}"
        )

        # ==================================
        # AUDIO OPTIONS
        # ==================================

        options = {

            "format":
                "bestaudio/best",

            "outtmpl":
                temp_path,

            "noplaylist":
                True,

            "postprocessors": [

                {
                    "key":
                        "FFmpegExtractAudio",

                    "preferredcodec":
                        "mp3",

                    "preferredquality":
                        "192",
                }

            ],

        }

        # ==================================
        # DOWNLOAD
        # ==================================

        with yt_dlp.YoutubeDL(
            options
        ) as ydl:

            ydl.download([
                url
            ])

        if not rename_finished_file(temp_path, final_path):
            print("❌ Audio completed but the output file was not found.")

    except Exception as e:

        print(
            "\n❌ Audio download failed."
        )

        print(
            "Error:",
            e
        )

        return False

    return True


# ==========================================
# GENERIC IMAGE SUPPORT
# ==========================================

def get_media_entries(url):
    """Return yt-dlp media entries without downloading.

    Returns None when yt-dlp cannot inspect the URL. It does not convert an
    inspection error into an empty list, because an empty list means that
    extraction succeeded but no media entries were exposed.
    """
    options = {
        "noplaylist": False,
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "ignore_no_formats_error": True,
    }
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)
        if not info:
            return []
        entries = info.get("entries")
        if entries is not None:
            return [e for e in entries if e]
        return [info]
    except Exception as e:
        print("\n⚠️ Could not inspect media:", e)
        return None


def download_image(entry, number=None):
    if not entry:
        return False

    source_url = (
        entry.get("webpage_url")
        or entry.get("original_url")
        or entry.get("url")
    )
    if not source_url:
        print("\\n❌ Image URL unavailable.")
        return False

    image_dir = os.path.expanduser("~/storage/downloads/Images")
    os.makedirs(image_dir, exist_ok=True)

    title = clean_filename(entry.get("title", "image"))
    image_id = clean_filename(entry.get("id", str(number or "unknown")))
    ext = clean_filename(entry.get("ext", "jpg")) or "jpg"
    prefix = f"{number} " if number is not None else ""
    filename = os.path.join(image_dir, f"{title} {prefix}[{image_id}].{ext}")

    options = {
        "format": "best",
        "outtmpl": filename,
        "noplaylist": True,
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([source_url])
        print("✅ Image finished.")
        return True
    except Exception as e:
        print("\\n❌ Image download failed.")
        print("Error:", e)
        return False
