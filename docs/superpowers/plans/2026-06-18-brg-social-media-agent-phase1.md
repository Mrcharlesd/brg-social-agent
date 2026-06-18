# BRG Social Media Agent — Phase 1: Content Intelligence Engine

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the web scraping and trend-ranking engine that monitors 7 source types every 6 hours and writes the top 20 ranked leadership/coaching topics to `data/trends.json`.

**Architecture:** A modular Python package (`brg_social_agent`) with a clean `engines/intelligence/` module containing three focused files: `sources.py` (source registry), `scraper.py` (per-source scraping functions), and `ranker.py` (scoring + duplicate suppression). A pipeline entry point in `engines/intelligence/__init__.py` wires them together and writes output.

**Tech Stack:** Python 3.11+, `feedparser` (RSS/podcasts), `praw` (Reddit), `python-dotenv` (env config), `pytest` + `pytest-mock` (testing)

## Global Constraints

- Python >= 3.11 (uses `list[T]` built-in generics, `match` statements not needed)
- All data written to `data/` directory relative to project root
- No secrets hardcoded anywhere — all credentials via environment variables
- `ContentItem.timestamp` is always timezone-aware UTC
- Ranker suppresses duplicate topics for 14 days
- Top 20 items written to `data/trends.json` per pipeline run
- Test coverage: every public function has at least one passing test

---

### Task 1: Project Scaffolding + Config

**Files:**
- Create: `brg_social_agent/pyproject.toml`
- Create: `brg_social_agent/.env.example`
- Create: `brg_social_agent/config.py`
- Create: `brg_social_agent/engines/__init__.py` (empty)
- Create: `brg_social_agent/engines/intelligence/__init__.py` (empty for now)
- Create: `brg_social_agent/tests/__init__.py` (empty)
- Create: `brg_social_agent/tests/test_intelligence/__init__.py` (empty)
- Create: `brg_social_agent/data/.gitkeep` (so data dirs exist in git)
- Create: `brg_social_agent/conftest.py` (adds project root to sys.path so pytest finds `config` and `engines`)
- Test: `brg_social_agent/tests/test_config.py`

**Interfaces:**
- Produces: `load_config() -> Config` — used by every downstream task

- [ ] **Step 1: Create project root directory and pyproject.toml**

```bash
mkdir -p brg_social_agent/engines/intelligence
mkdir -p brg_social_agent/tests/test_intelligence
mkdir -p brg_social_agent/data/queue brg_social_agent/data/posted
mkdir -p brg_social_agent/data/analytics brg_social_agent/data/errors brg_social_agent/data/logs
touch brg_social_agent/data/.gitkeep
cd brg_social_agent
```

Create `pyproject.toml`:

```toml
[project]
name = "brg-social-agent"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "feedparser>=6.0.11",
    "praw>=7.7.1",
    "youtube-transcript-api>=0.6.2",
    "newspaper4k>=0.9.3",
    "pytrends>=4.9.2",
    "python-dotenv>=1.0.1",
    "APScheduler>=3.10.4",
    "httpx>=0.27.0",
    "tweepy>=4.14.0",
    "google-api-python-client>=2.136.0",
    "anthropic>=0.30.0",
    "pydantic>=2.7.0",
    "jinja2>=3.1.4",
    "Pillow>=10.4.0",
    "playwright>=1.44.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.2.2",
    "pytest-mock>=3.14.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 1b: Create conftest.py so pytest resolves imports from project root**

```python
# brg_social_agent/conftest.py
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
```

- [ ] **Step 2: Create .env.example**

```bash
# brg_social_agent/.env.example
ANTHROPIC_API_KEY=your_anthropic_key_here
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret

# Optional brand overrides (defaults shown)
BRAND_PRIMARY_COLOR=#1A1A2E
BRAND_ACCENT_COLOR=#E94560
BRAND_FONT_FAMILY=Inter
LOGO_PATH=assets/brg_logo.svg
HEADSHOT_PATH=assets/charles_headshot.jpg
```

- [ ] **Step 3: Write config.py**

```python
# brg_social_agent/config.py
import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise EnvironmentError(f"Required environment variable {key!r} is not set")
    return val


