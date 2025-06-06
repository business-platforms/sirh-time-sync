# src/ui/users_interface.py
import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Optional, List

from src.domain.models import User
from src.data.repositories import AttendanceRepository
from src.service.device_service import DeviceService
from src.service.sync_service import SyncService

logger = logging.getLogger(__name__)


class UsersInterface:
    """Interface for managing users in the attendance system."""

    # Define color constants to match MainWindow theme
    COLOR_PRIMARY = "#24398E"  # Blue header color
    COLOR_BACKGROUND = "#FFFFFF"  # White background
    COLOR_SUCCESS = "#4CAF50"  # Green for success states
    COLOR_ERROR = "#F44336"  # Red for error/stopped states
    COLOR_WARNING = "#FF9800"  # Orange for warning states
    COLOR_NEUTRAL = "#757575"  # Gray for neutral states
    COLOR_CARD = "#FFFFFF"  # White card background

    def __init__(
            self,
            root: Optional[tk.Tk],
            users: Optional[List[User]] = None,
            attendance_repository: Optional[AttendanceRepository] = None,
            device_service: Optional[DeviceService] = None,
            sync_service: Optional[SyncService] = None
    ):
        """
        Initialize the users interface.

        Args:
            root: Tkinter root window
            users: List of users to display (will load from device if None)
            attendance_repository: Repository for attendance data
            device_service: Service for device operations
            sync_service: Service for synchronization operations
        """
        self.attendance_repository = attendance_repository
        self.device_service = device_service
        self.sync_service = sync_service
        self.root = tk.Toplevel(root) if root else tk.Tk()
        self.users = users or []

        # Configure window basics
        self.root.title("Gestion des Utilisateurs")
        self.root.geometry("1400x700")
        self.root.minsize(850, 700)
        self.root.withdraw()  # Hide window during setup

        # Status variable for displaying messages
        self.status_var = tk.StringVar(value="Prêt")

        # Set up style
        self.setup_style()

        # Create and configure all UI elements
        self.setup_ui()

        # Load data if not provided and service are available
        if not self.users and self.device_service:
            self.load_users()

        # Populate the user list
        self.refresh_user_list()

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

        # Add LabelFrame style
        style.configure('TLabelframe', background=self.COLOR_BACKGROUND)
        style.configure('TLabelframe.Label', background=self.COLOR_BACKGROUND, font=('Segoe UI', 9, 'bold'))

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
        style.configure('Delete.TButton', padding=8)

        # Treeview styles
        style.configure('Treeview', font=('Segoe UI', 10))
        style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'))

    def setup_ui(self):
        """Create and configure all UI elements."""
        # Create header frame
        header_frame = ttk.Frame(self.root, style='Header.TFrame')
        header_frame.pack(fill=tk.X, side=tk.TOP)

        # Header title
        title_label = ttk.Label(header_frame, text="Gestion des Utilisateurs",
                                style='Header.TLabel')
        title_label.pack(side=tk.LEFT, padx=15, pady=10)

        # Main content area
        main_frame = ttk.Frame(self.root, padding=15, style='TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create action buttons panel under header
        self.create_action_panel(main_frame)

        # Create user list card
        self.create_user_list_card(main_frame)

        # Status indicator at the bottom
        status_frame = ttk.Frame(main_frame, style='TFrame')
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=10)

        self.status_label = ttk.Label(status_frame, textvariable=self.status_var,
                                      style='Neutral.TLabel')
        self.status_label.pack(anchor=tk.W, pady=5)

    def create_card(self, parent, title):
        """Create a card with the given title in the parent frame."""
        # Create an outer frame that will have the background color
        outer_frame = ttk.Frame(parent, style='Card.TFrame')
        outer_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Title area
        title_frame = ttk.Frame(outer_frame, style='Card.TFrame')
        title_frame.pack(fill=tk.X, pady=(10, 5), padx=15)

        title_label = ttk.Label(title_frame, text=title, style='SectionTitle.TLabel')
        title_label.pack(anchor=tk.W)

        # Content area with padding
        inner_content_frame = ttk.Frame(outer_frame, style='Card.TFrame', padding=(15, 10))
        inner_content_frame.pack(fill=tk.BOTH, expand=True)

        return inner_content_frame

    def create_action_panel(self, parent):
        """Create panel with action buttons."""
        button_frame = ttk.Frame(parent, style='TFrame')
        button_frame.pack(fill=tk.X, pady=(10, 5))

        # Create three separate frames for button groups
        left_frame = ttk.Frame(button_frame, style='TFrame')
        left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        middle_frame = ttk.Frame(button_frame, style='TFrame')
        middle_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        right_frame = ttk.Frame(button_frame, style='TFrame')
        right_frame.pack(side=tk.RIGHT, fill=tk.X, padx=(0, 10))

        # Data operations group (left)
        data_frame = ttk.LabelFrame(left_frame, text="Opérations de données", style='TFrame')
        data_frame.pack(side=tk.LEFT, padx=(10, 5), pady=5)

        # Import Users button
        self.import_button = ttk.Button(
            data_frame,
            text="📥 Importer des Utilisateurs",
            command=self.import_users,
            style='Action.TButton'
        )
        self.import_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Refresh button
        refresh_button = ttk.Button(
            data_frame,
            text="🔄 Actualiser la Liste",
            command=self.refresh_data,
            style='Action.TButton'
        )
        refresh_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Selection operations group (middle)
        selection_frame = ttk.LabelFrame(middle_frame, text="Sélection", style='TFrame')
        selection_frame.pack(side=tk.LEFT, padx=5, pady=5)

        # Select All button
        select_all_button = ttk.Button(
            selection_frame,
            text="✓ Tout Sélectionner",
            command=self.select_all_users,
            style='Action.TButton'
        )
        select_all_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Add a Deselect All button for better user experience
        deselect_all_button = ttk.Button(
            selection_frame,
            text="✗ Tout Désélectionner",
            command=self.deselect_all_users,  # Need to add this method
            style='Action.TButton'
        )
        deselect_all_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Destructive operations group (right)
        delete_frame = ttk.LabelFrame(right_frame, text="Actions", style='TFrame')
        delete_frame.pack(side=tk.RIGHT, padx=5, pady=5)

        # Delete User button
        self.delete_button = ttk.Button(
            delete_frame,
            text="🗑️ Supprimer Utilisateur(s)",
            command=self.delete_users,
            style='Delete.TButton'
        )
        self.delete_button.pack(side=tk.LEFT, padx=5, pady=5)

    def resource_path(self, relative_path):
        """Get absolute path to resource, works for dev and for PyInstaller."""
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    def create_user_list_card(self, parent):
        """Create card containing the user list."""
        card = self.create_card(parent, "Liste des Utilisateurs")

        # Create Treeview with scrollbars
        tree_frame = ttk.Frame(card, style='Card.TFrame')
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Define columns - now including all three fields
        columns = ("id", "user_id", "name")
        # Changed selectmode from "browse" to "extended" to allow multi-selection
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="extended")

        # Configure column headings
        self.tree.heading("id", text="ID (UID)")
        self.tree.heading("user_id", text="ID Utilisateur")
        self.tree.heading("name", text="Code Employé")

        # Configure column widths and alignment
        self.tree.column("id", width=100, anchor=tk.CENTER)
        self.tree.column("user_id", width=150, anchor=tk.CENTER)
        self.tree.column("name", width=450, anchor=tk.W)

        # Add vertical scrollbar
        vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)

        # Add horizontal scrollbar
        hsb = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(xscroll=hsb.set)

        # Position scrollbars and treeview using grid
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # Configure grid weights
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Double-click event
        self.tree.bind("<Double-1>", self.on_user_double_click)

    def show(self):
        """Make the window visible and set focus."""
        self.root.grab_set()  # Make this window modal
        self.root.transient(self.root.master)
        self.root.focus_set()  # Set keyboard focus

    def load_users(self):
        """Load users from the device service."""
        if not self.device_service:
            self.status_var.set("Service de l'appareil non disponible")
            self.status_label.config(style='Error.TLabel')
            return

        try:
            # Update status
            self.status_var.set("Chargement des utilisateurs...")
            self.status_label.config(style='Warning.TLabel')
            self.root.update()  # Force UI update

            # Retrieve users from the device service
            self.users = self.device_service.get_users()

            if not self.users:
                logger.info("No users found from device service.")
                self.status_var.set("Aucun utilisateur trouvé")
                self.status_label.config(style='Warning.TLabel')
                return

            logger.info(f"Loaded {len(self.users)} users from device service")
            self.status_var.set(f"{len(self.users)} utilisateurs chargés")
            self.status_label.config(style='Success.TLabel')

        except Exception as e:
            self.handle_error("Erreur lors du chargement des utilisateurs", e)

    def refresh_data(self):
        """Refresh the user data and update the display."""
        self.load_users()
        self.refresh_user_list()

    def import_users(self):
        """Import users using the sync service."""
        if not self.sync_service:
            self.status_var.set("Service de synchronisation non disponible")
            self.status_label.config(style='Error.TLabel')
            return

        try:
            self.status_var.set("Importation des utilisateurs...")
            self.status_label.config(style='Warning.TLabel')
            self.root.update()  # Force UI update

            threading.Thread(target=self.sync_service.import_users_from_api_to_device, daemon=True).start()
            self.show_success(f"Le processus d'importation est en cours d'exécution en arrière-plan.")

            # Reload the user list after import
            self.load_users()

            # Refresh the display
            self.refresh_user_list()

        except Exception as e:
            self.handle_error("Erreur lors de l'importation des utilisateurs", e)

    def delete_users(self):
        """Delete selected users using the device service."""
        if not self.device_service:
            self.status_var.set("Service de l'appareil non disponible")
            self.status_label.config(style='Error.TLabel')
            return

        # Get selected users
        selected_items = self.tree.selection()
        if not selected_items:
            self.show_error("Veuillez sélectionner au moins un utilisateur à supprimer.")
            return

        # Collect UIDs and names for all selected users
        uids = []
        user_info = []
        for item in selected_items:
            values = self.tree.item(item, "values")
            uid = int(values[0])  # The ID/UID is the first column
            name = values[2]  # The name is the third column
            uids.append(uid)
            user_info.append(f"{name} (UID: {uid})")

        # Create confirmation message based on number of selected users
        if len(uids) == 1:
            confirm_message = f"Êtes-vous sûr de vouloir supprimer l'utilisateur {user_info[0]}?"
        else:
            confirm_message = f"Êtes-vous sûr de vouloir supprimer les {len(uids)} utilisateurs suivants?\n\n"
            # Add list of users to be deleted (limit to first 5 if too many)
            if len(user_info) <= 5:
                confirm_message += "\n".join(f"- {info}" for info in user_info)
            else:
                confirm_message += "\n".join(f"- {info}" for info in user_info[:5])
                confirm_message += f"\n... et {len(user_info) - 5} autres"

        # Confirm deletion
        if not messagebox.askyesno("Confirmer la suppression", confirm_message, parent=self.root):
            return

        try:
            # Update status
            self.status_var.set("Suppression des utilisateurs...")
            self.status_label.config(style='Warning.TLabel')
            self.root.update()  # Force UI update

            # Delete users from device using the new bulk delete method
            batch_size = 50
            for i in range(0, len(uids), batch_size):
                batch = uids[i:i + batch_size]
                thread = threading.Thread(
                    target=self.device_service.delete_users,
                    args=(batch,),
                    daemon=True
                )
                thread.start()
            self.show_success(f"Le processus d'importation est en cours d'exécution en arrière-plan.")

            # Refresh the display
            self.refresh_user_list()


        except Exception as e:
            self.handle_error("Erreur lors de la suppression des utilisateurs", e)

    def refresh_user_list(self):
        """Update the treeview with current user data."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # If no users, display a message in the status bar
        if not self.users or len(self.users) == 0:
            self.status_var.set("Aucun utilisateur à afficher")
            self.status_label.config(style='Warning.TLabel')
            return

        # Insert user data into the treeview
        for user in self.users:
            # Handle different types of user objects
            if hasattr(user, 'id') and hasattr(user, 'user_id') and hasattr(user, 'name'):
                # Complete user object with all fields
                uid = user.id
                user_id = user.user_id
                name = user.name
            elif hasattr(user, 'user_id') and hasattr(user, 'name'):
                # User with user_id and name but missing id
                uid = user.user_id  # Use user_id as fallback for uid
                user_id = user.user_id
                name = user.name
            elif isinstance(user, dict):
                # Dictionary representation of user
                uid = user.get('id', user.get('user_id', 'N/A'))
                user_id = user.get('user_id', 'N/A')
                name = user.get('name', 'N/A')
            else:
                # Unknown format
                uid = 'N/A'
                user_id = 'N/A'
                name = 'N/A'

            self.tree.insert("", tk.END, values=(uid, user_id, name))

        # Update status message
        self.status_var.set(f"Affichage de {len(self.users)} utilisateurs")
        self.status_label.config(style='Success.TLabel')

    def on_user_double_click(self, event):
        """Handle double-click on a user row (placeholder for future functionality)."""
        if not self.tree.selection():
            return

        item = self.tree.selection()[0]
        values = self.tree.item(item, "values")
        uid = values[0]
        user_id = values[1]
        name = values[2]

        # Placeholder for future user detail view
        self.status_var.set(f"Utilisateur sélectionné: {name} (UID: {uid}, ID: {user_id})")
        self.status_label.config(style='Neutral.TLabel')

    def select_all_users(self):
        """Select all users in the treeview."""
        # Clear current selection
        self.tree.selection_remove(self.tree.selection())

        # Select all items
        for item in self.tree.get_children():
            self.tree.selection_add(item)

        # Update status
        items_count = len(self.tree.get_children())
        if items_count > 0:
            self.status_var.set(f"{items_count} utilisateurs sélectionnés")
            self.status_label.config(style='Neutral.TLabel')

    def deselect_all_users(self):
        """Deselect all users in the treeview."""
        # Clear current selection
        self.tree.selection_remove(self.tree.selection())

        # Update status
        self.status_var.set("Sélection effacée")
        self.status_label.config(style='Neutral.TLabel')

    def show_error(self, message: str):
        """Show an error message dialog and update status bar."""
        self.status_var.set(f"Erreur: {message}")
        self.status_label.config(style='Error.TLabel')
        messagebox.showerror("Erreur", message, parent=self.root)

    def show_success(self, message: str):
        """Show a success message dialog and update status bar."""
        self.status_var.set(message)
        self.status_label.config(style='Success.TLabel')
        messagebox.showinfo("Succès", message, parent=self.root)

    def handle_error(self, message: str, exception: Exception):
        """Log and display errors with context."""
        error_msg = f"{message}: {exception}"
        logger.error(error_msg)
        self.show_error(error_msg)