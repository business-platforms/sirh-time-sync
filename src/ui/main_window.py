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
    """Main application window with updated modern design and responsive layout."""

    # Define color constants
    COLOR_PRIMARY = "#24398E"  # Blue header color
    COLOR_BACKGROUND = "#F5F7FA"  # Light gray-blue background for better contrast
    COLOR_SUCCESS = "#4CAF50"  # Green for success states
    COLOR_ERROR = "#F44336"  # Red for error/stopped states
    COLOR_WARNING = "#FF9800"  # Orange for warning states
    COLOR_NEUTRAL = "#757575"  # Gray for neutral states
    COLOR_CARD = "#FFFFFF"  # White card background
    COLOR_BORDER = "#E0E6ED"  # Soft blue-gray for borders

    # Minimum dimensions
    MIN_WIDTH = 640
    MIN_HEIGHT = 680

    # Default dimensions for medium-sized screens
    DEFAULT_WIDTH = 820
    DEFAULT_HEIGHT = 900

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
        self.button_container = None  # New reference for button container

        # Layout references
        self.main_frame = None
        self.columns_frame = None
        self.left_column = None
        self.right_column = None
        self.current_layout = "dual"  # Keep track of current layout: "dual" or "single"

        # Connection test status
        self.connectivity_success = False

        logger.info("Main window initializing")

    def setup_ui(self):
        """Set up the modern user interface with responsive layout."""
        # Configure window basics
        self.root.title("Panneau de Contrôle du Système de Présence")

        # Set initial size based on screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Determine appropriate window size
        width = min(self.DEFAULT_WIDTH, int(screen_width * 0.8))
        height = min(self.DEFAULT_HEIGHT, int(screen_height * 0.8))

        # Set geometry and constraints
        self.root.geometry(f"{width}x{height}")
        self.root.minsize(self.MIN_WIDTH, self.MIN_HEIGHT)
        self.root.resizable(True, True)

        # Configure styles for modern look
        self.setup_styles()

        # Set base colors
        self.root.configure(background=self.COLOR_BACKGROUND)

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

        # Main content area with increased padding
        self.main_frame = ttk.Frame(self.root, padding=20, style='TFrame')
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Title with logos
        title_frame = ttk.Frame(self.main_frame, style='TFrame')
        title_frame.pack(fill=tk.X, pady=(5, 15))  # Reduce vertical padding from (5, 20) to (5, 15)

        # Add width constraint to the title_frame
        title_frame.pack_propagate(False)  # Prevent propagation of size from children
        title_frame.configure(height=50)  # Set a fixed height for the title area

        # Global project logo on the left - make smaller
        if hasattr(self, 'global_logo_img'):
            global_logo_label = ttk.Label(title_frame, image=self.global_logo_img, background=self.COLOR_BACKGROUND)
            global_logo_label.pack(side=tk.LEFT, padx=(0, 5))  # Reduce padding from (0, 10) to (0, 5)

        # Title text in the middle - use smaller font or reduce padding
        title_text = ttk.Label(title_frame, text="Système de Présence", style='Title.TLabel')
        title_text.pack(side=tk.LEFT, padx=10)  # Reduce padding from 15 to 10

        # Application logo on the right - make smaller
        if hasattr(self, 'app_logo_img'):
            app_logo_label = ttk.Label(title_frame, image=self.app_logo_img, background=self.COLOR_BACKGROUND)
            app_logo_label.pack(side=tk.RIGHT, padx=(5, 0))  # Reduce padding from (10, 0) to (5, 0)

        # Create the layout based on initial window size
        self.create_responsive_layout()

        # Bottom toolbar for navigation buttons
        toolbar_frame = ttk.Frame(self.main_frame, style='TFrame')
        toolbar_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(25, 0))

        # Create a container frame to better handle button layout
        self.button_container = ttk.Frame(toolbar_frame, style='TFrame')
        self.button_container.pack(fill=tk.X, expand=True)

        # Modern flat buttons with icons - with flex layout
        config_btn = ttk.Button(self.button_container, text="⚙ Configurer", command=self.open_config,
                                style='Action.TButton')
        config_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        users_btn = ttk.Button(self.button_container, text="👥 Utilisateurs", command=self.open_users,
                               style='Action.TButton')
        users_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        records_btn = ttk.Button(self.button_container, text="📋 Enregistrements", command=self.open_records,
                                 style='Action.TButton')
        records_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Set up initial state
        self.update_ui_based_on_config()

        # Set up close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Bind resize event
        self.root.bind("<Configure>", self.on_window_resize)

        # Show the window
        self.root.deiconify()

    def setup_styles(self):
        """Configure ttk styles for the application."""
        style = ttk.Style()
        style.theme_use('clam')

        # Configure styles
        style.configure('TFrame', background=self.COLOR_BACKGROUND)
        style.configure('Header.TFrame', background=self.COLOR_PRIMARY)
        style.configure('Card.TFrame', background=self.COLOR_CARD, relief='flat', borderwidth=0)

        style.configure('TLabel', background=self.COLOR_BACKGROUND, font=('Segoe UI', 10))
        style.configure('Card.TLabel', background=self.COLOR_CARD, font=('Segoe UI', 10))
        style.configure('Header.TLabel', background=self.COLOR_PRIMARY, foreground='white',
                        font=('Segoe UI', 12, 'bold'))
        style.configure('Title.TLabel', background=self.COLOR_BACKGROUND, font=('Segoe UI', 16, 'bold'))
        style.configure('SectionTitle.TLabel', background=self.COLOR_CARD, font=('Segoe UI', 12, 'bold'))

        # Status label styles
        style.configure('Success.TLabel', foreground=self.COLOR_SUCCESS, background=self.COLOR_CARD)
        style.configure('Error.TLabel', foreground=self.COLOR_ERROR, background=self.COLOR_CARD)
        style.configure('Warning.TLabel', foreground=self.COLOR_WARNING, background=self.COLOR_CARD)
        style.configure('Neutral.TLabel', foreground=self.COLOR_NEUTRAL, background=self.COLOR_CARD)

        # Button styles - improved padding and appearance
        style.configure('TButton', font=('Segoe UI', 10), padding=8)
        style.configure('Start.TButton', background='#f0f0f0')
        style.configure('Stop.TButton', background=self.COLOR_ERROR)
        style.configure('Action.TButton', padding=10)

        # Modern button styles with reduced padding and cleaner look
        style.configure('TButton', font=('Segoe UI', 9), padding=5)
        style.configure('ModernButton.TButton',
                        padding=(5, 3),
                        font=('Segoe UI', 9))

        # Define hover and pressed states for modern look
        style.map('ModernButton.TButton',
                  background=[('active', '#e0e6ed'), ('pressed', '#d0d6dd')],
                  relief=[('pressed', 'flat'), ('!pressed', 'flat')])

        # Small action buttons
        style.configure('SmallAction.TButton',
                        padding=(4, 2),
                        font=('Segoe UI', 8))

        # Card styles
        style.configure('Card.TLabelframe', background=self.COLOR_CARD, borderwidth=0)
        style.configure('Card.TLabelframe.Label', background=self.COLOR_CARD)

    def create_responsive_layout(self):
        """Create responsive layout based on window width."""
        # Get current window width
        width = self.root.winfo_width()

        # Remove existing layout if it exists
        if self.columns_frame:
            self.columns_frame.destroy()

        # Create new container for layout
        self.columns_frame = ttk.Frame(self.main_frame, style='TFrame')
        self.columns_frame.pack(fill=tk.BOTH, expand=True)

        # Decision point for layout type
        if width <= self.MIN_WIDTH + 100 and self.current_layout != "single":
            # Switch to single column layout for small screens
            self.create_single_column_layout()
            self.current_layout = "single"
        elif width > self.MIN_WIDTH + 100 and self.current_layout != "dual":
            # Switch to dual column layout for larger screens
            self.create_dual_column_layout()
            self.current_layout = "dual"
        else:
            # Use current layout type
            if self.current_layout == "single":
                self.create_single_column_layout()
            else:
                self.create_dual_column_layout()

    def create_dual_column_layout(self):
        """Create two-column layout."""
        # Left column
        self.left_column = ttk.Frame(self.columns_frame, style='TFrame')
        self.left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))

        # Right column
        self.right_column = ttk.Frame(self.columns_frame, style='TFrame')
        self.right_column.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(15, 0))

        # Create cards in appropriate columns
        self.create_system_controls(self.left_column)
        self.create_connection_tests(self.left_column)
        self.create_system_info(self.right_column)

    def create_single_column_layout(self):
        """Create single-column layout for smaller screens."""
        # Create a single column
        self.left_column = ttk.Frame(self.columns_frame, style='TFrame')
        self.left_column.pack(fill=tk.BOTH, expand=True)

        # Create all cards in the single column
        self.create_system_controls(self.left_column)
        self.create_connection_tests(self.left_column)
        self.create_system_info(self.left_column)

    def create_system_controls(self, parent):
        """Create the System Controls card with responsive button layout."""
        controls_card = self.create_card(parent, "Contrôles du Système", with_status=True)

        # Create a responsive container for the buttons
        self.system_buttons_container = ttk.Frame(controls_card, style='Card.TFrame')
        self.system_buttons_container.pack(fill=tk.X, pady=12)

        # Create buttons that will fill available space
        self.start_button = ttk.Button(self.system_buttons_container, text="► Démarrer",
                                       command=self.start_system, style='Action.TButton')
        self.start_button.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        self.stop_button = ttk.Button(self.system_buttons_container, text="■ Arrêter",
                                      command=self.stop_system, state=tk.DISABLED, style='Action.TButton')
        self.stop_button.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

    def create_connection_tests(self, parent):
        """Create Connection Tests card with responsive button."""
        connection_card = self.create_card(parent, "Tests de Connexion")

        # Create a frame to hold both status indicators in one row
        status_frame = ttk.Frame(connection_card, style='Card.TFrame')
        status_frame.pack(fill=tk.X, pady=8)

        # Device connection status (left side)
        self.device_status_label = ttk.Label(status_frame, textvariable=self.device_test_var,
                                             style='Neutral.TLabel')
        self.device_status_label.pack(side=tk.LEFT, anchor=tk.W)

        # Add a spacer between indicators
        ttk.Label(status_frame, text="  -  ", style='Card.TLabel').pack(side=tk.LEFT)

        # API connection status (right side)
        self.api_status_label = ttk.Label(status_frame, textvariable=self.api_test_var,
                                          style='Neutral.TLabel')
        self.api_status_label.pack(side=tk.LEFT, anchor=tk.W)

        # Separator for visual division
        # ttk.Separator(connection_card, orient='horizontal').pack(fill=tk.X, pady=10)

        # Test button in a container for responsiveness
        self.test_button_container = ttk.Frame(connection_card, style='Card.TFrame')
        self.test_button_container.pack(fill=tk.X, pady=12)

        self.test_button = ttk.Button(self.test_button_container, text="Relancer Tests",
                                      command=self.test_connections, style='ModernButton.TButton')
        self.test_button.pack(fill=tk.X, expand=True, pady=5, padx=5)

        # Test results
        self.test_results_label = ttk.Label(connection_card, textvariable=self.test_results_var,
                                            style='Success.TLabel')
        self.test_results_label.pack(anchor=tk.W, pady=8)

    def create_system_info(self, parent):
        """Create System Information card."""
        info_card = self.create_card(parent, "Informations Système")

        # Component status indicators with checkmarks
        self.collector_status_label = ttk.Label(info_card, textvariable=self.collector_status_var,
                                                style='Success.TLabel')
        self.collector_status_label.pack(anchor=tk.W, pady=8)

        self.uploader_status_label = ttk.Label(info_card, textvariable=self.uploader_status_var,
                                               style='Success.TLabel')
        self.uploader_status_label.pack(anchor=tk.W, pady=8)

        self.user_importer_status_label = ttk.Label(info_card, textvariable=self.user_importer_status_var,
                                                    style='Success.TLabel')
        self.user_importer_status_label.pack(anchor=tk.W, pady=8)

        # Separator with more pronounced visual appearance
        separator = ttk.Separator(info_card, orient='horizontal')
        separator.pack(fill=tk.X, pady=15)

        # Timestamp information with improved spacing
        ttk.Label(info_card, textvariable=self.last_collection_var, style='Card.TLabel').pack(anchor=tk.W, pady=5)
        ttk.Label(info_card, textvariable=self.last_upload_var, style='Card.TLabel').pack(anchor=tk.W, pady=5)
        ttk.Label(info_card, textvariable=self.last_import_var, style='Card.TLabel').pack(anchor=tk.W, pady=5)

    def on_window_resize(self, event):
        """Handle window resize events."""
        # Only respond to resize events for the main window, not child widgets
        if event.widget == self.root:
            # Avoid excessive updates by checking if width changed significantly
            if (self.current_layout == "single" and event.width > self.MIN_WIDTH + 120) or \
                    (self.current_layout == "dual" and event.width <= self.MIN_WIDTH + 100):
                # Wait a short time and then update layout
                self.root.after(100, self.create_responsive_layout)

            # Update system control buttons layout based on width
            if hasattr(self, 'system_buttons_container'):
                if event.width < 500:  # For small screens
                    # Stack system buttons vertically
                    for child in self.system_buttons_container.winfo_children():
                        child.pack_forget()
                        child.pack(side=tk.TOP, fill=tk.X, expand=True, pady=2, padx=5)
                else:
                    # Horizontal system button layout
                    for child in self.system_buttons_container.winfo_children():
                        child.pack_forget()
                        child.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

            # Update test button layout
            if hasattr(self, 'test_button_container') and hasattr(self, 'test_button'):
                if event.width < 400:  # Very small screens
                    # Use a more compact label
                    self.test_button.config(text="Tests")
                else:
                    self.test_button.config(text="Relancer Tests")

            # Update toolbar button layout based on width
            if hasattr(self, 'button_container'):
                if event.width < 400:  # Very small screens
                    # Stack buttons vertically
                    for child in self.button_container.winfo_children():
                        child.pack_forget()
                        child.pack(side=tk.TOP, fill=tk.X, expand=True, pady=2, padx=5)
                else:
                    # Horizontal button layout
                    for child in self.button_container.winfo_children():
                        child.pack_forget()
                        child.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

    def create_card(self, parent, title, with_status=False):
        """Create a card with the given title in the parent frame."""
        # Create an outer frame that will have the background color
        outer_frame = ttk.Frame(parent, style='Card.TFrame')
        outer_frame.pack(fill=tk.BOTH, expand=True, pady=15)

        # Create rounded corners with Canvas
        card_canvas = tk.Canvas(outer_frame, bg=self.COLOR_CARD,
                                highlightthickness=0)
        card_canvas.pack(fill=tk.BOTH, expand=True)

        # Set minimum width for the canvas to prevent squashing
        card_canvas.config(width=200, height=120)

        # Draw rounded rectangle - we'll update this when the canvas resizes
        card_canvas.bind("<Configure>", lambda e, c=card_canvas: self.update_card_corners(c))

        # Content frame inside the canvas
        content_frame = ttk.Frame(card_canvas, style='Card.TFrame')

        # Place the frame in the canvas - we'll update this when the canvas resizes
        card_canvas.create_window(10, 10, window=content_frame,
                                  anchor="nw",
                                  tags="content_window")

        # Update window size when canvas changes
        card_canvas.bind("<Configure>", lambda e, c=card_canvas, f=content_frame:
        self.update_card_content(c, f))

        # Title area with visual header
        title_frame = ttk.Frame(content_frame, style='Card.TFrame')
        title_frame.pack(fill=tk.X, pady=(15, 10), padx=15)

        # Create a row for the title and status (if needed)
        title_row = ttk.Frame(title_frame, style='Card.TFrame')
        title_row.pack(fill=tk.X)

        title_label = ttk.Label(title_row, text=title, style='SectionTitle.TLabel')
        title_label.pack(side=tk.LEFT, anchor=tk.W)

        # Add status indicator if requested
        if with_status:
            # Add spacer
            ttk.Label(title_row, text="  -  ", style='Card.TLabel').pack(side=tk.LEFT)

            # Status indicator
            self.status_label = ttk.Label(title_row, textvariable=self.status_var,
                                          style='Success.TLabel' if self.app.is_running() else 'Error.TLabel')
            self.status_label.pack(side=tk.LEFT)

        # Divider below title
        ttk.Separator(content_frame, orient='horizontal').pack(fill=tk.X, padx=15)

        # Content area with padding
        inner_content_frame = ttk.Frame(content_frame, style='Card.TFrame', padding=(20, 15))
        inner_content_frame.pack(fill=tk.BOTH, expand=True)

        return inner_content_frame

    def update_card_corners(self, canvas):
        """Update card corners when canvas is resized."""
        # Clear canvas
        canvas.delete("corners")

        # Get current dimensions
        width = canvas.winfo_width()
        height = canvas.winfo_height()

        # Draw rounded rectangle
        radius = 12  # Corner radius

        # Draw rectangle parts with a subtle border
        canvas.create_rectangle(radius, 0, width - radius, height,
                                fill=self.COLOR_CARD, outline=self.COLOR_BORDER,
                                width=1, tags="corners")
        canvas.create_rectangle(0, radius, width, height - radius,
                                fill=self.COLOR_CARD, outline=self.COLOR_BORDER,
                                width=1, tags="corners")

        # Draw corner arcs
        canvas.create_arc(0, 0, radius * 2, radius * 2,
                          start=90, extent=90,
                          fill=self.COLOR_CARD, outline=self.COLOR_BORDER,
                          width=1, tags="corners")
        canvas.create_arc(width - (radius * 2), 0, width, radius * 2,
                          start=0, extent=90,
                          fill=self.COLOR_CARD, outline=self.COLOR_BORDER,
                          width=1, tags="corners")
        canvas.create_arc(0, height - (radius * 2), radius * 2, height,
                          start=180, extent=90,
                          fill=self.COLOR_CARD, outline=self.COLOR_BORDER,
                          width=1, tags="corners")
        canvas.create_arc(width - (radius * 2), height - (radius * 2), width, height,
                          start=270, extent=90,
                          fill=self.COLOR_CARD, outline=self.COLOR_BORDER,
                          width=1, tags="corners")

        # Add subtle drop shadow (optional visual enhancement)
        shadow_offset = 3
        shadow_color = "#E0E0E0"

        canvas.create_rectangle(shadow_offset, shadow_offset,
                                width + shadow_offset, height + shadow_offset,
                                fill="", outline=shadow_color,
                                width=0, tags="shadow")

    def update_card_content(self, canvas, frame):
        """Update content frame size when canvas is resized."""
        # Delete and recreate the window to update size
        canvas.delete("content_window")
        width = canvas.winfo_width()
        height = canvas.winfo_height()

        # Update corners
        self.update_card_corners(canvas)

        # Create window with updated dimensions
        canvas.create_window(width / 2, height / 2, window=frame,
                             anchor="center", width=width - 20, height=height - 20,
                             tags="content_window")

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
            global_logo_path = self.resource_path("assets/timesync-logo.png")
            global_logo_img = tk.PhotoImage(file=global_logo_path)
            global_logo_display = global_logo_img.subsample(8, 8)  # Adjust scale as needed
            self.global_logo_img = global_logo_display  # Store reference

            # Load application-specific logo
            app_logo_path = self.resource_path("assets/logo.png")
            app_logo_img = tk.PhotoImage(file=app_logo_path)
            app_logo_display = app_logo_img.subsample(32, 32)  # Adjust scale as needed
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
        config_window = ConfigInterface(self.root, self.app.container.get('config_repository'), self.app)
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