import json
import os
import sys
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class UIConfig:
    """UI configuration for environment differentiation."""
    header_color: str
    environment_badge: Optional[str]
    show_environment_indicator: bool
    window_title_suffix: str


@dataclass
class DeploymentConfig:
    """Deployment configuration for CI/CD."""
    server_host: str
    server_path: str
    ssh_key_secret: str
    admin_key_secret: str


@dataclass
class ProfileConfig:
    """Complete profile configuration."""
    environment: str
    api_url: str
    update_server_url: str
    database_suffix: str
    ui_config: UIConfig
    deployment: DeploymentConfig


class ProfileManager:
    """Manages environment-specific configuration profiles."""

    _instance = None
    _profile_config = None

    def __new__(cls):
        """Singleton pattern to ensure single instance."""
        if cls._instance is None:
            cls._instance = super(ProfileManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize profile manager."""
        if self._profile_config is None:
            self._profile_config = self._load_profile_configuration()
            logger.info(f"Profile Manager initialized for environment: {self.get_environment_name()}")

    def _load_profile_configuration(self) -> ProfileConfig:
        """Load profile configuration from embedded file or fallback to production."""
        try:
            # Try to load embedded profile first (for built applications)
            embedded_path = self._get_embedded_profile_path()
            if os.path.exists(embedded_path):
                logger.info(f"Loading embedded profile from: {embedded_path}")
                with open(embedded_path, 'r', encoding='utf-8') as f:
                    embedded_data = json.load(f)
                    return self._parse_profile_config(embedded_data["profile"])

            # Development fallback - load from profiles directory
            dev_profile_path = self._get_development_profile_path()
            if os.path.exists(dev_profile_path):
                logger.info(f"Loading development profile from: {dev_profile_path}")
                with open(dev_profile_path, 'r', encoding='utf-8') as f:
                    profile_data = json.load(f)
                    return self._parse_profile_config(profile_data)

            # Final fallback to production defaults
            logger.warning("No profile found, using production defaults")
            return self._get_production_defaults()

        except Exception as e:
            logger.error(f"Error loading profile configuration: {e}")
            logger.info("Falling back to production defaults")
            return self._get_production_defaults()

    def _get_embedded_profile_path(self) -> str:
        """Get path to embedded profile file."""
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller executable
            if hasattr(sys, '_MEIPASS'):
                return os.path.join(sys._MEIPASS, "embedded_profile.json")
            else:
                return os.path.join(os.path.dirname(sys.executable), "embedded_profile.json")
        else:
            # Running as script
            return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                "src", "embedded_profile.json")

    def _get_development_profile_path(self) -> str:
        """Get path to development profile for local development."""
        if getattr(sys, 'frozen', False):
            return ""  # Not applicable for built applications
        else:
            # Running as script - load development profile
            return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                "profiles", "dev.json")

    def _parse_profile_config(self, profile_data: Dict[str, Any]) -> ProfileConfig:
        """Parse profile data into structured configuration."""
        ui_data = profile_data.get("ui_config", {})
        deployment_data = profile_data.get("deployment", {})

        ui_config = UIConfig(
            header_color=ui_data.get("header_color", "#24398E"),
            environment_badge=ui_data.get("environment_badge"),
            show_environment_indicator=ui_data.get("show_environment_indicator", False),
            window_title_suffix=ui_data.get("window_title_suffix", "")
        )

        deployment_config = DeploymentConfig(
            server_host=deployment_data.get("server_host", ""),
            server_path=deployment_data.get("server_path", ""),
            ssh_key_secret=deployment_data.get("ssh_key_secret", ""),
            admin_key_secret=deployment_data.get("admin_key_secret", "")
        )

        return ProfileConfig(
            environment=profile_data.get("environment", "production"),
            api_url=profile_data.get("api_url", "https://app.rh-partner.com"),
            update_server_url=profile_data.get("update_server_url", "https://timesync.rh-partner.com/api/updates"),
            database_suffix=profile_data.get("database_suffix", ""),
            ui_config=ui_config,
            deployment=deployment_config
        )

    def _get_production_defaults(self) -> ProfileConfig:
        """Get production default configuration for backward compatibility."""
        ui_config = UIConfig(
            header_color="#24398E",
            environment_badge=None,
            show_environment_indicator=False,
            window_title_suffix=""
        )

        deployment_config = DeploymentConfig(
            server_host="157.173.97.199",
            server_path="/root/sirh/time-sync/downloads",
            ssh_key_secret="SSH_PRIVATE_KEY",
            admin_key_secret="ADMIN_KEY"
        )

        return ProfileConfig(
            environment="production",
            api_url="https://app.rh-partner.com",
            update_server_url="https://timesync.rh-partner.com/api/updates",
            database_suffix="",
            ui_config=ui_config,
            deployment=deployment_config
        )

    # Public API methods
    def get_environment_name(self) -> str:
        """Get the current environment name."""
        return self._profile_config.environment

    def get_api_url(self) -> str:
        """Get the API URL for current environment."""
        return self._profile_config.api_url

    def get_update_server_url(self) -> str:
        """Get the update server URL for current environment."""
        return self._profile_config.update_server_url

    def get_database_suffix(self) -> str:
        """Get the database suffix for current environment."""
        return self._profile_config.database_suffix

    def get_ui_config(self) -> UIConfig:
        """Get UI configuration for current environment."""
        return self._profile_config.ui_config

    def get_deployment_config(self) -> DeploymentConfig:
        """Get deployment configuration for current environment."""
        return self._profile_config.deployment

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self._profile_config.environment == "production"

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self._profile_config.environment == "development"

    def is_staging(self) -> bool:
        """Check if running in staging environment."""
        return self._profile_config.environment == "staging"

    def get_profile_info(self) -> Dict[str, Any]:
        """Get complete profile information for debugging."""
        return {
            "environment": self._profile_config.environment,
            "api_url": self._profile_config.api_url,
            "update_server_url": self._profile_config.update_server_url,
            "database_suffix": self._profile_config.database_suffix,
            "ui_config": {
                "header_color": self._profile_config.ui_config.header_color,
                "environment_badge": self._profile_config.ui_config.environment_badge,
                "show_environment_indicator": self._profile_config.ui_config.show_environment_indicator,
                "window_title_suffix": self._profile_config.ui_config.window_title_suffix
            }
        }