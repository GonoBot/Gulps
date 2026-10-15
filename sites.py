# Site identification is informational only.
# V7 does NOT use this list as a download whitelist.
# If yt-dlp supports a URL, the generic downloader is allowed to try it.

def detect_site(url):
    url = (url or "").lower()

    checks = [
        ("youtube", ("youtube.com", "youtu.be")),
        ("tiktok", ("tiktok.com",)),
        ("twitter", ("twitter.com", "x.com")),
        ("instagram", ("instagram.com",)),
        ("facebook", ("facebook.com", "fb.watch")),
        ("reddit", ("reddit.com", "redd.it")),
        ("pinterest", ("pinterest.com", "pin.it")),
        ("snapchat", ("snapchat.com",)),
        ("threads", ("threads.net", "threads.com")),
        ("linkedin", ("linkedin.com",)),
        ("pornhub", ("pornhub.com",)),
        ("xvideos", ("xvideos.com",)),
        ("xnxx", ("xnxx.com",)),
        ("eporner", ("eporner.com",)),
        ("xhamster", ("xhamster.com",)),
    ]

    for name, domains in checks:
        if any(domain in url for domain in domains):
            return name

    return None
