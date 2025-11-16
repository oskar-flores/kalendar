"""Tests for FileSystemCache implementation."""

import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from kalendar.domain.models.event import CalendarEvent
from kalendar.infrastructure.storage.filesystem_cache import FileSystemCache


class TestFileSystemCacheInitialization:
    """Test cache directory initialization and permission handling."""

    def test_creates_cache_directory_if_not_exists(self):
        """Cache should create directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "new_cache_dir"
            assert not cache_dir.exists()

            cache = FileSystemCache(str(cache_dir))

            assert cache_dir.exists()
            assert cache_dir.is_dir()

    def test_uses_existing_cache_directory(self):
        """Cache should use existing directory without error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "existing_cache"
            cache_dir.mkdir()

            cache = FileSystemCache(str(cache_dir))

            assert cache.cache_dir == cache_dir
            assert cache_dir.exists()

    def test_creates_nested_cache_directory(self):
        """Cache should create nested directories with parents=True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "parent" / "child" / "cache"
            assert not cache_dir.exists()

            cache = FileSystemCache(str(cache_dir))

            assert cache_dir.exists()
            assert cache_dir.is_dir()

    def test_fallback_to_user_cache_on_permission_error(self):
        """Cache should fall back to ~/.cache/kalendar on permission error."""
        # Mock mkdir to raise PermissionError on first call, succeed on second
        original_mkdir = Path.mkdir
        call_count = {"count": 0}

        def mock_mkdir(self, parents=False, exist_ok=False):
            call_count["count"] += 1
            if call_count["count"] == 1:
                # First call (to /var/cache/kalendar) fails
                raise PermissionError("[Errno 13] Permission denied: '/var/cache/kalendar'")
            else:
                # Second call (to ~/.cache/kalendar) succeeds
                original_mkdir(self, parents=parents, exist_ok=exist_ok)

        with patch.object(Path, "mkdir", mock_mkdir):
            cache = FileSystemCache("/var/cache/kalendar")

            # Should fall back to user cache directory
            expected_fallback = Path.home() / ".cache" / "kalendar"
            assert cache.cache_dir == expected_fallback

    def test_uses_default_cache_dir_if_not_specified(self):
        """Cache should use ./cache as default directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import os
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                cache = FileSystemCache()
                assert cache.cache_dir == Path("./cache")
            finally:
                os.chdir(original_cwd)


