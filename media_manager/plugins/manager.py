import importlib
import logging
import pkgutil
from pathlib import Path
from typing import Dict, List, Type, Optional

from fastapi import APIRouter

from media_manager.plugins.base.plugin import BaseMediaPlugin
from media_manager.plugins.base.schemas import MediaPluginInfo, MediaPluginConfig

log = logging.getLogger(__name__)


class PluginManager:
    """
    Manages discovery, loading, and lifecycle of media plugins
    """
    
    def __init__(self):
        self.plugins: Dict[str, BaseMediaPlugin] = {}
        self.plugin_configs: Dict[str, MediaPluginConfig] = {}
        self._initialized = False
    
    def discover_plugins(self) -> List[str]:
        """
        Discover all available plugins in the plugins directory
        """
        plugins_dir = Path(__file__).parent
        plugin_names = []
        
        for finder, name, ispkg in pkgutil.iter_modules([str(plugins_dir)]):
            if ispkg and name not in ['base', '__pycache__']:
                # Check if the plugin directory contains a plugin.py file
                plugin_file = plugins_dir / name / "plugin.py"
                if plugin_file.exists():
                    plugin_names.append(name)
                    log.info(f"Discovered plugin: {name}")
        
        return plugin_names
    
    def load_plugin(self, plugin_name: str) -> Optional[BaseMediaPlugin]:
        """
        Load a specific plugin by name
        """
        try:
            # Import the plugin module
            module_name = f"media_manager.plugins.{plugin_name}.plugin"
            plugin_module = importlib.import_module(module_name)
            
            # Look for a class that inherits from BaseMediaPlugin
            plugin_class = None
            for attr_name in dir(plugin_module):
                attr = getattr(plugin_module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, BaseMediaPlugin) and 
                    attr != BaseMediaPlugin):
                    plugin_class = attr
                    break
            
            if plugin_class is None:
                log.error(f"No plugin class found in {module_name}")
                return None
            
            # Instantiate the plugin
            plugin_instance = plugin_class()
            
            # Validate plugin info
            info = plugin_instance.plugin_info
            if not isinstance(info, MediaPluginInfo):
                log.error(f"Plugin {plugin_name} has invalid plugin_info")
                return None
            
            log.info(f"Loaded plugin: {info.display_name} v{info.version}")
            return plugin_instance
            
        except Exception as e:
            log.error(f"Failed to load plugin {plugin_name}: {e}")
            return None
    
    def load_all_plugins(self, plugin_configs: Dict[str, MediaPluginConfig] = None) -> None:
        """
        Discover and load all available plugins
        """
        self.plugin_configs = plugin_configs or {}
        plugin_names = self.discover_plugins()
        
        for plugin_name in plugin_names:
            config = self.plugin_configs.get(plugin_name, MediaPluginConfig())
            
            if not config.enabled:
                log.info(f"Plugin {plugin_name} is disabled in configuration")
                continue
            
            plugin = self.load_plugin(plugin_name)
            if plugin:
                # Validate configuration
                if not plugin.validate_config(config):
                    log.error(f"Invalid configuration for plugin {plugin_name}")
                    continue
                
                self.plugins[plugin_name] = plugin
                plugin.on_startup()
                log.info(f"Plugin {plugin_name} started successfully")
        
        self._initialized = True
        log.info(f"Loaded {len(self.plugins)} plugins: {list(self.plugins.keys())}")
    
    def get_plugin(self, plugin_name: str) -> Optional[BaseMediaPlugin]:
        """
        Get a specific plugin by name
        """
        return self.plugins.get(plugin_name)
    
    def get_all_plugins(self) -> Dict[str, BaseMediaPlugin]:
        """
        Get all loaded plugins
        """
        return self.plugins.copy()
    
    def get_plugin_by_media_type(self, media_type: str) -> Optional[BaseMediaPlugin]:
        """
        Get plugin that handles a specific media type
        """
        for plugin in self.plugins.values():
            if plugin.plugin_info.media_type == media_type:
                return plugin
        return None
    
    def get_all_routers(self) -> List[tuple[str, APIRouter]]:
        """
        Get all plugin routers for FastAPI integration
        """
        routers = []
        for plugin_name, plugin in self.plugins.items():
            try:
                router = plugin.router
                if router:
                    routers.append((plugin_name, router))
            except Exception as e:
                log.error(f"Failed to get router for plugin {plugin_name}: {e}")
        return routers
    
    def get_all_database_models(self) -> List[Type]:
        """
        Get all database models from all plugins
        """
        models = []
        for plugin in self.plugins.values():
            try:
                plugin_models = plugin.get_database_models()
                models.extend(plugin_models)
            except Exception as e:
                log.error(f"Failed to get models for plugin {plugin.plugin_info.name}: {e}")
        return models
    
    def get_plugin_info_list(self) -> List[MediaPluginInfo]:
        """
        Get information about all loaded plugins
        """
        return [plugin.plugin_info for plugin in self.plugins.values()]
    
    def shutdown_all_plugins(self) -> None:
        """
        Shutdown all plugins
        """
        for plugin_name, plugin in self.plugins.items():
            try:
                plugin.on_shutdown()
                log.info(f"Plugin {plugin_name} shut down successfully")
            except Exception as e:
                log.error(f"Error shutting down plugin {plugin_name}: {e}")
        
        self.plugins.clear()
        self._initialized = False
    
    @property
    def initialized(self) -> bool:
        """
        Check if the plugin manager has been initialized
        """
        return self._initialized


# Global plugin manager instance
plugin_manager = PluginManager()