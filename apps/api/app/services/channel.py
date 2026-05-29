PLATFORM_PRIORITY = [
    "instagram",
    "youtube",
    "tiktok",
    "twitter",
    "linkedin",
    "facebook",
    "threads",
    "bluesky",
    "mastodon",
]


def compute_recommended_channel(platforms: list[str] | None) -> str | None:
    if not platforms:
        return None
    for preferred in PLATFORM_PRIORITY:
        for plat in platforms:
            if preferred in plat.lower():
                return plat
    return platforms[0]