class TestFileSystemCacheSaveAndLoad:
    """Test saving and loading events from cache."""

    @pytest.fixture
    def cache(self):
        """Create cache in temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield FileSystemCache(tmpdir)

    @pytest.fixture
    def sample_events(self):
        """Create sample calendar events."""
        return [
            CalendarEvent(
                id="event-1",
                calendar_source_id="cal-1",
                title="Test Event 1",
                start_datetime=datetime(2025, 11, 16, 10, 0, tzinfo=timezone.utc),
                end_datetime=datetime(2025, 11, 16, 11, 0, tzinfo=timezone.utc),
                is_all_day=False,
                location="Office",
                description="Test description",
                is_recurring=False,
                recurrence_id=None,
            ),
            CalendarEvent(
                id="event-2",
                calendar_source_id="cal-1",
                title="Test Event 2",
                start_datetime=datetime(2025, 11, 17, 14, 0, tzinfo=timezone.utc),
                end_datetime=datetime(2025, 11, 17, 15, 30, tzinfo=timezone.utc),
                is_all_day=False,
                location=None,
                description=None,
                is_recurring=True,
                recurrence_id="rec-123",
            ),
        ]

    def test_save_events_creates_cache_file(self, cache, sample_events):
        """Saving events should create a JSON cache file."""
        source_id = "test-source"
        timestamp = datetime.now(timezone.utc)

        cache.save_events(source_id, sample_events, timestamp)

        cache_file = cache.cache_dir / f"{source_id}.json"
        assert cache_file.exists()

    def test_save_events_stores_correct_data(self, cache, sample_events):
        """Saved cache file should contain correct event data."""
        source_id = "test-source"
        timestamp = datetime.now(timezone.utc)

        cache.save_events(source_id, sample_events, timestamp)

        cache_file = cache.cache_dir / f"{source_id}.json"
        with open(cache_file) as f:
            data = json.load(f)

        assert data["source_id"] == source_id
        assert data["last_sync"] == timestamp.isoformat()
        assert len(data["events"]) == 2
        assert data["events"][0]["title"] == "Test Event 1"
        assert data["events"][1]["title"] == "Test Event 2"

    def test_load_events_returns_none_for_missing_cache(self, cache):
        """Loading non-existent cache should return None."""
        result = cache.load_events("non-existent-source")
        assert result is None

    def test_load_events_returns_saved_events(self, cache, sample_events):
        """Loading should return previously saved events."""
        source_id = "test-source"
        timestamp = datetime.now(timezone.utc)

        cache.save_events(source_id, sample_events, timestamp)
        loaded_events = cache.load_events(source_id)

        assert loaded_events is not None
        assert len(loaded_events) == 2
        assert loaded_events[0].title == "Test Event 1"
        assert loaded_events[0].location == "Office"
        assert loaded_events[1].title == "Test Event 2"
        assert loaded_events[1].is_recurring is True

    def test_load_events_handles_corrupted_json(self, cache):
        """Loading corrupted cache file should return None."""
        source_id = "corrupted-source"
        cache_file = cache.cache_dir / f"{source_id}.json"

        # Write invalid JSON
        with open(cache_file, "w") as f:
            f.write("{ invalid json }")

        result = cache.load_events(source_id)
        assert result is None

    def test_load_events_handles_missing_keys(self, cache):
        """Loading cache with missing keys should return None."""
        source_id = "invalid-source"
        cache_file = cache.cache_dir / f"{source_id}.json"

        # Write JSON missing required keys
        with open(cache_file, "w") as f:
            json.dump({"source_id": source_id}, f)

        result = cache.load_events(source_id)
        assert result is None


class TestFileSystemCacheValidation:
    """Test cache validation and expiration."""

    @pytest.fixture
    def cache(self):
        """Create cache in temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield FileSystemCache(tmpdir)

    def test_is_cache_valid_returns_false_for_missing_cache(self, cache):
        """Non-existent cache should not be valid."""
        assert cache.is_cache_valid("non-existent") is False

    def test_is_cache_valid_returns_true_for_fresh_cache(self, cache):
        """Recently saved cache should be valid."""
        source_id = "test-source"
        events = [
            CalendarEvent(
                id="event-1",
                calendar_source_id="cal-1",
                title="Test",
                start_datetime=datetime.now(timezone.utc),
                end_datetime=datetime.now(timezone.utc) + timedelta(hours=1),
                is_all_day=False,
            )
        ]
        timestamp = datetime.now(timezone.utc)

        cache.save_events(source_id, events, timestamp)

        assert cache.is_cache_valid(source_id, max_age_hours=24) is True

    def test_is_cache_valid_returns_false_for_expired_cache(self, cache):
        """Old cache should be invalid."""
        source_id = "test-source"
        cache_file = cache.cache_dir / f"{source_id}.json"

        # Create cache with old timestamp
        old_timestamp = datetime.now(timezone.utc) - timedelta(hours=48)
        data = {
            "source_id": source_id,
            "last_sync": old_timestamp.isoformat(),
            "events": [],
        }

        with open(cache_file, "w") as f:
            json.dump(data, f)

        assert cache.is_cache_valid(source_id, max_age_hours=24) is False

    def test_is_cache_valid_respects_max_age_parameter(self, cache):
        """Cache validation should respect custom max_age_hours."""
        source_id = "test-source"
        cache_file = cache.cache_dir / f"{source_id}.json"

        # Create cache 2 hours old
        timestamp = datetime.now(timezone.utc) - timedelta(hours=2)
        data = {
            "source_id": source_id,
            "last_sync": timestamp.isoformat(),
            "events": [],
        }

        with open(cache_file, "w") as f:
            json.dump(data, f)

        # Should be valid with max_age=3 hours
        assert cache.is_cache_valid(source_id, max_age_hours=3) is True

        # Should be invalid with max_age=1 hour
        assert cache.is_cache_valid(source_id, max_age_hours=1) is False

    def test_is_cache_valid_handles_corrupted_cache(self, cache):
        """Corrupted cache should be invalid."""
        source_id = "corrupted-source"
        cache_file = cache.cache_dir / f"{source_id}.json"

        with open(cache_file, "w") as f:
            f.write("invalid json")

        assert cache.is_cache_valid(source_id) is False


