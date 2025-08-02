import pytest
from unittest.mock import Mock, MagicMock
from uuid import uuid4

from media_manager.plugins.music.plugin import MusicPlugin
from media_manager.plugins.music.service import MusicPluginService
from media_manager.plugins.music.repository import MusicPluginRepository
from media_manager.plugins.base.schemas import MediaPluginConfig


@pytest.fixture
def music_plugin():
    """Create a MusicPlugin instance for testing"""
    return MusicPlugin()


@pytest.fixture
def mock_session():
    """Create a mock database session"""
    return Mock()


def test_music_plugin_info(music_plugin):
    """Test that plugin info is correctly configured"""
    info = music_plugin.plugin_info
    
    assert info.name == "music"
    assert info.display_name == "Music"
    assert info.version == "1.0.0"
    assert info.media_type == "music"
    assert ".mp3" in info.supported_extensions
    assert ".flac" in info.supported_extensions
    assert "musicbrainz" in info.metadata_providers


def test_music_plugin_media_model_class(music_plugin):
    """Test that the correct model class is returned"""
    from media_manager.plugins.music.models import Artist
    
    model_class = music_plugin.media_model_class
    assert model_class == Artist


def test_music_plugin_router(music_plugin):
    """Test that router is returned"""
    router = music_plugin.router
    assert router is not None


def test_music_plugin_get_repository(music_plugin, mock_session):
    """Test getting repository instance"""
    repository = music_plugin.get_repository(mock_session)
    
    assert isinstance(repository, MusicPluginRepository)
    assert repository.session == mock_session


def test_music_plugin_get_service(music_plugin, mock_session):
    """Test getting service instance"""
    service = music_plugin.get_service(session=mock_session)
    
    assert isinstance(service, MusicPluginService)
    assert service.repository is not None


def test_music_plugin_get_service_no_session(music_plugin):
    """Test that getting service without session raises error"""
    with pytest.raises(ValueError, match="Session dependency is required"):
        music_plugin.get_service()


def test_music_plugin_get_database_models(music_plugin):
    """Test getting database models"""
    from media_manager.plugins.music.models import Artist, Album, Track, AlbumFile, AlbumRequest
    
    models = music_plugin.get_database_models()
    
    assert Artist in models
    assert Album in models
    assert Track in models
    assert AlbumFile in models
    assert AlbumRequest in models


def test_music_plugin_validate_config_valid(music_plugin):
    """Test validating a valid configuration"""
    config = MediaPluginConfig(
        enabled=True,
        libraries=[
            {"name": "Music", "path": "/data/music", "enabled": True}
        ]
    )
    
    assert music_plugin.validate_config(config) is True


def test_music_plugin_validate_config_no_libraries(music_plugin):
    """Test validating configuration with no libraries"""
    config = MediaPluginConfig(enabled=True, libraries=[])
    
    assert music_plugin.validate_config(config) is False


def test_music_plugin_validate_config_library_no_path(music_plugin):
    """Test validating configuration with library missing path"""
    config = MediaPluginConfig(
        enabled=True,
        libraries=[
            {"name": "Music", "path": "", "enabled": True}
        ]
    )
    
    assert music_plugin.validate_config(config) is False


def test_music_plugin_lifecycle_methods(music_plugin):
    """Test plugin lifecycle methods"""
    # These should not raise exceptions
    music_plugin.on_startup()
    music_plugin.on_shutdown()


@pytest.fixture
def mock_repository():
    """Create a mock repository for service testing"""
    repository = Mock(spec=MusicPluginRepository)
    repository.get_downloadable_requests.return_value = []
    repository.get_artist_by_id.return_value = None
    repository.get_artists.return_value = []
    return repository


def test_music_service_get_plugin_info():
    """Test getting plugin info from service"""
    mock_repo = Mock()
    service = MusicPluginService(repository=mock_repo)
    
    info = service.get_plugin_info()
    
    assert info.name == "music"
    assert info.display_name == "Music"
    assert info.media_type == "music"


def test_music_service_search_metadata():
    """Test searching metadata (placeholder implementation)"""
    mock_repo = Mock()
    service = MusicPluginService(repository=mock_repo)
    
    # Currently returns empty list (placeholder)
    results = service.search_metadata("test query")
    assert results == []


def test_music_service_create_from_metadata():
    """Test creating from metadata (placeholder implementation)"""
    mock_repo = Mock()
    service = MusicPluginService(repository=mock_repo)
    
    # Currently returns None (placeholder)
    result = service.create_from_metadata(Mock())
    assert result is None


def test_music_service_auto_download_approved_requests(mock_repository):
    """Test auto download approved requests"""
    service = MusicPluginService(repository=mock_repository)
    
    # Should not raise an exception
    service.auto_download_approved_requests()
    
    mock_repository.get_downloadable_requests.assert_called_once()


def test_music_service_import_downloaded_files(mock_repository):
    """Test import downloaded files"""
    service = MusicPluginService(repository=mock_repository)
    
    # Should not raise an exception (placeholder implementation)
    service.import_downloaded_files()


def test_music_service_delegate_methods(mock_repository):
    """Test that service methods delegate to repository"""
    artist_id = uuid4()
    service = MusicPluginService(repository=mock_repository)
    
    # Test get_artist_by_id delegation
    service.get_artist_by_id(artist_id)
    mock_repository.get_artist_by_id.assert_called_with(artist_id)
    
    # Test get_artists delegation - check positional args
    service.get_artists(limit=50, offset=10)
    mock_repository.get_artists.assert_called_with(50, 10)