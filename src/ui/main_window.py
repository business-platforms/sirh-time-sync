# src/ui/main_window.py
import os
import sys
import logging
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import Optional, Dict, Any

from src.ui.config_interface import ConfigInterface
from src.ui.records_interface import RecordsInterface
from src.ui.users_interface import UsersInterface
from src.application import Application

logger = logging.getLogger(__name__)


class MainWindow:
    """Main application window with updated modern design."""

    # Define color constants
    COLOR_PRIMARY = "#24398E"  # Blue header color
    COLOR_BACKGROUND = "#FFFFFF"  # White background
    COLOR_SUCCESS = "#4CAF50"  # Green for success states
    COLOR_ERROR = "#F44336"  # Red for error/stopped states
    COLOR_WARNING = "#FF9800"  # Orange for warning states
    COLOR_NEUTRAL = "#757575"  # Gray for neutral states
    COLOR_CARD = "#FFFFFF"  # White card background

    def __init__(self, application: Application):
        self.app = application

        # Create main window
        self.root = tk.Tk()
        self.root.withdraw()  # Hide window during setup

        # UI status variables
        self.status_var = tk.StringVar(value="Système arrêté")
        self.collector_status_var = tk.StringVar(value="Collecteur: Arrêté")
        self.uploader_status_var = tk.StringVar(value="Téléchargeur: Arrêté")
        self.user_importer_status_var = tk.StringVar(value="Importateur d'Utilisateurs: Arrêté")
        self.device_test_var = tk.StringVar(value="Connexion Appareil: Non Testé")
        self.api_test_var = tk.StringVar(value="Connexion API: Non Testé")
        self.last_collection_var = tk.StringVar(value="Dernière collecte: Jamais")
        self.last_upload_var = tk.StringVar(value="Dernier téléchargement: Jamais")
        self.last_import_var = tk.StringVar(value="Dernière importation d'utilisateur: Jamais")
        self.test_results_var = tk.StringVar(value="")

        # References for UI elements
        self.status_label = None
        self.start_button = None
        self.stop_button = None
        self.test_button = None
        self.device_status_label = None
        self.api_status_label = None
        self.collector_status_label = None
        self.uploader_status_label = None
        self.user_importer_status_label = None
        self.test_results_label = None
        self.logo_img = None

        # Connection test status
        self.connectivity_success = False

        logger.info("Main window initializing")

    def setup_ui(self):
        """Set up the modern user interface."""
        # Configure window basics
        self.root.title("Panneau de Contrôle du Système de Présence")
        self.root.geometry("820x900")
        self.root.minsize(820, 900)
        self.root.resizable(True, True)

        # Configure styles for modern look
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
        style.configure('Start.TButton', background='#f0f0f0')
        style.configure('Stop.TButton', background=self.COLOR_ERROR)
        style.configure('Action.TButton', padding=8)

        # Card styles
        style.configure('Card.TLabelframe', background=self.COLOR_CARD, borderwidth=0)
        style.configure('Card.TLabelframe.Label', background=self.COLOR_CARD)

        # Load Logo
        self.load_logo()

        # Create header frame
        header_frame = ttk.Frame(self.root, style='Header.TFrame')
        header_frame.pack(fill=tk.X, side=tk.TOP)

        # Add window controls (minimize, maximize, close) - these would need custom implementation
        controls_frame = ttk.Frame(header_frame, style='Header.TFrame')
        controls_frame.pack(side=tk.RIGHT, padx=10)

        # Header title
        title_label = ttk.Label(header_frame, text="Panneau de Contrôle du Système de Présence",
                                style='Header.TLabel')
        title_label.pack(side=tk.LEFT, padx=15, pady=10)

        # Main content area
        main_frame = ttk.Frame(self.root, padding=15, style='TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title with logos
        title_frame = ttk.Frame(main_frame, style='TFrame')
        title_frame.pack(fill=tk.X, pady=(10, 20))

        # Global project logo on the left
        if hasattr(self, 'global_logo_img'):
            global_logo_label = ttk.Label(title_frame, image=self.global_logo_img, background=self.COLOR_BACKGROUND)
            global_logo_label.pack(side=tk.LEFT, padx=(0, 10))

        # Title text in the middle
        title_text = ttk.Label(title_frame, text="Système de Présence", style='Title.TLabel')
        title_text.pack(side=tk.LEFT, padx=15)

        # Application logo on the right
        if hasattr(self, 'app_logo_img'):
            app_logo_label = ttk.Label(title_frame, image=self.app_logo_img, background=self.COLOR_BACKGROUND)
            app_logo_label.pack(side=tk.RIGHT, padx=(10, 0))

        # Create two-column layout for cards
        columns_frame = ttk.Frame(main_frame, style='TFrame')
        columns_frame.pack(fill=tk.BOTH, expand=True)

        # Left column
        left_column = ttk.Frame(columns_frame, style='TFrame')
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Right column
        right_column = ttk.Frame(columns_frame, style='TFrame')
        right_column.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        # System Controls Card
        controls_card = self.create_card(left_column, "Contrôles du Système")

        # Status row in controls card
        status_frame = ttk.Frame(controls_card, style='Card.TFrame')
        status_frame.pack(fill=tk.X, pady=5)

        status_label = ttk.Label(status_frame, text="Statut:", style='Card.TLabel')
        status_label.pack(side=tk.LEFT)

        self.status_label = ttk.Label(status_frame, textvariable=self.status_var,
                                      style='Success.TLabel' if self.app.is_running() else 'Error.TLabel')
        self.status_label.pack(side=tk.LEFT, padx=10)

        # Buttons row
        buttons_frame = ttk.Frame(controls_card, style='Card.TFrame')
        buttons_frame.pack(fill=tk.X, pady=10)

        self.start_button = ttk.Button(buttons_frame, text="► Démarrer le Système",
                                       command=self.start_system, style='Action.TButton')
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))

        self.stop_button = ttk.Button(buttons_frame, text="■ Arrêter le Système",
                                      command=self.stop_system, state=tk.DISABLED, style='Action.TButton')
        self.stop_button.pack(side=tk.LEFT)

        # Connection Tests Card
        connection_card = self.create_card(left_column, "Tests de Connexion")

        # Device connection status
        self.device_status_label = ttk.Label(connection_card, textvariable=self.device_test_var,
                                             style='Neutral.TLabel')
        self.device_status_label.pack(anchor=tk.W, pady=5)

        # API connection status
        self.api_status_label = ttk.Label(connection_card, textvariable=self.api_test_var,
                                          style='Neutral.TLabel')
        self.api_status_label.pack(anchor=tk.W, pady=5)

        # Test button
        test_button_frame = ttk.Frame(connection_card, style='Card.TFrame')
        test_button_frame.pack(fill=tk.X, pady=10)

        self.test_button = ttk.Button(test_button_frame, text="Relancer les Tests de Connexion",
                                      command=self.test_connections, style='Action.TButton')
        self.test_button.pack(pady=5)

        # Test results
        self.test_results_label = ttk.Label(connection_card, textvariable=self.test_results_var,
                                            style='Success.TLabel')
        self.test_results_label.pack(anchor=tk.W, pady=5)

        # System Information Card
        info_card = self.create_card(right_column, "Informations Système")

        # Component status indicators with checkmarks
        self.collector_status_label = ttk.Label(info_card, textvariable=self.collector_status_var,
                                                style='Success.TLabel')
        self.collector_status_label.pack(anchor=tk.W, pady=5)

        self.uploader_status_label = ttk.Label(info_card, textvariable=self.uploader_status_var,
                                               style='Success.TLabel')
        self.uploader_status_label.pack(anchor=tk.W, pady=5)

        self.user_importer_status_label = ttk.Label(info_card, textvariable=self.user_importer_status_var,
                                                    style='Success.TLabel')
        self.user_importer_status_label.pack(anchor=tk.W, pady=5)

        # Separator
        ttk.Separator(info_card, orient='horizontal').pack(fill=tk.X, pady=10)

        # Timestamp information
        ttk.Label(info_card, textvariable=self.last_collection_var, style='Card.TLabel').pack(anchor=tk.W, pady=3)
        ttk.Label(info_card, textvariable=self.last_upload_var, style='Card.TLabel').pack(anchor=tk.W, pady=3)
        ttk.Label(info_card, textvariable=self.last_import_var, style='Card.TLabel').pack(anchor=tk.W, pady=3)

        # Bottom toolbar for navigation buttons
        toolbar_frame = ttk.Frame(main_frame, style='TFrame')
        toolbar_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(20, 0))

        # Modern flat buttons with icons
        ttk.Button(toolbar_frame, text="⚙ Configurer", command=self.open_config,
                   style='Action.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar_frame, text="👥 Utilisateurs", command=self.open_users,
                   style='Action.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar_frame, text="📋 Enregistrements", command=self.open_records,
                   style='Action.TButton').pack(side=tk.LEFT, padx=5)

        # Set up initial state
        self.update_ui_based_on_config()

        # Set up close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Show the window
        self.root.deiconify()

    def create_card(self, parent, title):
        """Create a card with the given title in the parent frame."""
        # Create an outer frame that will have the background color
        outer_frame = ttk.Frame(parent, style='Card.TFrame')
        outer_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Create rounded corners with Canvas
        card_canvas = tk.Canvas(outer_frame, bg=self.COLOR_CARD,
                                highlightthickness=0)
        card_canvas.pack(fill=tk.BOTH, expand=True)

        # Draw rounded rectangle
        radius = 15  # Corner radius
        card_canvas.create_rectangle(radius, 0,
                                     card_canvas.winfo_reqwidth() - radius,
                                     card_canvas.winfo_reqheight(),
                                     fill=self.COLOR_CARD, outline="lightgray", width=1)
        card_canvas.create_rectangle(0, radius,
                                     card_canvas.winfo_reqwidth(),
                                     card_canvas.winfo_reqheight() - radius,
                                     fill=self.COLOR_CARD, outline="lightgray", width=1)
        card_canvas.create_arc(0, 0, radius * 2, radius * 2,
                               start=90, extent=90,
                               fill=self.COLOR_CARD, outline="lightgray", width=1)
        card_canvas.create_arc(card_canvas.winfo_reqwidth() - (radius * 2), 0,
                               card_canvas.winfo_reqwidth(), radius * 2,
                               start=0, extent=90,
                               fill=self.COLOR_CARD, outline="lightgray", width=1)
        card_canvas.create_arc(0, card_canvas.winfo_reqheight() - (radius * 2),
                               radius * 2, card_canvas.winfo_reqheight(),
                               start=180, extent=90,
                               fill=self.COLOR_CARD, outline="lightgray", width=1)
        card_canvas.create_arc(card_canvas.winfo_reqwidth() - (radius * 2),
                               card_canvas.winfo_reqheight() - (radius * 2),
                               card_canvas.winfo_reqwidth(), card_canvas.winfo_reqheight(),
                               start=270, extent=90,
                               fill=self.COLOR_CARD, outline="lightgray", width=1)

        # Content frame inside the canvas
        content_frame = ttk.Frame(card_canvas, style='Card.TFrame')
        card_canvas.create_window(card_canvas.winfo_reqwidth() / 2,
                                  card_canvas.winfo_reqheight() / 2,
                                  window=content_frame,
                                  anchor="center",
                                  width=card_canvas.winfo_reqwidth() - 20,
                                  height=card_canvas.winfo_reqheight() - 20)

        # Title area
        title_frame = ttk.Frame(content_frame, style='Card.TFrame')
        title_frame.pack(fill=tk.X, pady=(10, 5), padx=15)

        title_label = ttk.Label(title_frame, text=title, style='SectionTitle.TLabel')
        title_label.pack(anchor=tk.W)

        # Content area with padding
        inner_content_frame = ttk.Frame(content_frame, style='Card.TFrame', padding=(15, 10))
        inner_content_frame.pack(fill=tk.BOTH, expand=True)

        return inner_content_frame

    def update_ui_based_on_config(self):
        """Update UI based on configuration existence."""
        config_service = self.app.container.get('config_service')
        config = config_service.get_config()

        if config:
            self.status_var.set("Système prêt à démarrer")
            self.status_label.config(style='Warning.TLabel')
            # Automatically run connection tests on startup
            self.test_connections()
            if self.connectivity_success:
                self.start_system()
        else:
            self.status_var.set("Système non configuré")
            self.status_label.config(style='Error.TLabel')
            self.start_button.config(state=tk.DISABLED)

    def update_status(self, var, component, status, status_type):
        """Update a status variable with formatting."""
        # Status type can be: 'success', 'warning', 'error', or 'neutral'
        icon = "✓" if status_type == "success" else "✗" if status_type == "error" else "●"
        var.set(f"{icon} {component}: {status}")

    def load_logo(self):
        """Load both the global project logo and application-specific logo."""
        try:
            # Load global project logo
            global_logo_path = self.resource_path("assets/logo.png")
            global_logo_img = tk.PhotoImage(file=global_logo_path)
            global_logo_display = global_logo_img.subsample(18, 18)  # Adjust scale as needed
            self.global_logo_img = global_logo_display  # Store reference

            # Load application-specific logo
            app_logo_path = self.resource_path("assets/timesync-logo.png")
            app_logo_img = tk.PhotoImage(file=app_logo_path)
            app_logo_display = app_logo_img.subsample(5, 5)  # Adjust scale as needed
            self.app_logo_img = app_logo_display  # Store reference

            # Use application logo for window icon
            self.root.iconphoto(True, app_logo_img)

            logger.info("Both logos loaded successfully")
        except FileNotFoundError as e:
            logger.error(f"Logo file not found: {e}")
        except Exception as e:
            logger.error(f"Failed to load logos: {e}")

    def resource_path(self, relative_path):
        """Get absolute path to resource, works for dev and for PyInstaller."""
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    def test_connections(self):
        """Test device and API connections."""
        # Update UI to show testing in progress
        self.test_button.config(text="Test en cours...", state=tk.DISABLED)
        self.test_results_var.set("Exécution des tests de connexion...")
        self.test_results_label.config(style='Warning.TLabel')

        # Update connection status indicators
        self.update_status(self.device_test_var, "Connexion Appareil", "Test en cours...", "warning")
        self.device_status_label.config(style='Warning.TLabel')
        self.update_status(self.api_test_var, "Connexion API", "Test en cours...", "warning")
        self.api_status_label.config(style='Warning.TLabel')

        # Allow UI to update
        self.root.update_idletasks()

        # Run tests
        results = self.app.test_connections()
        self.connectivity_success = results.get('overall', False)

        # Update device status
        device_result = results.get('device', {})
        if device_result.get('success', False):
            self.update_status(self.device_test_var, "Connexion Appareil", "Connecté", "success")
            self.device_status_label.config(style='Success.TLabel')
        else:
            self.update_status(self.device_test_var, "Connexion Appareil", "Échec", "error")
            self.device_status_label.config(style='Error.TLabel')

        # Update API status
        api_result = results.get('api', {})
        if api_result.get('success', False):
            self.update_status(self.api_test_var, "Connexion API", "Connectée", "success")
            self.api_status_label.config(style='Success.TLabel')
        else:
            self.update_status(self.api_test_var, "Connexion API", "Échec", "error")
            self.api_status_label.config(style='Error.TLabel')

        # Update overall results
        if self.connectivity_success:
            self.test_results_var.set("✓ Toutes les connexions réussies")
            self.test_results_label.config(style='Success.TLabel')
        else:
            self.test_results_var.set("✗ Test de connexion échoué")
            self.test_results_label.config(style='Error.TLabel')

        # Re-enable test button
        self.test_button.config(text="Relancer les Tests de Connexion", state=tk.NORMAL)

        # Update start button state
        config_service = self.app.container.get('config_service')
        if self.connectivity_success and config_service.get_config():
            self.start_button.config(state=tk.NORMAL)
        else:
            self.start_button.config(state=tk.DISABLED)

    def start_system(self):
        """Start the attendance system."""
        if not self.connectivity_success:
            messagebox.showerror("Erreur de Connexion",
                                 "Impossible de démarrer le système. Veuillez vérifier les connexions.")
            return

        if self.app.start_service():
            # Update main status
            self.status_var.set("Système en marche")
            self.status_label.config(style='Success.TLabel')

            # Update component statuses
            self.update_status(self.collector_status_var, "Collecteur", "En marche", "success")
            self.collector_status_label.config(style='Success.TLabel')

            self.update_status(self.uploader_status_var, "Téléchargeur", "En marche", "success")
            self.uploader_status_label.config(style='Success.TLabel')

            self.update_status(self.user_importer_status_var, "Importateur d'Utilisateurs", "En marche", "success")
            self.user_importer_status_label.config(style='Success.TLabel')

            # Update button states
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)

            # Show current time as start time
            self.last_collection_var.set("Dernière collecte: Programmée")
            self.last_upload_var.set("Dernier téléchargement: Programmé")
            self.last_import_var.set("Dernière importation d'utilisateur: Programmée")
        else:
            messagebox.showerror("Erreur Système",
                                 "Impossible de démarrer le système. Consultez les journaux pour plus de détails.")

    def stop_system(self):
        """Stop the attendance system."""
        self.app.stop_service()

        # Update main status
        self.status_var.set("Système arrêté")
        self.status_label.config(style='Error.TLabel')

        # Update component statuses
        self.update_status(self.collector_status_var, "Collecteur", "Arrêté", "error")
        self.collector_status_label.config(style='Error.TLabel')

        self.update_status(self.uploader_status_var, "Téléchargeur", "Arrêté", "error")
        self.uploader_status_label.config(style='Error.TLabel')

        self.update_status(self.user_importer_status_var, "Importateur d'Utilisateurs", "Arrêté", "error")
        self.user_importer_status_label.config(style='Error.TLabel')

        # Update button states
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def open_config(self):
        """Open the configuration window."""
        config_window = ConfigInterface(self.root, self.app.container.get('config_repository'))
        config_window.show()

        # After config window is closed, check if we need to update the UI
        # self.update_ui_based_on_config()

    def open_users(self):
        """Open the users management window."""
        device_service = self.app.container.get('device_service')
        users = device_service.get_users()
        users_window = UsersInterface(
            self.root,
            users,
            self.app.container.get('attendance_repository'),
            self.app.container.get('device_service'),
            self.app.container.get('sync_service')
        )
        users_window.show()

    def open_records(self):
        """Open the records management window."""
        # First collect the latest records
        attendance_service = self.app.container.get('attendance_service')
        attendance_service.collect_attendance()

        # Now open the records window
        device_service = self.app.container.get('device_service')
        users = device_service.get_users()
        records_window = RecordsInterface(
            self.root,
            users,
            self.app.container.get('attendance_repository'),
            self.app.container.get('attendance_service'),
            self.app.container.get('sync_service')
        )
        records_window.show()

    def on_close(self):
        """Handle window closing."""
        if messagebox.askokcancel("Quitter", "Voulez-vous quitter? Cela arrêtera la collecte de présence."):
            self.app.stop_service()
            self.root.destroy()

    def start(self):
        """Start the main window."""
        self.setup_ui()
        self.root.mainloop()