from .models import ContentPackage

_BRG_GEOGRAPHIES: list[str] = [
    "Chicago, IL",
    "Dallas, TX",
    "Houston, TX",
    "Atlanta, GA",
    "New York, NY",
]

_BRG_DEFAULT_HASHTAGS: list[str] = [
    "#Leadership",
    "#BattleRhythm",
    "#BRG",
    "#ExecutiveCoach",
    "#Accountability",
    "#Discipline",
    "#Mindset",
    "#BusinessCoach",
    "#Entrepreneur",
    "#Faith",
]

_MIN_HASHTAGS = 10
_MAX_HASHTAGS = 15


def validate_hashtags(package: ContentPackage) -> ContentPackage:
    """Trim excess hashtags or pad with BRG defaults to satisfy the 10–15 constraint."""
    tags = list(package.hashtags)

    if len(tags) > _MAX_HASHTAGS:
        tags = tags[:_MAX_HASHTAGS]
    elif len(tags) < _MIN_HASHTAGS:
        existing = {t.lower() for t in tags}
        for default_tag in _BRG_DEFAULT_HASHTAGS:
            if len(tags) >= _MIN_HASHTAGS:
                break
            if default_tag.lower() not in existing:
                tags.append(default_tag)
                existing.add(default_tag.lower())

    return package.model_copy(update={"hashtags": tags})


def add_location_signals(package: ContentPackage) -> ContentPackage:
    """Append a BRG geo context sentence to the post body and populate location_signals.
    Idempotent — returns unchanged package if location_signals already populated."""
    if package.location_signals:
        return package
    geo_list = _BRG_GEOGRAPHIES[:-1]
    geo_last = _BRG_GEOGRAPHIES[-1]
    geo_str = ", ".join(geo_list) + f", and {geo_last}"
    signal_sentence = f" If you're a leader in {geo_str}, this applies to you."

    updated_post = package.post.model_copy(
        update={"body": package.post.body + signal_sentence}
    )
    return package.model_copy(
        update={
            "post": updated_post,
            "location_signals": list(_BRG_GEOGRAPHIES),
        }
    )