@dataclass
class Config:
    # Credentials
    anthropic_api_key: str = field(default_factory=lambda: _require("ANTHROPIC_API_KEY"))
    reddit_client_id: str = field(default_factory=lambda: _require("REDDIT_CLIENT_ID"))
    reddit_client_secret: str = field(default_factory=lambda: _require("REDDIT_CLIENT_SECRET"))
    reddit_user_agent: str = "BRGSocialAgent/1.0"

    # Brand
    brand_primary_color: str = field(default_factory=lambda: os.getenv("BRAND_PRIMARY_COLOR", "#1A1A2E"))
    brand_accent_color: str = field(default_factory=lambda: os.getenv("BRAND_ACCENT_COLOR", "#E94560"))
    brand_font_family: str = field(default_factory=lambda: os.getenv("BRAND_FONT_FAMILY", "Inter"))
    logo_path: str = field(default_factory=lambda: os.getenv("LOGO_PATH", "assets/brg_logo.svg"))
    headshot_path: str = field(default_factory=lambda: os.getenv("HEADSHOT_PATH", "assets/charles_headshot.jpg"))

    # Data paths
    trends_file: str = "data/trends.json"
    seen_topics_file: str = "data/seen_topics.json"
    queue_dir: str = "data/queue"
    posted_dir: str = "data/posted"
    analytics_dir: str = "data/analytics"
    errors_dir: str = "data/errors"
    logs_dir: str = "data/logs"


def load_config() -> Config:
    return Config()
```

- [ ] **Step 4: Write the failing config test**

```python
# brg_social_agent/tests/test_config.py
import pytest
from config import load_config


def test_load_config_raises_on_missing_anthropic_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("REDDIT_CLIENT_ID", raising=False)
    monkeypatch.delenv("REDDIT_CLIENT_SECRET", raising=False)
    with pytest.raises(EnvironmentError, match="ANTHROPIC_API_KEY"):
        load_config()


