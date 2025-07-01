# src/ui/config_interface.py
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import logging
import threading
from typing import Optional, Callable

from src.application import Application
from src.domain.models import Config
from src.data.repositories import ConfigRepository
from src.core.config_service import ConfigurationService

logger = logging.getLogger(__name__)


class ConfigInterface:
    """Interface for configuring the attendance system."""

    # Define color constants to match MainWindow theme
    COLOR_PRIMARY = "#24398E"  # Blue header color
    COLOR_BACKGROUND = "#FFFFFF"  # White background
    COLOR_SUCCESS = "#4CAF50"  # Green for success states
    COLOR_ERROR = "#F44336"  # Red for error/stopped states
    COLOR_WARNING = "#FF9800"  # Orange for warning states
    COLOR_NEUTRAL = "#757575"  # Gray for neutral states
    COLOR_CARD = "#FFFFFF"  # White card background

    def __init__(self, root: Optional[tk.Tk], config_repository: ConfigRepository, application: Application):
        """
        Initialize the configuration interface.

        Args:
            root: Tkinter root window, creates a new one if None
            config_repository: Repository for configuration data
        """
        self.app = application
        self.config_repository = config_repository
        self.config_service = ConfigurationService(config_repository)
        self.root = tk.Toplevel(root) if root else tk.Tk()

        # UI status variables
        self.status_var = tk.StringVar(value="")

        # Initialize all UI-related variables
        self.company_id_var = tk.StringVar()
        self.api_username_var = tk.StringVar()
        self.api_password_var = tk.StringVar()
        self.api_secret_key_var = tk.StringVar()
        self.device_ip_var = tk.StringVar()
        self.device_port_var = tk.IntVar(value=4370)
        self.collection_interval_var = tk.IntVar(value=60)
        self.upload_interval_var = tk.IntVar(value=1)
        self.user_import_interval_var = tk.IntVar(value=12)

        # Configure window basics
        self.root.title("XXXXXConfiguration du Système de Présence")
        self.root.geometry("900x750")
        self.root.minsize(850, 800)
        self.root.withdraw()  # Hide window during setup

        # Set up style
        self.setup_style()

        # Set up the UI
        self.setup_ui()

        # Load existing configuration
        self.load_config()

        # Show the window
        self.root.deiconify()

    def setup_style(self):
        """Configure styles for modern look."""
        style = ttk.Style()
        style.theme_use('clam')

        # Set base colors
        self.root.configure(background=self.COLOR_BACKGROUND)

        # Configure styles
        style.configure('TFrame', background=self.COLOR_BACKGROUND)
        style.configure('Header.TFrame', background=self.COLOR_PRIMARY)
        style.configure('Card.TFrame', background=self.COLOR_CARD, relief='flat', borderwidth=0)

        style.configure('TLabel', background=self.COLOR_BACKGROUND, font=('Segoe UI', 10))
        style.configure('Card.TLabel', background=self.COLOR_CARD, font=('Segoe UI', 10))
        style.configure('Header.TLabel', background=self.COLOR_PRIMARY, foreground='white',
                        font=('Segoe UI', 12, 'bold'))
        style.configure('Title.TLabel', background=self.COLOR_BACKGROUND, font=('Segoe UI', 14, 'bold'))
        style.configure('SectionTitle.TLabel', background=self.COLOR_CARD, font=('Segoe UI', 12, 'bold'))

        # Status label styles
        style.configure('Success.TLabel', foreground=self.COLOR_SUCCESS, background=self.COLOR_CARD)
        style.configure('Error.TLabel', foreground=self.COLOR_ERROR, background=self.COLOR_CARD)
        style.configure('Warning.TLabel', foreground=self.COLOR_WARNING, background=self.COLOR_CARD)
        style.configure('Neutral.TLabel', foreground=self.COLOR_NEUTRAL, background=self.COLOR_CARD)

        # Button styles
        style.configure('TButton', font=('Segoe UI', 10), padding=6)
        style.configure('Action.TButton', padding=8)

        # Entry styles
        style.configure('TEntry', font=('Segoe UI', 10), padding=6)

    def setup_ui(self):
        """Set up the modern user interface."""
        # Create header frame
        header_frame = ttk.Frame(self.root, style='Header.TFrame')
        header_frame.pack(fill=tk.X, side=tk.TOP)

        # Header title
        title_label = ttk.Label(header_frame, text="Configuration du Système de Présence",
                                style='Header.TLabel')
        title_label.pack(side=tk.LEFT, padx=15, pady=10)

        # Main content area
        main_frame = ttk.Frame(self.root, padding=15, style='TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create cards for different configuration sections
        self.create_api_config_card(main_frame)
        self.create_device_config_card(main_frame)
        self.create_scheduler_config_card(main_frame)

        # Create bottom button panel
        self.create_button_panel(main_frame)

        # Status indicator at the bottom
        status_frame = ttk.Frame(main_frame, style='TFrame')
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=10)

        self.status_label = ttk.Label(status_frame, textvariable=self.status_var,
                                      style='Neutral.TLabel', wraplength=700)
        self.status_label.pack(anchor=tk.W, pady=5)

        # After window is shown, check for updates
        self.root.after(5000, lambda: self.app.check_for_updates(show_if_none=False))

    def show(self):
        """Make the window modal and visible."""
        self.root.grab_set()
        self.root.transient(self.root.master)
        self.root.focus_set()

    def create_card(self, parent, title):
        """Create a card with the given title in the parent frame."""
        # Create an outer frame that will have the background color
        outer_frame = ttk.Frame(parent, style='Card.TFrame')
        outer_frame.pack(fill=tk.BOTH, expand=False, pady=10)

        # Title area
        title_frame = ttk.Frame(outer_frame, style='Card.TFrame')
        title_frame.pack(fill=tk.X, pady=(10, 5), padx=15)

        title_label = ttk.Label(title_frame, text=title, style='SectionTitle.TLabel')
        title_label.pack(anchor=tk.W)

        # Content area with padding
        inner_content_frame = ttk.Frame(outer_frame, style='Card.TFrame', padding=(15, 10))
        inner_content_frame.pack(fill=tk.BOTH, expand=True)

        return inner_content_frame

    def create_api_config_card(self, parent):
        """Create the API configuration card."""
        card = self.create_card(parent, "Configuration API")

        # Company ID
        company_frame = ttk.Frame(card, style='Card.TFrame')
        company_frame.pack(fill=tk.X, pady=5)
        ttk.Label(company_frame, text="ID Entreprise:", style='Card.TLabel').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Entry(company_frame, textvariable=self.company_id_var, width=40).pack(side=tk.LEFT, expand=True, fill=tk.X)

        # API Username
        username_frame = ttk.Frame(card, style='Card.TFrame')
        username_frame.pack(fill=tk.X, pady=5)
        ttk.Label(username_frame, text="Nom d'utilisateur API:", style='Card.TLabel').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Entry(username_frame, textvariable=self.api_username_var, width=40).pack(side=tk.LEFT, expand=True,
                                                                                     fill=tk.X)

        # API Password
        password_frame = ttk.Frame(card, style='Card.TFrame')
        password_frame.pack(fill=tk.X, pady=5)
        ttk.Label(password_frame, text="Mot de passe API:", style='Card.TLabel').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Entry(password_frame, textvariable=self.api_password_var, show="*", width=40).pack(side=tk.LEFT,
                                                                                               expand=True, fill=tk.X)

        # API Secret Key
        secret_key_frame = ttk.Frame(card, style='Card.TFrame')
        secret_key_frame.pack(fill=tk.X, pady=5)
        ttk.Label(secret_key_frame, text="Clé Secrète API:", style='Card.TLabel').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Entry(secret_key_frame, textvariable=self.api_secret_key_var, show="*", width=40).pack(side=tk.LEFT,
                                                                                                   expand=True,
                                                                                                   fill=tk.X)

    def create_device_config_card(self, parent):
        """Create the device configuration card."""
        card = self.create_card(parent, "Configuration de l'Appareil")

        # Device IP
        ip_frame = ttk.Frame(card, style='Card.TFrame')
        ip_frame.pack(fill=tk.X, pady=5)
        ttk.Label(ip_frame, text="IP de l'Appareil:", style='Card.TLabel').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Entry(ip_frame, textvariable=self.device_ip_var, width=40).pack(side=tk.LEFT, expand=True, fill=tk.X)

        # Device Port
        port_frame = ttk.Frame(card, style='Card.TFrame')
        port_frame.pack(fill=tk.X, pady=5)
        ttk.Label(port_frame, text="Port de l'Appareil:", style='Card.TLabel').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Entry(port_frame, textvariable=self.device_port_var, width=40).pack(side=tk.LEFT, expand=True, fill=tk.X)

    def create_scheduler_config_card(self, parent):
        """Create the scheduler configuration card."""
        card = self.create_card(parent, "Configuration du Planificateur")

        # Collection Interval
        collection_frame = ttk.Frame(card, style='Card.TFrame')
        collection_frame.pack(fill=tk.X, pady=5)
        ttk.Label(collection_frame, text="Intervalle de Collecte (minutes):", style='Card.TLabel').pack(side=tk.LEFT,
                                                                                                        padx=(0, 10))
        ttk.Entry(collection_frame, textvariable=self.collection_interval_var, width=40).pack(side=tk.LEFT, expand=True,
                                                                                              fill=tk.X)

        # Upload Interval
        upload_frame = ttk.Frame(card, style='Card.TFrame')
        upload_frame.pack(fill=tk.X, pady=5)
        ttk.Label(upload_frame, text="Intervalle de Téléchargement (minutes):", style='Card.TLabel').pack(side=tk.LEFT,
                                                                                                         padx=(0, 10))
        ttk.Entry(upload_frame, textvariable=self.upload_interval_var, width=40).pack(side=tk.LEFT, expand=True,
                                                                                      fill=tk.X)

        # User Import Interval
        import_frame = ttk.Frame(card, style='Card.TFrame')
        import_frame.pack(fill=tk.X, pady=5)
        ttk.Label(import_frame, text="Intervalle d'Importation des Utilisateurs (minutes):", style='Card.TLabel').pack(
            side=tk.LEFT, padx=(0, 10))
        ttk.Entry(import_frame, textvariable=self.user_import_interval_var, width=40).pack(side=tk.LEFT, expand=True,
                                                                                           fill=tk.X)

    def create_button_panel(self, parent):
        """Create the panel with action buttons."""
        button_frame = ttk.Frame(parent, style='TFrame')
        button_frame.pack(fill=tk.X, pady=20)

        # Create modern action buttons
        ttk.Button(button_frame, text="Charger Configuration", command=self.load_config,
                   style='Action.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Tester Appareil", command=self.test_device_connection,
                   style='Action.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Tester API", command=self.test_api_connection,
                   style='Action.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Vérifier les Mises à Jour", command=self.check_for_updates,
                   style='Action.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Enregistrer Configuration", command=self.save_config,
                   style='Action.TButton').pack(side=tk.RIGHT, padx=5)

    def resource_path(self, relative_path):
        """Get absolute path to resource, works for dev and for PyInstaller."""
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    def get_config_from_form(self) -> Config:
        """Get configuration from form values."""
        return Config(
            company_id=self.company_id_var.get(),
            api_username=self.api_username_var.get(),
            api_password=self.api_password_var.get(),
            api_secret_key=self.api_secret_key_var.get(),
            device_ip=self.device_ip_var.get(),
            device_port=int(self.device_port_var.get()),
            collection_interval=int(self.collection_interval_var.get()),
            upload_interval=int(self.upload_interval_var.get()),
            import_interval=int(self.user_import_interval_var.get())
        )

    def load_config(self):
        """Load configuration from the repository."""
        try:
            config = self.config_repository.get_config()
            if not config:
                self.status_var.set(
                    "Aucune configuration existante trouvée. Veuillez saisir les détails de configuration.")
                self.status_label.config(style='Warning.TLabel')
                logger.info("No configuration found in database.")
                return

            logger.debug(f"Loaded config: {config.__dict__}")

            # Set form values from config
            self.company_id_var.set(config.company_id)
            self.api_username_var.set(config.api_username)
            self.api_password_var.set(config.api_password)
            self.api_secret_key_var.set(config.api_secret_key)
            self.device_ip_var.set(config.device_ip)
            self.device_port_var.set(config.device_port)
            self.collection_interval_var.set(config.collection_interval)
            self.upload_interval_var.set(config.upload_interval)
            self.user_import_interval_var.set(config.import_interval)

            # Update UI
            self.root.update_idletasks()
            self.status_var.set("✓ Configuration chargée avec succès.")
            self.status_label.config(style='Success.TLabel')
            logger.info("Configuration loaded from database.")
        except Exception as e:
            self.handle_error("Erreur lors du chargement de la configuration", e)

    def validate_config(self) -> bool:
        """Validate the form values."""
        if not self.company_id_var.get() or not self.device_ip_var.get():
            self.show_validation_error("L'ID de l'entreprise et l'IP de l'appareil sont des champs obligatoires.")
            return False
        return True

    def check_for_updates(self):
        """Check for application updates."""
        self.app.check_for_updates(show_if_none=True)

    def save_config(self):
        """Save configuration to the repository."""
        try:
            if not self.validate_config():
                return

            config = self.get_config_from_form()
            if self.config_service.save_config(config):
                self.show_success("✓ Configuration enregistrée avec succès.")
            else:
                self.show_error("✗ Échec de l'enregistrement de la configuration.")

        except Exception as e:
            self.handle_error("Error saving configuration", e)

    def test_device_connection(self):
        """Test connection to the device."""
        self.status_var.set("Test de la connexion à l'appareil en cours...")
        self.status_label.config(style='Warning.TLabel')
        self.run_async(self.device_connection_logic)

    def test_api_connection(self):
        """Test connection to the API."""
        self.status_var.set("Test de la connexion API en cours...")
        self.status_label.config(style='Warning.TLabel')
        self.run_async(self.api_connection_logic)

    def device_connection_logic(self):
        """Logic for testing device connection."""
        try:
            result = self.config_service.test_device_connection(
                self.device_ip_var.get(),
                int(self.device_port_var.get())
            )

            if result['success']:
                self.show_success(f"✓ {result['message']}")
            else:
                self.show_error(f"✗ {result['message']}")

        except Exception as e:
            self.handle_error("Error testing device connection", e)

    def api_connection_logic(self):
        """Logic for testing API connection."""
        try:
            result = self.config_service.test_api_connection(
                self.company_id_var.get(),
                self.api_username_var.get(),
                self.api_password_var.get()
            )

            if result['success']:
                self.show_success(f"✓ {result['message']}")
            else:
                self.show_error(f"✗ {result['message']}")

        except Exception as e:
            self.handle_error("Error testing API connection", e)

    def run_async(self, target: Callable):
        """Run a function asynchronously."""
        threading.Thread(target=target, daemon=True).start()

    def show_validation_error(self, message: str):
        """Show a validation error message."""
        self.status_var.set(f"✗ {message}")
        self.status_label.config(style='Error.TLabel')
        messagebox.showerror("Erreur de Validation", message, parent=self.root)

    def show_error(self, message: str):
        """Show an error message."""
        self.status_var.set(message)
        self.status_label.config(style='Error.TLabel')
        messagebox.showerror("Erreur", message, parent=self.root)

    def show_success(self, message: str):
        """Show a success message."""
        self.status_var.set(message)
        self.status_label.config(style='Success.TLabel')
        messagebox.showinfo("Succès", message, parent=self.root)

    def handle_error(self, message: str, exception: Exception):
        """Handle and log an error."""
        error_msg = f"{message}: {exception}"
        self.show_error(f"✗ {error_msg}")
        logger.error(error_msg)