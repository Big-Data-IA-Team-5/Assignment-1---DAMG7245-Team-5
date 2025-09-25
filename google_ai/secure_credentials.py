"""
Secure Credential Manager for Google Document AI
Team 5 - DAMG7245 Fall 2025

This module handles secure credential loading from multiple sources
with proper security practices and fallback mechanisms.
"""

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class SecureCredentialManager:
    """
    Manages Google Cloud credentials securely with multiple sources.

    Priority order:
    1. Environment variable GOOGLE_APPLICATION_CREDENTIALS
    2. Project credentials file
    3. Config file specified path
    4. Default Google Cloud SDK credentials
    """

    def __init__(self):
        """Initialize the credential manager."""
        self.credential_sources = []
        self.active_credentials_path = None
        self.project_id = None

    def find_credentials(self, config_file=None):
        """
        Find Google Cloud credentials from multiple secure sources.

        Args:
            config_file (Optional[str]): Path to config file with credential settings

        Returns:
            Optional[str]: Path to valid credentials file, or None if not found
        """
        self.credential_sources = []

        # 1. Check environment variable (MOST SECURE)
        env_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if env_creds:
            self.credential_sources.append(("Environment Variable", env_creds))
            if self._validate_credentials_file(env_creds):
                logger.info("✅ Using credentials from environment variable (SECURE)")
                self.active_credentials_path = env_creds
                return env_creds

        # 2. Check project credentials file
        project_creds = "credentials/google-credentials.json"
        if Path(project_creds).exists():
            self.credential_sources.append(("Project File", project_creds))
            if self._validate_credentials_file(project_creds):
                logger.warning("⚠️  Using project file credentials (LESS SECURE)")
                logger.warning(
                    "   Consider using environment variables for better security"
                )
                self.active_credentials_path = project_creds
                return project_creds

        # 3. Check config file specified path
        if config_file and Path(config_file).exists():
            try:
                with open(config_file, "r") as f:
                    config = json.load(f)

                config_creds = config.get("google_document_ai", {}).get(
                    "credentials_path"
                )
                if config_creds and Path(config_creds).exists():
                    self.credential_sources.append(("Config File", config_creds))
                    if self._validate_credentials_file(config_creds):
                        logger.info(f"✅ Using credentials from config: {config_creds}")
                        self.active_credentials_path = config_creds
                        return config_creds
            except Exception as e:
                logger.warning(f"Could not read config file {config_file}: {e}")

        # 4. Try default Google Cloud SDK location
        home = Path.home()
        default_creds = (
            home / ".config" / "gcloud" / "application_default_credentials.json"
        )
        if default_creds.exists():
            self.credential_sources.append(("Google Cloud SDK", str(default_creds)))
            logger.info("✅ Using default Google Cloud SDK credentials")
            self.active_credentials_path = str(default_creds)
            return str(default_creds)

        # No credentials found
        logger.error("❌ No Google Cloud credentials found!")
        self._print_credential_help()
        return None

    def _validate_credentials_file(self, creds_path):
        """
        Validate that a credentials file exists and has proper structure.

        Args:
            creds_path (str): Path to credentials file

        Returns:
            bool: True if valid, False otherwise
        """
        try:
            if not Path(creds_path).exists():
                return False

            with open(creds_path, "r") as f:
                creds = json.load(f)

            # Check for required fields
            required_fields = ["type", "project_id", "private_key", "client_email"]
            missing_fields = [field for field in required_fields if field not in creds]

            if missing_fields:
                logger.error(
                    f"Invalid credentials file {creds_path}. Missing fields: {missing_fields}"
                )
                return False

            # Store project ID for later use
            self.project_id = creds.get("project_id")

            # Check file permissions (should be restrictive)
            file_stat = Path(creds_path).stat()
            permissions = oct(file_stat.st_mode)[-3:]
            if permissions not in ["600", "644"]:
                logger.warning(
                    f"⚠️  Credentials file has permissions {permissions}. Consider setting to 600 for security."
                )

            return True

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in credentials file: {creds_path}")
            return False
        except Exception as e:
            logger.error(f"Error validating credentials file {creds_path}: {e}")
            return False

    def get_project_id(self, config_file=None):
        """
        Extract project ID from credentials or config.

        Args:
            config_file (Optional[str]): Path to config file

        Returns:
            Optional[str]: Project ID if found
        """
        # First try from validated credentials
        if self.project_id:
            return self.project_id

        # Try from config file
        if config_file and Path(config_file).exists():
            try:
                with open(config_file, "r") as f:
                    config = json.load(f)
                return config.get("google_document_ai", {}).get("project_id")
            except Exception:
                pass

        return None

    def setup_environment(self, config_file=None):
        """
        Set up the environment for Google Cloud authentication.

        Args:
            config_file (Optional[str]): Path to config file

        Returns:
            bool: True if setup successful, False otherwise
        """
        creds_path = self.find_credentials(config_file)
        if not creds_path:
            return False

        # Set environment variable if not already set
        if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path
            logger.info(f"Set GOOGLE_APPLICATION_CREDENTIALS to: {creds_path}")

        return True

    def _print_credential_help(self):
        """Print helpful information about setting up credentials."""
        logger.info("📋 CREDENTIAL SETUP OPTIONS:")
        logger.info("")
        logger.info("🔒 MOST SECURE - Environment Variable:")
        logger.info(
            "   export GOOGLE_APPLICATION_CREDENTIALS='/path/to/your/credentials.json'"
        )
        logger.info("")
        logger.info("📁 PROJECT FILE - Less Secure:")
        logger.info("   Place your credentials at: credentials/google-credentials.json")
        logger.info("")
        logger.info("⚙️  CONFIG FILE - Specify in configs/google_ai_config.json:")
        logger.info('   "credentials_path": "/path/to/your/credentials.json"')
        logger.info("")
        logger.info("📚 For detailed setup: see SECURE_CREDENTIALS_GUIDE.md")

        if self.credential_sources:
            logger.info("🔍 SEARCHED LOCATIONS:")
            for source, path in self.credential_sources:
                exists = "✅" if Path(path).exists() else "❌"
                logger.info(f"   {exists} {source}: {path}")


# Convenience function for easy use
def setup_secure_credentials(config_file=None):
    """
    Set up secure Google Cloud credentials.

    Args:
        config_file (Optional[str]): Path to config file

    Returns:
        tuple: (success: bool, project_id: Optional[str])
    """
    manager = SecureCredentialManager()
    success = manager.setup_environment(config_file)
    project_id = manager.get_project_id(config_file) if success else None

    return success, project_id


if __name__ == "__main__":
    # Test the credential manager
    print("🔐 Testing Secure Credential Manager")
    print("=" * 50)

    manager = SecureCredentialManager()
    config_file = "configs/google_ai_config.json"

    success = manager.setup_environment(config_file)
    project_id = manager.get_project_id(config_file)

    print(f"✅ Setup successful: {success}")
    print(f"📋 Project ID: {project_id}")
    print(f"🔑 Active credentials: {manager.active_credentials_path}")
