"""
Test Scanner Configuration
===========================

Tests for scan configuration loading and validation.
"""

import pytest
import json
from pathlib import Path


@pytest.mark.scanner
@pytest.mark.unit
class TestConfigurationLoading:
    """Test configuration file loading."""
    
    def test_sample_config_structure(self, sample_config):
        """Test sample config has required fields."""
        assert 'audit_name' in sample_config
        assert 'headless' in sample_config
        assert 'browser' in sample_config
        assert 'viewport_sizes' in sample_config
    
    def test_config_has_valid_audit_name(self, sample_config):
        """Test config has a valid audit name."""
        assert sample_config['audit_name']
        assert isinstance(sample_config['audit_name'], str)
        assert len(sample_config['audit_name']) > 0
    
    def test_config_has_valid_browser_setting(self, sample_config):
        """Test browser setting is valid."""
        assert sample_config['browser'] in ['chrome', 'chromium', 'firefox']
    
    def test_config_viewport_sizes_valid(self, sample_config):
        """Test viewport sizes are properly formatted."""
        viewports = sample_config['viewport_sizes']
        
        assert isinstance(viewports, dict)
        
        for size_name, size_config in viewports.items():
            assert 'width' in size_config
            assert 'height' in size_config
            assert isinstance(size_config['width'], int)
            assert isinstance(size_config['height'], int)
            assert size_config['width'] > 0
            assert size_config['height'] > 0


@pytest.mark.scanner
@pytest.mark.unit
class TestConfigurationValidation:
    """Test configuration validation logic."""
    
    def test_thread_count_is_positive(self, sample_config):
        """Test thread count is a positive integer."""
        if 'thread_count' in sample_config:
            assert sample_config['thread_count'] > 0
            assert isinstance(sample_config['thread_count'], int)
    
    def test_max_links_is_reasonable(self, sample_config):
        """Test max links per domain is reasonable."""
        if 'max_links_per_domain' in sample_config:
            assert sample_config['max_links_per_domain'] > 0
            assert sample_config['max_links_per_domain'] <= 1000  # Reasonable upper limit
    
    def test_headless_is_boolean(self, sample_config):
        """Test headless setting is boolean."""
        if 'headless' in sample_config:
            assert isinstance(sample_config['headless'], bool)


@pytest.mark.scanner
@pytest.mark.integration
class TestActualConfigFiles:
    """Test actual configuration files in the project."""
    
    def test_config_files_exist(self):
        """Test that config files exist in config directory."""
        config_dir = Path('config')
        
        if config_dir.exists():
            config_files = list(config_dir.glob('*.json'))
            assert len(config_files) > 0, "No config files found in config directory"
    
    def test_config_files_are_valid_json(self):
        """Test all config files contain valid JSON."""
        config_dir = Path('config')
        
        if config_dir.exists():
            for config_file in config_dir.glob('*.json'):
                with open(config_file, 'r') as f:
                    try:
                        config_data = json.load(f)
                        assert isinstance(config_data, dict)
                    except json.JSONDecodeError:
                        pytest.fail(f"Invalid JSON in {config_file}")
    
    def test_default_config_has_required_fields(self):
        """Test default config has all required fields."""
        config_file = Path('config/config_default.json')
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            required_fields = ['audit_name', 'browser', 'headless']
            for field in required_fields:
                assert field in config, f"Missing required field: {field}"


@pytest.mark.scanner
@pytest.mark.unit
class TestAuditPluginConfiguration:
    """Test audit plugin configuration."""
    
    def test_config_has_audit_plugins_section(self, sample_config):
        """Test config can define audit plugins."""
        # Sample config may or may not have this, so we just test structure if present
        if 'audit_plugins' in sample_config:
            plugins = sample_config['audit_plugins']
            assert isinstance(plugins, dict)
    
    def test_audit_plugin_has_required_fields(self):
        """Test audit plugin configuration structure."""
        plugin_config = {
            'axe_core_audit': {
                'class_name': 'AxeCoreAudit',
                'enabled': True
            }
        }
        
        for plugin_name, plugin_settings in plugin_config.items():
            assert 'class_name' in plugin_settings
            assert 'enabled' in plugin_settings
            assert isinstance(plugin_settings['enabled'], bool)
