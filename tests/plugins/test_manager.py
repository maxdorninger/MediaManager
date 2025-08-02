import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from media_manager.plugins.manager import PluginManager
from media_manager.plugins.base.plugin import BaseMediaPlugin
from media_manager.plugins.base.schemas import MediaPluginInfo, MediaPluginConfig


class MockPlugin(BaseMediaPlugin):
    """Mock plugin for testing"""
    
    @property
    def plugin_info(self) -> MediaPluginInfo:
        return MediaPluginInfo(
            name="test",
            display_name="Test Plugin",
            version="1.0.0",
            description="A test plugin",
            media_type="test",
            supported_extensions=[".test"],
            metadata_providers=["test_provider"]
        )
    
    @property
    def media_model_class(self):
        return Mock
    
    @property
    def router(self):
        return Mock()
    
    def get_service(self, **dependencies):
        return Mock()
    
    def get_repository(self, session, **kwargs):
        return Mock()
    
    def get_database_models(self):
        return [Mock]
    
    def validate_config(self, config: MediaPluginConfig) -> bool:
        return True


@pytest.fixture
def plugin_manager():
    """Create a fresh plugin manager for each test"""
    return PluginManager()


def test_plugin_manager_initialization(plugin_manager):
    """Test plugin manager initializes correctly"""
    assert plugin_manager.plugins == {}
    assert plugin_manager.plugin_configs == {}
    assert not plugin_manager.initialized


def test_discover_plugins_empty_directory(plugin_manager):
    """Test discovering plugins with no plugins directory"""
    with patch('pathlib.Path.exists', return_value=False):
        plugins = plugin_manager.discover_plugins()
        assert plugins == []


def test_load_plugin_success(plugin_manager):
    """Test successfully loading a plugin"""
    with patch('importlib.import_module') as mock_import:
        # Create a mock module with our MockPlugin
        mock_module = Mock()
        mock_module.MockPlugin = MockPlugin
        mock_import.return_value = mock_module
        
        plugin = plugin_manager.load_plugin("test")
        
        assert plugin is not None
        assert isinstance(plugin, MockPlugin)
        assert plugin.plugin_info.name == "test"


def test_load_plugin_no_plugin_class(plugin_manager):
    """Test loading plugin with no plugin class"""
    with patch('importlib.import_module') as mock_import:
        # Create a mock module without a plugin class
        mock_module = Mock()
        del mock_module.MockPlugin  # Ensure no plugin class exists
        mock_import.return_value = mock_module
        
        plugin = plugin_manager.load_plugin("test")
        
        assert plugin is None


def test_load_plugin_import_error(plugin_manager):
    """Test loading plugin with import error"""
    with patch('importlib.import_module', side_effect=ImportError("Module not found")):
        plugin = plugin_manager.load_plugin("test")
        assert plugin is None


def test_load_all_plugins_with_config(plugin_manager):
    """Test loading all plugins with configuration"""
    test_config = MediaPluginConfig(enabled=True)
    configs = {"test": test_config}
    
    with patch.object(plugin_manager, 'discover_plugins', return_value=["test"]):
        with patch.object(plugin_manager, 'load_plugin', return_value=MockPlugin()) as mock_load:
            plugin_manager.load_all_plugins(configs)
            
            mock_load.assert_called_once_with("test")
            assert len(plugin_manager.plugins) == 1
            assert "test" in plugin_manager.plugins
            assert plugin_manager.initialized


def test_load_all_plugins_disabled_plugin(plugin_manager):
    """Test that disabled plugins are not loaded"""
    test_config = MediaPluginConfig(enabled=False)
    configs = {"test": test_config}
    
    with patch.object(plugin_manager, 'discover_plugins', return_value=["test"]):
        with patch.object(plugin_manager, 'load_plugin') as mock_load:
            plugin_manager.load_all_plugins(configs)
            
            mock_load.assert_not_called()
            assert len(plugin_manager.plugins) == 0


def test_get_plugin(plugin_manager):
    """Test getting a specific plugin"""
    mock_plugin = MockPlugin()
    plugin_manager.plugins["test"] = mock_plugin
    
    result = plugin_manager.get_plugin("test")
    assert result == mock_plugin
    
    result = plugin_manager.get_plugin("nonexistent")
    assert result is None


def test_get_all_plugins(plugin_manager):
    """Test getting all plugins"""
    mock_plugin = MockPlugin()
    plugin_manager.plugins["test"] = mock_plugin
    
    result = plugin_manager.get_all_plugins()
    assert result == {"test": mock_plugin}
    assert result is not plugin_manager.plugins  # Should return a copy


def test_get_plugin_by_media_type(plugin_manager):
    """Test getting plugin by media type"""
    mock_plugin = MockPlugin()
    plugin_manager.plugins["test"] = mock_plugin
    
    result = plugin_manager.get_plugin_by_media_type("test")
    assert result == mock_plugin
    
    result = plugin_manager.get_plugin_by_media_type("nonexistent")
    assert result is None


def test_get_all_routers(plugin_manager):
    """Test getting all plugin routers"""
    mock_plugin = MockPlugin()
    plugin_manager.plugins["test"] = mock_plugin
    
    routers = plugin_manager.get_all_routers()
    assert len(routers) == 1
    assert routers[0][0] == "test"  # plugin name
    assert routers[0][1] is not None  # router object


def test_get_all_database_models(plugin_manager):
    """Test getting all database models from plugins"""
    mock_plugin = MockPlugin()
    plugin_manager.plugins["test"] = mock_plugin
    
    models = plugin_manager.get_all_database_models()
    assert len(models) == 1
    assert models[0] == Mock


def test_get_plugin_info_list(plugin_manager):
    """Test getting plugin info list"""
    mock_plugin = MockPlugin()
    plugin_manager.plugins["test"] = mock_plugin
    
    info_list = plugin_manager.get_plugin_info_list()
    assert len(info_list) == 1
    assert info_list[0].name == "test"
    assert info_list[0].display_name == "Test Plugin"


def test_shutdown_all_plugins(plugin_manager):
    """Test shutting down all plugins"""
    mock_plugin = MockPlugin()
    mock_plugin.on_shutdown = Mock()
    plugin_manager.plugins["test"] = mock_plugin
    plugin_manager._initialized = True
    
    plugin_manager.shutdown_all_plugins()
    
    mock_plugin.on_shutdown.assert_called_once()
    assert len(plugin_manager.plugins) == 0
    assert not plugin_manager.initialized


def test_shutdown_all_plugins_with_error(plugin_manager):
    """Test shutting down plugins when one raises an error"""
    mock_plugin1 = MockPlugin()
    mock_plugin1.on_shutdown = Mock(side_effect=Exception("Shutdown error"))
    
    mock_plugin2 = MockPlugin()
    mock_plugin2.on_shutdown = Mock()
    
    plugin_manager.plugins["test1"] = mock_plugin1
    plugin_manager.plugins["test2"] = mock_plugin2
    plugin_manager._initialized = True
    
    # Should not raise an exception despite plugin1 error
    plugin_manager.shutdown_all_plugins()
    
    mock_plugin1.on_shutdown.assert_called_once()
    mock_plugin2.on_shutdown.assert_called_once()
    assert len(plugin_manager.plugins) == 0