def test_load_config_raises_on_missing_reddit_id(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.delenv("REDDIT_CLIENT_ID", raising=False)
    monkeypatch.delenv("REDDIT_CLIENT_SECRET", raising=False)
    with pytest.raises(EnvironmentError, match="REDDIT_CLIENT_ID"):
        load_config()


def test_load_config_success(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("REDDIT_CLIENT_ID", "test-id")
    monkeypatch.setenv("REDDIT_CLIENT_SECRET", "test-secret")
    config = load_config()
    assert config.anthropic_api_key == "test-key"
    assert config.trends_file == "data/trends.json"
    assert config.brand_primary_color == "#1A1A2E"
```

- [ ] **Step 5: Run tests to verify they fail (config not created yet at this point — after creating config.py they should pass)**

```bash
cd brg_social_agent
pip install -e ".[dev]"
pytest tests/test_config.py -v
```

Expected: All 3 tests PASS (config.py is already written in Step 3)

- [ ] **Step 6: Commit**

```bash
git init
git add pyproject.toml .env.example config.py engines/__init__.py \
        engines/intelligence/__init__.py tests/__init__.py \
        tests/test_intelligence/__init__.py tests/test_config.py \
        data/.gitkeep
git commit -m "feat: project scaffolding and config module"
```

---

### Task 2: Data Model + Sources Registry

**Files:**
- Create: `brg_social_agent/engines/intelligence/scraper.py` (ContentItem dataclass only)
- Create: `brg_social_agent/engines/intelligence/sources.py`
- Test: `brg_social_agent/tests/test_intelligence/test_sources.py`

**Interfaces:**
- Produces:
  - `ContentItem(title, body, url, source, timestamp, likes, shares, comments, score)` — used by Tasks 3, 4, 5, 6
  - `ContentItem.to_dict() -> dict` — used by Task 6 when writing trends.json
  - `SOURCES: list[Source]` — used by Task 6 pipeline
  - `SourceType` enum with values `RSS`, `REDDIT`, `YOUTUBE`, `TRENDS` — used by Task 6 pipeline

- [ ] **Step 1: Write the failing test**

```python
# brg_social_agent/tests/test_intelligence/test_sources.py
from datetime import datetime, timezone
from engines.intelligence.scraper import ContentItem
from engines.intelligence.sources import SOURCES, SourceType


def test_content_item_to_dict_contains_required_keys():
    item = ContentItem(
        title="Lead with purpose",
        body="Discipline beats motivation every time.",
        url="https://example.com/article",
        source="Forbes Leadership",
        timestamp=datetime(2026, 6, 18, 10, 0, 0, tzinfo=timezone.utc),
        likes=120,
        shares=30,
        comments=15,
        score=0.75,
    )
    d = item.to_dict()
    assert d["title"] == "Lead with purpose"
    assert d["source"] == "Forbes Leadership"
    assert d["timestamp"] == "2026-06-18T10:00:00+00:00"
    assert d["score"] == 0.75


def test_sources_registry_contains_rss_sources():
    rss = [s for s in SOURCES if s.type == SourceType.RSS]
    assert len(rss) >= 3
    for s in rss:
        assert s.url is not None and s.url.startswith("http")


def test_sources_registry_contains_reddit_sources():
    reddit = [s for s in SOURCES if s.type == SourceType.REDDIT]
    assert len(reddit) >= 3
    for s in reddit:
        assert s.subreddit is not None


def test_all_sources_have_names():
    for s in SOURCES:
        assert s.name and len(s.name) > 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_intelligence/test_sources.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'engines.intelligence.scraper'`

- [ ] **Step 3: Create scraper.py with ContentItem only**

```python
# brg_social_agent/engines/intelligence/scraper.py
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ContentItem:
    title: str
    body: str
    url: str
    source: str
    timestamp: datetime
    likes: int = 0
    shares: int = 0
    comments: int = 0
    score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "body": self.body,
            "url": self.url,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "likes": self.likes,
            "shares": self.shares,
            "comments": self.comments,
            "score": self.score,
        }
```

- [ ] **Step 4: Create sources.py**

```python
# brg_social_agent/engines/intelligence/sources.py
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class SourceType(str, Enum):
    RSS = "rss"
    REDDIT = "reddit"
    YOUTUBE = "youtube"
    TRENDS = "trends"


@dataclass
class Source:
    name: str
    type: SourceType
    url: Optional[str] = None
    subreddit: Optional[str] = None
    youtube_channel_id: Optional[str] = None


SOURCES: list[Source] = [
    # News / RSS
    Source(name="Forbes Leadership", type=SourceType.RSS,
           url="https://www.forbes.com/leadership/feed/"),
    Source(name="Harvard Business Review", type=SourceType.RSS,
           url="https://hbr.org/rss/topic/leadership"),
    Source(name="Inc Magazine", type=SourceType.RSS,
           url="https://www.inc.com/rss.html"),
    # Reddit
    Source(name="Reddit Entrepreneur", type=SourceType.REDDIT, subreddit="Entrepreneur"),
    Source(name="Reddit Leadership", type=SourceType.REDDIT, subreddit="leadership"),
    Source(name="Reddit Self Improvement", type=SourceType.REDDIT, subreddit="selfimprovement"),
    # Google Trends
    Source(name="Google Trends", type=SourceType.TRENDS),
]
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_intelligence/test_sources.py -v
```

Expected: All 4 tests PASS

- [ ] **Step 6: Commit**

```bash
git add engines/intelligence/scraper.py engines/intelligence/sources.py \
        tests/test_intelligence/test_sources.py
git commit -m "feat: ContentItem model and sources registry"
```

---

### Task 3: RSS + Podcast Scraper

**Files:**
- Modify: `brg_social_agent/engines/intelligence/scraper.py` (add `scrape_rss()`)
- Test: `brg_social_agent/tests/test_intelligence/test_scraper.py`

**Interfaces:**
- Consumes: `ContentItem`, `Source` (from Task 2)
- Produces: `scrape_rss(source: Source) -> list[ContentItem]` — used by Task 6 pipeline

- [ ] **Step 1: Write the failing test**

```python
# brg_social_agent/tests/test_intelligence/test_scraper.py
import pytest
from datetime import timezone
from unittest.mock import patch, MagicMock
from engines.intelligence.scraper import ContentItem, scrape_rss
from engines.intelligence.sources import Source, SourceType


def _mock_rss_feed():
    entry = MagicMock()
    entry.title = "5 Leadership Lessons for Entrepreneurs"
    entry.summary = "How to build a high-performing team through accountability."
    entry.link = "https://forbes.com/article/123"
    entry.published_parsed = (2026, 6, 18, 10, 0, 0, 0, 169, 0)
    feed = MagicMock()
    feed.entries = [entry]
    return feed


def test_scrape_rss_returns_content_items():
    source = Source(name="Forbes Leadership", type=SourceType.RSS,
                    url="https://forbes.com/leadership/feed/")
    with patch("engines.intelligence.scraper.feedparser.parse",
               return_value=_mock_rss_feed()):
        items = scrape_rss(source)
    assert len(items) == 1
    assert isinstance(items[0], ContentItem)
    assert items[0].title == "5 Leadership Lessons for Entrepreneurs"
    assert items[0].source == "Forbes Leadership"
    assert items[0].timestamp.tzinfo == timezone.utc


def test_scrape_rss_handles_missing_published_date():
    entry = MagicMock()
    entry.title = "Article without date"
    entry.summary = "Summary text"
    entry.link = "https://example.com/article"
    entry.published_parsed = None
    feed = MagicMock()
    feed.entries = [entry]
    source = Source(name="Test RSS", type=SourceType.RSS, url="https://test.com/feed")
    with patch("engines.intelligence.scraper.feedparser.parse", return_value=feed):
        items = scrape_rss(source)
    assert len(items) == 1
    assert items[0].timestamp is not None
    assert items[0].timestamp.tzinfo == timezone.utc


def test_scrape_rss_limits_to_ten_entries():
    entries = []
    for i in range(15):
        e = MagicMock()
        e.title = f"Article {i}"
        e.summary = "Summary"
        e.link = f"https://example.com/{i}"
        e.published_parsed = (2026, 6, 18, 10, 0, 0, 0, 169, 0)
        entries.append(e)
    feed = MagicMock()
    feed.entries = entries
    source = Source(name="Test", type=SourceType.RSS, url="https://test.com/feed")
    with patch("engines.intelligence.scraper.feedparser.parse", return_value=feed):
        items = scrape_rss(source)
    assert len(items) == 10
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_intelligence/test_scraper.py -v
```

Expected: FAIL — `ImportError: cannot import name 'scrape_rss'`

- [ ] **Step 3: Add scrape_rss() to scraper.py**

Add these imports at the top of `engines/intelligence/scraper.py`:

```python
from datetime import datetime, timezone
import feedparser
from .sources import Source
```

Add this function after the `ContentItem` class:

```python
def scrape_rss(source: Source) -> list["ContentItem"]:
    feed = feedparser.parse(source.url)
    items = []
    for entry in feed.entries[:10]:
        try:
            ts = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        except (AttributeError, TypeError):
            ts = datetime.now(timezone.utc)
        items.append(ContentItem(
            title=entry.get("title", "").strip(),
            body=entry.get("summary", "")[:1000].strip(),
            url=entry.get("link", ""),
            source=source.name,
            timestamp=ts,
        ))
    return items
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_intelligence/test_scraper.py -v
```

Expected: All 3 RSS tests PASS

- [ ] **Step 5: Commit**

```bash
git add engines/intelligence/scraper.py tests/test_intelligence/test_scraper.py
git commit -m "feat: RSS and podcast scraper"
```

---

### Task 4: Reddit Scraper

**Files:**
- Modify: `brg_social_agent/engines/intelligence/scraper.py` (add `scrape_reddit()`)
- Modify: `brg_social_agent/tests/test_intelligence/test_scraper.py` (add Reddit tests)

**Interfaces:**
- Consumes: `ContentItem`, `Source` (Task 2); `praw.Reddit` instance
- Produces: `scrape_reddit(source: Source, reddit: praw.Reddit) -> list[ContentItem]` — used by Task 6 pipeline

- [ ] **Step 1: Add failing Reddit tests to test_scraper.py**

Append these tests to `tests/test_intelligence/test_scraper.py`:

```python
def _mock_reddit_post(title="Leadership mindset shift", score=450,
                      num_comments=87, selftext="Build your team's accountability."):
    post = MagicMock()
    post.title = title
    post.selftext = selftext
    post.permalink = "/r/leadership/comments/abc123/title"
    post.created_utc = 1750240800.0  # 2026-06-18 10:00:00 UTC
    post.score = score
    post.num_comments = num_comments
    post.stickied = False
    return post


def test_scrape_reddit_returns_content_items():
    import praw
    source = Source(name="Reddit Leadership", type=SourceType.REDDIT, subreddit="leadership")
    mock_reddit = MagicMock(spec=praw.Reddit)
    mock_reddit.subreddit.return_value.hot.return_value = [_mock_reddit_post()]
    with patch("engines.intelligence.scraper.praw", mock_reddit):
        from engines.intelligence.scraper import scrape_reddit
        items = scrape_reddit(source, mock_reddit)
    assert len(items) == 1
    assert items[0].title == "Leadership mindset shift"
    assert items[0].likes == 450
    assert items[0].comments == 87
    assert items[0].timestamp.tzinfo == timezone.utc


def test_scrape_reddit_skips_stickied_posts():
    import praw
    stickied = _mock_reddit_post(title="Stickied announcement")
    stickied.stickied = True
    normal = _mock_reddit_post(title="Normal post")
    source = Source(name="Reddit Leadership", type=SourceType.REDDIT, subreddit="leadership")
    mock_reddit = MagicMock(spec=praw.Reddit)
    mock_reddit.subreddit.return_value.hot.return_value = [stickied, normal]
    with patch("engines.intelligence.scraper.praw", mock_reddit):
        from engines.intelligence.scraper import scrape_reddit
        items = scrape_reddit(source, mock_reddit)
    assert len(items) == 1
    assert items[0].title == "Normal post"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_intelligence/test_scraper.py::test_scrape_reddit_returns_content_items -v
```

Expected: FAIL — `ImportError: cannot import name 'scrape_reddit'`

- [ ] **Step 3: Add scrape_reddit() to scraper.py**

Add `import praw` to the imports at the top of `engines/intelligence/scraper.py`.

Add this function after `scrape_rss()`:

```python
def scrape_reddit(source: Source, reddit: praw.Reddit) -> list["ContentItem"]:
    subreddit = reddit.subreddit(source.subreddit)
    items = []
    for post in subreddit.hot(limit=25):
        if post.stickied:
            continue
        items.append(ContentItem(
            title=post.title,
            body=post.selftext[:500].strip(),
            url=f"https://reddit.com{post.permalink}",
            source=source.name,
            timestamp=datetime.fromtimestamp(post.created_utc, tz=timezone.utc),
            likes=post.score,
            comments=post.num_comments,
        ))
    return items
```

- [ ] **Step 4: Run all scraper tests**

```bash
pytest tests/test_intelligence/test_scraper.py -v
```

Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add engines/intelligence/scraper.py tests/test_intelligence/test_scraper.py
git commit -m "feat: Reddit scraper"
```

---

### Task 5: Ranker + Duplicate Suppression

**Files:**
- Create: `brg_social_agent/engines/intelligence/ranker.py`
- Test: `brg_social_agent/tests/test_intelligence/test_ranker.py`

**Interfaces:**
- Consumes: `ContentItem` (Task 2); `seen_topics_file: str` path from `Config`
- Produces:
  - `rank(items: list[ContentItem], seen_file: str, top_n: int = 20) -> list[ContentItem]` — used by Task 6
  - `mark_seen(title: str, seen: dict, seen_file: str) -> None` — used by Task 6
  - `load_seen_topics(seen_file: str) -> dict[str, str]` — used by Task 6

- [ ] **Step 1: Write the failing tests**

```python
# brg_social_agent/tests/test_intelligence/test_ranker.py
import json
import os
import pytest
from datetime import datetime, timedelta, timezone
from engines.intelligence.scraper import ContentItem
from engines.intelligence.ranker import (
    recency_score,
    engagement_score,
    relevance_score,
    rank,
    mark_seen,
    load_seen_topics,
    is_duplicate,
)


def _item(title="Leadership and coaching strategy",
          body="Mindset growth discipline accountability",
          hours_old=1, likes=100, shares=10, comments=20) -> ContentItem:
    return ContentItem(
        title=title, body=body,
        url="https://example.com",
        source="Test",
        timestamp=datetime.now(timezone.utc) - timedelta(hours=hours_old),
        likes=likes, shares=shares, comments=comments,
    )


# --- Scoring unit tests ---

def test_recency_score_fresh_item_near_one():
    score = recency_score(datetime.now(timezone.utc))
    assert score > 0.99


def test_recency_score_day_old_is_half():
    ts = datetime.now(timezone.utc) - timedelta(hours=24)
    score = recency_score(ts)
    assert 0.45 < score < 0.55


def test_recency_score_very_old_item_near_zero():
    ts = datetime.now(timezone.utc) - timedelta(hours=168)
    score = recency_score(ts)
    assert score < 0.05


def test_engagement_score_caps_at_one():
    score = engagement_score(likes=10000, shares=5000, comments=2000)
    assert score == 1.0


def test_engagement_score_zero_for_no_engagement():
    assert engagement_score(0, 0, 0) == 0.0


def test_relevance_score_on_topic_above_half():
    score = relevance_score(
        "Leadership coaching for entrepreneurs",
        "business mindset growth strategy"
    )
    assert score > 0.5


def test_relevance_score_off_topic_is_zero():
    score = relevance_score("Best pizza recipes", "cooking tips for beginners")
    assert score == 0.0


# --- Duplicate suppression ---

def test_is_duplicate_returns_false_when_not_seen(tmp_path):
    seen_file = str(tmp_path / "seen.json")
    seen = load_seen_topics(seen_file)
    assert not is_duplicate("Brand new topic", seen)


def test_is_duplicate_returns_true_within_14_days(tmp_path):
    seen_file = str(tmp_path / "seen.json")
    seen = {}
    mark_seen("Leadership topic", seen, seen_file)
    seen = load_seen_topics(seen_file)
    assert is_duplicate("Leadership topic", seen)


def test_is_duplicate_case_insensitive(tmp_path):
    seen_file = str(tmp_path / "seen.json")
    seen = {}
    mark_seen("Leadership Topic", seen, seen_file)
    seen = load_seen_topics(seen_file)
    assert is_duplicate("leadership topic", seen)


# --- rank() integration ---

def test_rank_returns_sorted_highest_first(tmp_path):
    seen_file = str(tmp_path / "seen.json")
    low = _item(title="pizza recipes cooking", body="food tips", hours_old=72, likes=0)
    high = _item(title="leadership coaching business", body="mindset growth strategy",
                 hours_old=1, likes=500, comments=100)
    ranked = rank([low, high], seen_file)
    assert ranked[0].title == "leadership coaching business"


def test_rank_limits_to_top_n(tmp_path):
    seen_file = str(tmp_path / "seen.json")
    items = [_item(title=f"Leadership article {i}") for i in range(30)]
    ranked = rank(items, seen_file, top_n=20)
    assert len(ranked) <= 20


def test_rank_excludes_seen_duplicates(tmp_path):
    seen_file = str(tmp_path / "seen.json")
    seen = {}
    mark_seen("Leadership topic", seen, seen_file)
    items = [_item(title="Leadership topic"), _item(title="New business growth strategy")]
    ranked = rank(items, seen_file)
    titles = [r.title for r in ranked]
    assert "Leadership topic" not in titles
    assert "New business growth strategy" in titles
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_intelligence/test_ranker.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'engines.intelligence.ranker'`

- [ ] **Step 3: Create ranker.py**

```python
# brg_social_agent/engines/intelligence/ranker.py
import json
import math
import os
from datetime import datetime, timedelta, timezone

from .scraper import ContentItem

BRG_KEYWORDS = [
    "leadership", "coaching", "business", "entrepreneur", "productivity",
    "team", "culture", "mindset", "growth", "strategy", "faith", "purpose",
    "execution", "accountability", "performance", "vision", "mission",
    "discipline", "resilience", "transformation",
]


def recency_score(timestamp: datetime, half_life_hours: float = 24.0) -> float:
    age_hours = (datetime.now(timezone.utc) - timestamp).total_seconds() / 3600
    return math.exp(-age_hours / half_life_hours * math.log(2))


def engagement_score(likes: int, shares: int, comments: int) -> float:
    total = likes + (shares * 2) + (comments * 1.5)
    return min(total / 1000.0, 1.0)


def relevance_score(title: str, body: str) -> float:
    text = f"{title} {body}".lower()
    matches = sum(1 for kw in BRG_KEYWORDS if kw in text)
    return min(matches / 5.0, 1.0)


def load_seen_topics(seen_file: str) -> dict[str, str]:
    if not os.path.exists(seen_file):
        return {}
    with open(seen_file) as f:
        return json.load(f)


def is_duplicate(title: str, seen: dict[str, str], days: int = 14) -> bool:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    key = title.lower()
    return key in seen and seen[key] > cutoff


def mark_seen(title: str, seen: dict[str, str], seen_file: str) -> None:
    seen[title.lower()] = datetime.now(timezone.utc).isoformat()
    os.makedirs(os.path.dirname(seen_file) or ".", exist_ok=True)
    with open(seen_file, "w") as f:
        json.dump(seen, f, indent=2)


def rank(
    items: list[ContentItem],
    seen_file: str,
    top_n: int = 20,
) -> list[ContentItem]:
    seen = load_seen_topics(seen_file)
    filtered = [item for item in items if not is_duplicate(item.title, seen)]
    for item in filtered:
        r = recency_score(item.timestamp)
        e = engagement_score(item.likes, item.shares, item.comments)
        v = relevance_score(item.title, item.body)
        item.score = round((r * 0.3) + (e * 0.3) + (v * 0.4), 4)
    return sorted(filtered, key=lambda x: x.score, reverse=True)[:top_n]
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_intelligence/test_ranker.py -v
```

Expected: All 13 tests PASS

- [ ] **Step 5: Commit**

```bash
git add engines/intelligence/ranker.py tests/test_intelligence/test_ranker.py
git commit -m "feat: ranker with recency, engagement, relevance scoring and duplicate suppression"
```

---

### Task 6: Pipeline Integration + trends.json Writer

**Files:**
- Modify: `brg_social_agent/engines/intelligence/scraper.py` (add `scrape_all()`)
- Modify: `brg_social_agent/engines/intelligence/__init__.py` (add `run_intelligence_pipeline()`)
- Create: `brg_social_agent/main.py` (Phase 1 entry point)
- Test: `brg_social_agent/tests/test_intelligence/test_pipeline.py`

**Interfaces:**
- Consumes: all prior tasks
- Produces:
  - `scrape_all(config: Config) -> list[ContentItem]` — internal to pipeline
  - `run_intelligence_pipeline(config: Config) -> list[dict]` — called by `main.py`; returns the written items as list of dicts
  - `data/trends.json` with schema: `{ "generated_at": ISO string, "items": [ ContentItem.to_dict(), ... ] }`

- [ ] **Step 1: Write the failing pipeline test**

```python
# brg_social_agent/tests/test_intelligence/test_pipeline.py
import json
import os
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from config import Config
from engines.intelligence import run_intelligence_pipeline
from engines.intelligence.scraper import ContentItem


def _make_config(tmp_path) -> Config:
    config = Config.__new__(Config)
    config.anthropic_api_key = "test"
    config.reddit_client_id = "test"
    config.reddit_client_secret = "test"
    config.reddit_user_agent = "test"
    config.brand_primary_color = "#1A1A2E"
    config.brand_accent_color = "#E94560"
    config.brand_font_family = "Inter"
    config.logo_path = "assets/logo.svg"
    config.headshot_path = "assets/headshot.jpg"
    config.trends_file = str(tmp_path / "trends.json")
    config.seen_topics_file = str(tmp_path / "seen_topics.json")
    config.queue_dir = str(tmp_path / "queue")
    config.posted_dir = str(tmp_path / "posted")
    config.analytics_dir = str(tmp_path / "analytics")
    config.errors_dir = str(tmp_path / "errors")
    config.logs_dir = str(tmp_path / "logs")
    return config


def _make_items(n: int) -> list[ContentItem]:
    return [
        ContentItem(
            title=f"Leadership growth strategy {i}",
            body="mindset accountability coaching business",
            url=f"https://example.com/{i}",
            source="Test",
            timestamp=datetime.now(timezone.utc),
            likes=100 + i,
            comments=20,
        )
        for i in range(n)
    ]


def test_pipeline_writes_trends_json(tmp_path):
    config = _make_config(tmp_path)
    with patch("engines.intelligence.scrape_all", return_value=_make_items(5)):
        result = run_intelligence_pipeline(config)
    assert os.path.exists(config.trends_file)
    with open(config.trends_file) as f:
        data = json.load(f)
    assert "generated_at" in data
    assert "items" in data
    assert len(data["items"]) == 5


def test_pipeline_returns_list_of_dicts(tmp_path):
    config = _make_config(tmp_path)
    with patch("engines.intelligence.scrape_all", return_value=_make_items(3)):
        result = run_intelligence_pipeline(config)
    assert isinstance(result, list)
    assert all(isinstance(item, dict) for item in result)
    assert result[0]["title"].startswith("Leadership")


def test_pipeline_caps_output_at_20_items(tmp_path):
    config = _make_config(tmp_path)
    with patch("engines.intelligence.scrape_all", return_value=_make_items(30)):
        result = run_intelligence_pipeline(config)
    assert len(result) <= 20


def test_pipeline_marks_topics_seen(tmp_path):
    import json
    config = _make_config(tmp_path)
    with patch("engines.intelligence.scrape_all", return_value=_make_items(3)):
        run_intelligence_pipeline(config)
    assert os.path.exists(config.seen_topics_file)
    with open(config.seen_topics_file) as f:
        seen = json.load(f)
    assert len(seen) == 3
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_intelligence/test_pipeline.py -v
```

Expected: FAIL — `ImportError: cannot import name 'run_intelligence_pipeline'`

- [ ] **Step 3: Add scrape_all() to scraper.py**

Add these imports at the top of `engines/intelligence/scraper.py` (after existing imports):

```python
import praw
from config import Config
from .sources import SOURCES, SourceType
```

Add this function after `scrape_reddit()`:

```python
def scrape_all(config: Config) -> list["ContentItem"]:
    reddit = praw.Reddit(
        client_id=config.reddit_client_id,
        client_secret=config.reddit_client_secret,
        user_agent=config.reddit_user_agent,
    )
    items: list[ContentItem] = []
    for source in SOURCES:
        if source.type == SourceType.RSS:
            items.extend(scrape_rss(source))
        elif source.type == SourceType.REDDIT:
            items.extend(scrape_reddit(source, reddit))
        # SourceType.YOUTUBE, SourceType.TRENDS, and Playwright-based sources
        # (LinkedIn, competitor accounts) are implemented in Phase 1 Extension — see note below.
    return items
```

- [ ] **Step 4: Populate engines/intelligence/__init__.py**

```python
# brg_social_agent/engines/intelligence/__init__.py
import json
import os
from datetime import datetime, timezone

from config import Config
from .scraper import scrape_all
from .ranker import rank, mark_seen, load_seen_topics


def run_intelligence_pipeline(config: Config) -> list[dict]:
    """Scrape all sources, rank, write top 20 to trends.json. Returns items as list of dicts."""
    raw_items = scrape_all(config)
    top_items = rank(raw_items, config.seen_topics_file)

    os.makedirs(os.path.dirname(config.trends_file), exist_ok=True)
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "items": [item.to_dict() for item in top_items],
    }
    with open(config.trends_file, "w") as f:
        json.dump(output, f, indent=2)

    seen = load_seen_topics(config.seen_topics_file)
    for item in top_items:
        mark_seen(item.title, seen, config.seen_topics_file)

    return output["items"]
```

- [ ] **Step 5: Create main.py (Phase 1 entry point)**

```python
# brg_social_agent/main.py
import logging
from config import load_config
from engines.intelligence import run_intelligence_pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def main():
    config = load_config()
    log.info("Starting BRG Social Media Agent — Phase 1: Content Intelligence")
    items = run_intelligence_pipeline(config)
    log.info(f"Pipeline complete. {len(items)} trending topics written to {config.trends_file}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run all tests**

```bash
pytest tests/ -v
```

Expected: All tests PASS (config + sources + scraper + ranker + pipeline)

- [ ] **Step 7: Run the pipeline manually to verify end-to-end output**

Copy `.env.example` to `.env` and fill in your Reddit API credentials (Anthropic key not needed yet for Phase 1).

```bash
cp .env.example .env
# edit .env — add REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET
python main.py
```

Expected output:
```
2026-06-18 13:00:00 INFO Starting BRG Social Media Agent — Phase 1: Content Intelligence
2026-06-18 13:00:12 INFO Pipeline complete. 20 trending topics written to data/trends.json
```

Verify `data/trends.json` exists and contains 20 items with titles, bodies, scores, and timestamps.

- [ ] **Step 8: Commit**

```bash
git add engines/intelligence/__init__.py engines/intelligence/scraper.py \
        tests/test_intelligence/test_pipeline.py main.py
git commit -m "feat: Phase 1 pipeline — scrape, rank, write trends.json"
```

---

---

## Phase 1 Extension: Remaining Source Types

The spec defines 7 source types. RSS and Reddit are implemented above. The remaining 5 are intentionally deferred because they each require additional credentials or browser infrastructure that adds setup friction before you have a working pipeline. Implement these after Task 6 is running cleanly:

| Source | Requires | Implementation note |
|--------|---------|---------------------|
| YouTube transcripts | YouTube Data API v3 key | `youtube-transcript-api` — given channel IDs, fetch latest video transcripts |
| Google Trends | No extra credentials | `pytrends` — query leadership/coaching keywords, return rising topics |
| Podcast RSS | No extra credentials | Already handled by `scrape_rss()` — add podcast RSS URLs to `SOURCES` |
| LinkedIn trending posts | Playwright headless browser | Scrape public hashtag pages; no login required for public content |
| Competitor accounts | Playwright headless browser | Scrape public profile post text from 10–20 defined handles |

Add each as a new `elif source.type == SourceType.X:` branch in `scrape_all()` and a corresponding test.

---

## Phase 1 Done ✓

At this point you have:
- A working `python main.py` that scrapes 6+ sources, ranks by recency + engagement + relevance, suppresses 14-day duplicates, and writes `data/trends.json`
- 100% of public functions covered by passing tests
- A clean foundation for Phase 2 (Content Generation Engine) to consume `data/trends.json`

**Next:** When ready to implement Phase 2, ask for the `2026-06-18-brg-social-media-agent-phase2.md` plan.
