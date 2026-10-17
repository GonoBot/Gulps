from sites import detect_site
from core import download_video, download_audio, get_video_entries, get_media_entries
from image import (
    get_image_entries,
    choose_image_entries,
    download_twitter_images,
)

MAX_MULTI_VIDEOS = 15


def choose_quality(url, selected_entries=None):
    print("\nChoose quality:")
    print("1. Best quality")
    print("2. 1080p")
    print("3. 720p")
    print("4. 480p")
    print("5. Audio only (MP3)")
    print("Q. Cancel")

    choice = input("\nChoice: ").strip().lower()

    if choice == "1":
        return download_video(url, "best", selected_entries)
    if choice == "2":
        return download_video(url, "1080", selected_entries)
    if choice == "3":
        return download_video(url, "720", selected_entries)
    if choice == "4":
        return download_video(url, "480", selected_entries)
    if choice == "5":
        if selected_entries:
            print("\n❌ Audio download for selected multi-video items is not enabled.")
            return False
        print("\n🎵 Downloading audio...\n")
        return download_audio(url)
    if choice == "q":
        print("\n❌ Cancelled.")
        return False

    print("\n❌ Invalid choice.")
    return False


def choose_multi_video(url, entries=None):
    if entries is None:
        entries = get_video_entries(url)

    if entries is None:
        # Inspection failed. Do NOT show a quality menu because we do not
        # know that this URL is a video.
        return None

    if not entries:
        print("\n❌ No downloadable video was found.")
        return False

    if len(entries) <= 1:
        return choose_quality(url)

    shown = entries[:MAX_MULTI_VIDEOS]
    total = len(entries)

    print("\nThis post contains multiple videos!")
    print(f"Found {total} videos.")
    if total > MAX_MULTI_VIDEOS:
        print(f"Showing the first {MAX_MULTI_VIDEOS} only.")

    for number, entry in enumerate(shown, 1):
        title = entry.get("title") or f"Video {number}"
        duration = entry.get("duration")
        duration_text = ""
        if duration:
            try:
                seconds = int(float(duration))
                duration_text = f" ({seconds // 60}:{seconds % 60:02d})"
            except (TypeError, ValueError):
                pass
        print(f"{number}. {title}{duration_text}")

    print("\nA. Download all")

    while True:
        choice = input(
            f"\nChoose video (1-{len(shown)}) or A for all: "
        ).strip().lower()

        if choice == "a":
            selected = shown
            break

        try:
            number = int(choice)
        except ValueError:
            print("❌ Invalid choice.")
            continue

        if 1 <= number <= len(shown):
            selected = [shown[number - 1]]
            break

        print(f"❌ Enter a number from 1 to {len(shown)}, or A.")

    return choose_quality(url, selected)


def process_url(url):
    site = detect_site(url)
    if site:
        print(f"\n✅ Detected: {site}")
    else:
        print("\n🔎 No site-specific module detected.")
        print("Trying yt-dlp directly...")

    # X/Twitter image posts are a special case: yt-dlp's Twitter extractor
    # can report "No video could be found" for a post that contains photos.
    # Try the public syndication media data before treating the URL as video.
    if site == "twitter":
        twitter_result = download_twitter_images(url)
        if twitter_result is True:
            return True
        if twitter_result is False:
            # No X photos found; continue with normal yt-dlp media detection.
            pass

    # One media inspection. This prevents an inspection error from falling
    # through into the quality menu.
    entries = get_media_entries(url)

    if entries is None:
        print("\n❌ Could not inspect this URL.")
        print("No quality menu was opened because the media type is unknown.")
        return False

    images, videos = get_image_entries(entries)

    if images and not videos:
        return choose_image_entries(images)

    if videos:
        return choose_multi_video(url, videos)

    if images:
        # Mixed/ambiguous media: let the user choose images first.
        print(f"\nFound {len(images)} image(s) and {len(videos)} video(s).")
        print("1. Download images")
        print("2. Download videos")
        print("Q. Cancel")
        choice = input("\nChoice: ").strip().lower()
        if choice == "1":
            return choose_image_entries(images)
        if choice == "2":
            return choose_multi_video(url, videos)
        return False

    print("\n❌ No downloadable image or video was found for this URL.")
    return False


print("================================")
print("         Gulps V0.1")
print("================================")
print("Any URL supported by yt-dlp can be attempted.")
print("Image downloading is enabled.")
print("Multi-video selection: up to 15 items.")
print("Type q to quit.\n")

while True:
    url = input("URL: ").strip()

    if url.lower() == "q":
        print("\n👋 Downloader closed.")
        break

    if not url:
        print("\n❌ Please enter a URL.\n")
        continue

    try:
        process_url(url)
    except Exception as e:
        print("\n❌ Download failed.")
        print("Error:", e)
        print(
            "\nℹ️ If the site requires login, cookies, age verification, "
            "private access, or another permission, yt-dlp cannot bypass "
            "that access control."
        )

    print()
