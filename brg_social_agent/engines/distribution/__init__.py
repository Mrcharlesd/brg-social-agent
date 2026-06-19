import logging
from pathlib import Path

from config import Config
from engines.generation.models import ContentPackage

from .publishers.instagram import InstagramPublisher
from .publishers.linkedin import LinkedInPublisher
from .state import load_state, save_state

log = logging.getLogger(__name__)


def run_distribution_pipeline(config: Config) -> list[str]:
    """
    Scan queue_dir for rendered packages and distribute to enabled platforms.
    A package must have at least one .png to be considered rendered.
    Per-platform idempotency is tracked in distributed.json inside each post dir.
    Returns list of post_ids that had at least one new distribution this run.
    """
    queue_dir = Path(config.queue_dir)
    if not queue_dir.exists():
        log.warning("queue_dir not found at %s — nothing to distribute", queue_dir)
        return []

    publishers: dict = {}
    if "instagram" in config.enabled_platforms and config.instagram_account_id:
        publishers["instagram"] = InstagramPublisher(
            account_id=config.instagram_account_id,
            access_token=config.instagram_access_token,
            image_base_url=config.image_base_url,
        )
    if "linkedin" in config.enabled_platforms and config.linkedin_person_id:
        publishers["linkedin"] = LinkedInPublisher(
            person_id=config.linkedin_person_id,
            access_token=config.linkedin_access_token,
        )

    distributed_ids: list[str] = []

    for post_dir in sorted(queue_dir.iterdir()):
        if not post_dir.is_dir():
            continue

        content_path = post_dir / "content.json"
        if not content_path.exists():
            continue

        if not any(post_dir.glob("*.png")):
            log.info("Skipping %s — not yet rendered", post_dir.name)
            continue

        try:
            package = ContentPackage.model_validate_json(
                content_path.read_text(encoding="utf-8")
            )
        except Exception as exc:
            log.warning("Failed to load content package at %s: %s", content_path, exc)
            continue

        state = load_state(post_dir)
        any_new = False

        if "instagram" in publishers and not state.is_distributed_to("instagram"):
            try:
                _distribute_instagram(publishers["instagram"], package, post_dir)
                state = state.mark_distributed("instagram")
                save_state(state, post_dir)
                any_new = True
                log.info("Distributed %s to Instagram", package.post_id)
            except Exception as exc:
                log.warning("Instagram failed for %s: %s", package.post_id, exc)

        if "linkedin" in publishers and not state.is_distributed_to("linkedin"):
            try:
                _distribute_linkedin(publishers["linkedin"], package, post_dir)
                state = state.mark_distributed("linkedin")
                save_state(state, post_dir)
                any_new = True
                log.info("Distributed %s to LinkedIn", package.post_id)
            except Exception as exc:
                log.warning("LinkedIn failed for %s: %s", package.post_id, exc)

        if any_new:
            distributed_ids.append(package.post_id)

    return distributed_ids


def _distribute_instagram(
    ig: InstagramPublisher, package: ContentPackage, post_dir: Path
) -> None:
    carousel_slides = sorted(post_dir.glob("carousel_slide_*.png"))
    if carousel_slides:
        ig.publish_carousel(
            post_id=package.post_id,
            slide_filenames=[p.name for p in carousel_slides],
            caption=_build_ig_caption(package),
        )
    story_frame = post_dir / "story_frame_000.png"
    if story_frame.exists():
        ig.publish_story(post_id=package.post_id, filename="story_frame_000.png")


def _distribute_linkedin(
    li: LinkedInPublisher, package: ContentPackage, post_dir: Path
) -> None:
    quote_path = post_dir / "quote.png"
    li.publish_post(
        text=package.post.body,
        image_path=quote_path if quote_path.exists() else None,
    )


def _build_ig_caption(package: ContentPackage) -> str:
    return f"{package.post.body}\n\n{' '.join(package.hashtags)}"