class TestFileSystemCacheClear:
    """Test cache clearing functionality."""

    @pytest.fixture
    def cache(self):
        """Create cache in temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield FileSystemCache(tmpdir)

    @pytest.fixture
    def sample_event(self):
        """Create a sample event."""
        return CalendarEvent(
            id="event-1",
            calendar_source_id="cal-1",
            title="Test",
            start_datetime=datetime.now(timezone.utc),
            end_datetime=datetime.now(timezone.utc) + timedelta(hours=1),
            is_all_day=False,
        )

    def test_clear_cache_removes_specific_source(self, cache, sample_event):
        """Clearing specific source should remove only that cache file."""
        # Create cache for two sources
        cache.save_events("source-1", [sample_event], datetime.now(timezone.utc))
        cache.save_events("source-2", [sample_event], datetime.now(timezone.utc))

        cache_file_1 = cache.cache_dir / "source-1.json"
        cache_file_2 = cache.cache_dir / "source-2.json"

        assert cache_file_1.exists()
        assert cache_file_2.exists()

        # Clear only source-1
        cache.clear_cache("source-1")

        assert not cache_file_1.exists()
        assert cache_file_2.exists()

    def test_clear_cache_handles_non_existent_source(self, cache):
        """Clearing non-existent source should not raise error."""
        cache.clear_cache("non-existent")  # Should not raise

    def test_clear_cache_removes_all_sources_when_no_id_specified(self, cache, sample_event):
        """Clearing without source_id should remove all cache files."""
        # Create cache for multiple sources
        cache.save_events("source-1", [sample_event], datetime.now(timezone.utc))
        cache.save_events("source-2", [sample_event], datetime.now(timezone.utc))
        cache.save_events("source-3", [sample_event], datetime.now(timezone.utc))

        # Clear all
        cache.clear_cache(None)

        # All cache files should be gone
        cache_files = list(cache.cache_dir.glob("*.json"))
        assert len(cache_files) == 0


class TestFileSystemCacheEventSerialization:
    """Test event serialization/deserialization."""

    @pytest.fixture
    def cache(self):
        """Create cache in temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield FileSystemCache(tmpdir)

    def test_serializes_all_event_fields(self, cache):
        """All event fields should be serialized correctly."""
        event = CalendarEvent(
            id="event-123",
            calendar_source_id="cal-456",
            title="Important Meeting",
            start_datetime=datetime(2025, 11, 16, 10, 0, tzinfo=timezone.utc),
            end_datetime=datetime(2025, 11, 16, 11, 0, tzinfo=timezone.utc),
            is_all_day=False,
            location="Conference Room A",
            description="Quarterly planning meeting",
            is_recurring=True,
            recurrence_id="rec-789",
        )

        cache.save_events("test", [event], datetime.now(timezone.utc))
        loaded_events = cache.load_events("test")

        assert len(loaded_events) == 1
        loaded = loaded_events[0]

        assert loaded.id == "event-123"
        assert loaded.calendar_source_id == "cal-456"
        assert loaded.title == "Important Meeting"
        assert loaded.start_datetime == datetime(2025, 11, 16, 10, 0, tzinfo=timezone.utc)
        assert loaded.end_datetime == datetime(2025, 11, 16, 11, 0, tzinfo=timezone.utc)
        assert loaded.is_all_day is False
        assert loaded.location == "Conference Room A"
        assert loaded.description == "Quarterly planning meeting"
        assert loaded.is_recurring is True
        assert loaded.recurrence_id == "rec-789"

    def test_handles_optional_fields(self, cache):
        """Optional fields (location, description, etc.) should serialize as None."""
        event = CalendarEvent(
            id="event-1",
            calendar_source_id="cal-1",
            title="Simple Event",
            start_datetime=datetime(2025, 11, 16, 10, 0, tzinfo=timezone.utc),
            end_datetime=datetime(2025, 11, 16, 11, 0, tzinfo=timezone.utc),
            is_all_day=False,
            location=None,
            description=None,
            is_recurring=False,
            recurrence_id=None,
        )

        cache.save_events("test", [event], datetime.now(timezone.utc))
        loaded_events = cache.load_events("test")

        loaded = loaded_events[0]
        assert loaded.location is None
        assert loaded.description is None
        assert loaded.recurrence_id is None
