Downloader V7

What V7 does:
- Attempts any URL that yt-dlp can extract; known-site detection is informational only.
- Supports video, audio, and image downloading.
- Image posts are handled before the video quality menu.
- X/Twitter public photo posts have a dedicated public-media fallback because yt-dlp can report "No video could be found" for photo-only posts.
- Multi-video selection is limited to 15 displayed items, with Download all.
- Video downloads use a short temporary filename while yt-dlp/FFmpeg work, then rename the completed file to a short title-only filename. This prevents long HLS fragment paths from causing Errno 36.

Important:
- V7 does not bypass private posts, login requirements, age verification, DRM, paywalls, or other access controls.
- If yt-dlp cannot access a post anonymously, V7 reports the failure.
- A URL being supported by yt-dlp does not guarantee that its media is accessible without authentication.

Folders:
- Videos: ~/storage/downloads/Videos
- Images: ~/storage/downloads/Images
- Audio: ~/storage/downloads/Py audio
