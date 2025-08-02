from typing import Dict, Any, List
from pathlib import Path
from pydantic import BaseModel, Field

from media_manager.plugins.base.schemas import MediaPluginConfig


class LibraryConfig(BaseModel):
    """
    Configuration for a media library
    """
    name: str
    path: str
    enabled: bool = True
    settings: Dict[str, Any] = {}


class PluginSpecificConfig(MediaPluginConfig):
    """
    Extended plugin configuration with library management
    """
    libraries: List[LibraryConfig] = []
    
    # Plugin-specific settings
    auto_download: bool = True
    update_metadata_interval: str = "weekly"  # daily, weekly, monthly
    import_check_interval: str = "15min"  # 5min, 15min, 30min, hourly
    
    # Quality preferences
    preferred_quality: str = "1080p"
    minimum_quality: str = "720p"
    
    # File organization
    create_subdirectories: bool = True
    file_naming_pattern: str = ""  # Plugin-specific default


class MediaPluginsConfig(BaseModel):
    """
    Configuration for all media plugins
    """
    # Global media settings
    base_media_directory: Path = Path("/data/media")
    torrent_directory: Path = Path("/data/torrents")
    image_directory: Path = Path("/data/images")
    
    # Global plugin settings
    enable_auto_discovery: bool = True
    enable_background_tasks: bool = True
    
    # Per-plugin configuration
    tv: PluginSpecificConfig = Field(default_factory=lambda: PluginSpecificConfig(
        enabled=True,
        libraries=[
            LibraryConfig(name="TV Shows", path="/data/media/tv"),
            LibraryConfig(name="Anime", path="/data/media/anime", enabled=False)
        ],
        file_naming_pattern="{show_name}/Season {season_number}/{show_name} - S{season_number:02d}E{episode_number:02d} - {episode_title}"
    ))
    
    movies: PluginSpecificConfig = Field(default_factory=lambda: PluginSpecificConfig(
        enabled=True,
        libraries=[
            LibraryConfig(name="Movies", path="/data/media/movies"),
            LibraryConfig(name="Documentaries", path="/data/media/documentaries", enabled=False)
        ],
        file_naming_pattern="{movie_name} ({year})"
    ))
    
    music: PluginSpecificConfig = Field(default_factory=lambda: PluginSpecificConfig(
        enabled=False,
        libraries=[
            LibraryConfig(name="Music", path="/data/media/music")
        ],
        file_naming_pattern="{artist}/{album}/{track_number:02d} - {track_title}"
    ))
    
    audiobooks: PluginSpecificConfig = Field(default_factory=lambda: PluginSpecificConfig(
        enabled=False,
        libraries=[
            LibraryConfig(name="Audiobooks", path="/data/media/audiobooks")
        ],
        file_naming_pattern="{author}/{book_title}"
    ))
    
    ebooks: PluginSpecificConfig = Field(default_factory=lambda: PluginSpecificConfig(
        enabled=False,
        libraries=[
            LibraryConfig(name="Ebooks", path="/data/media/ebooks")
        ],
        file_naming_pattern="{author}/{book_title}"
    ))
    
    def get_plugin_config(self, plugin_name: str) -> PluginSpecificConfig:
        """
        Get configuration for a specific plugin
        """
        return getattr(self, plugin_name, PluginSpecificConfig())
    
    def get_enabled_plugins(self) -> List[str]:
        """
        Get list of enabled plugin names
        """
        enabled = []
        for field_name, field_info in self.model_fields.items():
            if field_name.startswith(('base_', 'enable_', 'torrent_', 'image_')):
                continue
            config = getattr(self, field_name)
            if isinstance(config, PluginSpecificConfig) and config.enabled:
                enabled.append(field_name)
        return enabled
    
    def get_all_library_paths(self) -> Dict[str, List[str]]:
        """
        Get all library paths organized by plugin
        """
        paths = {}
        for field_name, field_info in self.model_fields.items():
            if field_name.startswith(('base_', 'enable_', 'torrent_', 'image_')):
                continue
            config = getattr(self, field_name)
            if isinstance(config, PluginSpecificConfig):
                paths[field_name] = [lib.path for lib in config.libraries if lib.enabled]
        return paths