# src/core/config_service.py
import logging
import os
from typing import Dict, Any, Optional

from src.core.profile_manager import ProfileManager
from src.domain.models import Config
from src.data.repositories import ConfigRepository
from src.service.device_service import DeviceConnection

logger = logging.getLogger(__name__)


class ConfigurationService:
    """Service for managing system configuration."""

    def __init__(self, config_repository: ConfigRepository):
        self.config_repository = config_repository

        profile_manager = ProfileManager()
        self._api_url = profile_manager.get_api_url()

    @property
    def api_url(self) -> str:
        """Get the API URL."""
        return self._api_url

    def get_config(self) -> Optional[Config]:
        """Get the current configuration."""
        return self.config_repository.get_config()

    def save_config(self, config: Config) -> bool:
        """Save a new configuration."""
        try:
            self.config_repository.save_config(config)
            logger.info("Configuration saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False

    def update_from_dict(self, config_dict: Dict[str, Any]) -> bool:
        """Update configuration from a dictionary."""
        try:
            # Get existing config or create new one
            config = self.get_config() or Config()

            # Update fields from dictionary
            for key, value in config_dict.items():
                if hasattr(config, key):
                    setattr(config, key, value)

            # Save updated config
            return self.save_config(config)
        except Exception as e:
            logger.error(f"Erreur de mise à jour de la configuration: {e}")
            return False

    def test_device_connection(self, ip: str, port: int) -> Dict[str, Any]:
        """Test connection to a device."""
        from src.service.device_service import DeviceService

        try:
            # Create temporary device service
            device_service = DeviceService(self.config_repository)

            # Override connection parameters
            device_service.connection = DeviceConnection(ip=ip, port=port)

            # Try to connect
            if not device_service.connect():
                return {
                    'success': False,
                    'message': f"Impossible de se connecter à l'appareil à l'adresse {ip}:{port}"
                }

            # Get user count
            users = device_service.get_users()
            user_count = len(users)

            # Disconnect
            device_service.disconnect()

            return {
                'success': True,
                'message': f"Connexion réussie à l'appareil. {user_count} utilisateurs trouvés.",
                'user_count': user_count
            }
        except Exception as e:
            logger.error(f"Error testing device connection: {e}")
            return {
                'success': False,
                'message': f"Erreur: {str(e)}"
            }

    def test_api_connection(self, company_id: str, username: str, password: str) -> Dict[str, Any]:
        """Test connection to the API."""
        from src.service.api_service import APIService

        try:
            # Create temporary config repository with test values
            class TestConfigRepository(ConfigRepository):
                def get_config(self):
                    return Config(
                        company_id=company_id,
                        api_username=username,
                        api_password=password
                    )

                def save_config(self, config):
                    pass

            # Create temporary API service
            api_service = APIService(TestConfigRepository(), self.api_url)

            # Try to authenticate
            if api_service.authenticate():
                return {
                    'success': True,
                    'message': f"Authentification réussie auprès de l'API à {self.api_url}"
                }
            else:
                return {
                    'success': False,
                    'message': f"Échec de l'authentification avec l'API à {self.api_url}"
                }
        except Exception as e:
            logger.error(f"Erreur lors du test de la connexion à l'API: {e}")
            return {
                'success': False,
                'message': f"Erreur: {str(e)}"
            }