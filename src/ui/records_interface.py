# src/ui/records_interface.py
import ast
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from src.domain.models import AttendanceRecord, User, ProcessedStatus, PunchType
from src.data.repositories import AttendanceRepository
from src.service.attendance_service import AttendanceService
from src.service.sync_service import SyncService

logger = logging.getLogger(__name__)


class RecordsInterface:
    """Interface for managing attendance records."""

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
            attendance_service: Optional[AttendanceService] = None,
            sync_service: Optional[SyncService] = None
    ):
        """
        Initialize the RecordsInterface.

        Args:
            root: Parent Tkinter window
            users: List of users
            attendance_repository: Repository for attendance records
            attendance_service: Service for attendance operations
            sync_service: Service for synchronization operations
        """
        self.attendance_repository = attendance_repository
        self.attendance_service = attendance_service
        self.sync_service = sync_service
        self.root = tk.Toplevel(root) if root else tk.Tk()
        self.users = users or []

        # Configure window basics
        self.root.title("Enregistrements de Présence")
        self.root.geometry("1300x750")
        self.root.minsize(1000, 700)
        self.root.withdraw()  # Hide window during setup

        self.status_var = tk.StringVar(value="Prêt")
        self.records: List[AttendanceRecord] = []

        # Filter variables
        self.filter_var = tk.StringVar(value="all")  # Default to showing all records
        self.sort_var = tk.StringVar(value="timestamp")  # Default sorting
        self.search_var = tk.StringVar()  # For search functionality

        # Record count variable
        self.record_count_var = tk.StringVar(value="Aucun enregistrement")

        # Set up style
        self.setup_style()

        # Create the UI
        self.setup_ui()

        # Load records and display them
        self.load_records()
        self.display_records()

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
        style.configure('Sync.TButton', padding=10, font=('Segoe UI', 10, 'bold'))

        # LabelFrame styles
        style.configure('Card.TLabelframe', background=self.COLOR_CARD)
        style.configure('Card.TLabelframe.Label', background=self.COLOR_CARD, font=('Segoe UI', 11, 'bold'))

        # Treeview styles
        style.configure('Treeview', font=('Segoe UI', 10), rowheight=25)
        style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'))

    def setup_ui(self):
        """Set up the modern user interface."""
        # Create header frame
        header_frame = ttk.Frame(self.root, style='Header.TFrame')
        header_frame.pack(fill=tk.X, side=tk.TOP)

        # Header title
        title_label = ttk.Label(header_frame, text="Enregistrements de Présence",
                                style='Header.TLabel')
        title_label.pack(side=tk.LEFT, padx=15, pady=10)

        # Record count in header
        count_label = ttk.Label(header_frame, textvariable=self.record_count_var,
                                style='Header.TLabel')
        count_label.pack(side=tk.RIGHT, padx=15, pady=10)

        # Main content area
        main_frame = ttk.Frame(self.root, padding=15, style='TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create search and filter card
        self.create_search_filter_card(main_frame)

        # Create records list card
        self.create_records_card(main_frame)

        # Create action button panel
        self.create_action_panel(main_frame)

        # Status indicator at the bottom
        status_frame = ttk.Frame(main_frame, style='TFrame')
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=10)

        self.status_label = ttk.Label(status_frame, textvariable=self.status_var,
                                      style='Neutral.TLabel')
        self.status_label.pack(anchor=tk.W, pady=5)

    def create_card(self, parent, title):
        """Create a card with the given title in the parent frame."""
        # Create an outer frame that will have the background color
        outer_frame = ttk.LabelFrame(parent, text=title, style='Card.TLabelframe')
        outer_frame.pack(fill=tk.BOTH, expand=False, pady=10)

        # Content area with padding
        inner_content_frame = ttk.Frame(outer_frame, style='Card.TFrame', padding=(15, 10))
        inner_content_frame.pack(fill=tk.BOTH, expand=True)

        return inner_content_frame

    def create_search_filter_card(self, parent):
        """Create the search and filter controls card."""
        card = self.create_card(parent, "Recherche et Filtres")

        # Create two frames side by side
        left_frame = ttk.Frame(card, style='Card.TFrame')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        right_frame = ttk.Frame(card, style='Card.TFrame')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        # Search controls in left frame
        search_frame = ttk.Frame(left_frame, style='Card.TFrame')
        search_frame.pack(fill=tk.X, pady=5)

        ttk.Label(search_frame, text="Rechercher:", style='Card.TLabel').pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(search_frame, textvariable=self.search_var).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(search_frame, text="Rechercher", command=self.apply_filter, style='Action.TButton').pack(
            side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Réinitialiser", command=self.reset_search, style='Action.TButton').pack(
            side=tk.LEFT, padx=5)

        # Filter controls in right frame
        filter_frame = ttk.Frame(right_frame, style='Card.TFrame')
        filter_frame.pack(fill=tk.X, pady=5)

        # Filter radio buttons
        ttk.Label(filter_frame, text="Filtre:", style='Card.TLabel').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(filter_frame, text="Tous", variable=self.filter_var, value="all").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(filter_frame, text="Traités", variable=self.filter_var, value=ProcessedStatus.PROCESSED).pack(
            side=tk.LEFT, padx=5)
        ttk.Radiobutton(filter_frame, text="Non Traités", variable=self.filter_var,
                        value=ProcessedStatus.UNPROCESSED).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(filter_frame, text="Erreur", variable=self.filter_var, value=ProcessedStatus.ERROR).pack(
            side=tk.LEFT, padx=5)

        # Sort options
        sort_frame = ttk.Frame(right_frame, style='Card.TFrame')
        sort_frame.pack(fill=tk.X, pady=5)

        ttk.Label(sort_frame, text="Trier par:", style='Card.TLabel').pack(side=tk.LEFT, padx=(0, 10))
        sort_combo = ttk.Combobox(sort_frame, textvariable=self.sort_var, width=15,
                                  values=["timestamp", "username", "id", "punch_type"])
        sort_combo.pack(side=tk.LEFT, padx=5)

        ttk.Button(sort_frame, text="Appliquer Filtre", command=self.apply_filter, style='Action.TButton').pack(
            side=tk.LEFT, padx=(20, 0))

    def resource_path(self, relative_path):
        """Get absolute path to resource, works for dev and for PyInstaller."""
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    def create_records_card(self, parent):
        """Create the card containing the records table."""
        self.records_frame = self.create_card(parent, "Liste des Enregistrements")
        # The actual treeview will be created in display_records()

    def create_action_panel(self, parent):
        """Create the panel with action buttons."""
        action_frame = ttk.Frame(parent, style='TFrame')
        action_frame.pack(fill=tk.X, pady=10)

        # Left side - CRUD operations
        crud_frame = ttk.Frame(action_frame, style='TFrame')
        crud_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(crud_frame, text="📝 Ajouter un Enregistrement", command=self.add_record,
                   style='Action.TButton').pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(crud_frame, text="✏️ Modifier l'Enregistrement", command=self.update_record,
                   style='Action.TButton').pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(crud_frame, text="🗑️ Supprimer l'Enregistrement", command=self.delete_record,
                   style='Action.TButton').pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(crud_frame, text="⚠️ Voir les Erreurs", command=self.view_errors,
                   style='Action.TButton').pack(side=tk.LEFT, padx=5, pady=5)

        # Right side - Synchronize button
        sync_frame = ttk.Frame(action_frame, style='TFrame')
        sync_frame.pack(side=tk.RIGHT, fill=tk.X)

        sync_btn = ttk.Button(sync_frame, text="🔄 SYNCHRONISER", command=self.synchronize_records,
                              style='Sync.TButton')
        sync_btn.pack(side=tk.RIGHT, padx=5, pady=5)

    def show(self):
        """Display the records window as a modal dialog."""
        self.root.grab_set()
        self.root.transient(self.root.master)
        self.root.focus_set()

    def load_records(self):
        """Load attendance records based on current filter."""
        try:
            if not self.attendance_repository:
                self.status_var.set("Référentiel d'enregistrements non disponible")
                self.status_label.config(style='Error.TLabel')
                return

            filter_value = self.filter_var.get()
            order_by = self.sort_var.get()
            search_term = self.search_var.get()

            # Convert filter value to the appropriate parameter
            filter_processed = None  # Default to all records
            if filter_value == ProcessedStatus.PROCESSED:
                filter_processed = ProcessedStatus.PROCESSED
            elif filter_value == ProcessedStatus.UNPROCESSED:
                filter_processed = ProcessedStatus.UNPROCESSED
            elif filter_value == ProcessedStatus.ERROR:
                filter_processed = ProcessedStatus.ERROR

            # Get records from repository
            self.records = self.attendance_repository.get_records(
                processed_status=filter_processed,
                order_by=order_by
            )

            # Apply search filter if provided
            if search_term:
                search_term = search_term.lower()
                self.records = [
                    r for r in self.records if
                    search_term in str(r.username).lower() or
                    search_term in str(r.timestamp).lower()
                ]

            # Update record count
            if not self.records:
                logger.info(f"No {filter_value} attendance records found.")
                self.record_count_var.set("0 enregistrements trouvés")
                self.status_var.set("Aucun enregistrement trouvé")
                self.status_label.config(style='Warning.TLabel')
            else:
                self.record_count_var.set(f"{len(self.records)} enregistrements")
                self.status_var.set(f"{len(self.records)} enregistrements chargés")
                self.status_label.config(style='Success.TLabel')
                logger.info(f"Loaded {len(self.records)} {filter_value} attendance records.")

        except Exception as e:
            self.handle_error("Erreur lors du chargement des enregistrements", e)
            self.records = []
            self.record_count_var.set("Erreur de chargement")

    def display_records(self):
        """Display the attendance records in the treeview."""
        # Clear previous records display
        for widget in self.records_frame.winfo_children():
            widget.destroy()

        # Create a frame for the treeview and scrollbars
        tree_container = ttk.Frame(self.records_frame, style='Card.TFrame')
        tree_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create the Treeview
        columns = ("id", "username", "timestamp", "punch_type", "processed")
        self.tree = ttk.Treeview(tree_container, columns=columns, show="headings", selectmode="browse")

        # Define headings
        self.tree.heading("id", text="ID", command=lambda: self.sort_treeview("id"))
        self.tree.heading("username", text="Code Employé", command=lambda: self.sort_treeview("username"))
        self.tree.heading("timestamp", text="Horodatage", command=lambda: self.sort_treeview("timestamp"))
        self.tree.heading("punch_type", text="Type de Pointage", command=lambda: self.sort_treeview("punch_type"))
        self.tree.heading("processed", text="Statut", command=lambda: self.sort_treeview("processed"))

        # Define columns
        self.tree.column("id", width=50, anchor=tk.CENTER)
        self.tree.column("username", width=150, anchor=tk.CENTER)
        self.tree.column("timestamp", width=220, anchor=tk.CENTER)
        self.tree.column("punch_type", width=120, anchor=tk.CENTER)
        self.tree.column("processed", width=120, anchor=tk.CENTER)

        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.tree.yview)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        h_scrollbar = ttk.Scrollbar(tree_container, orient=tk.HORIZONTAL, command=self.tree.xview)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Insert records into the Treeview
        for record in self.records:
            # Format punch type display
            punch_text = "Entrée" if record.punch_type == PunchType.IN else "Sortie"

            # Format processed status display
            if record.processed == ProcessedStatus.PROCESSED:
                processed_text = "Traité"
            elif record.processed == ProcessedStatus.UNPROCESSED:
                processed_text = "Non Traité"
            elif record.processed == ProcessedStatus.ERROR:
                error_count = len(record.errors) if hasattr(record, 'errors') and record.errors else 0
                processed_text = f"Erreur ({error_count})" if error_count else "Erreur"
            else:
                processed_text = "Inconnu"

            self.tree.insert("", tk.END, values=(
                record.id,
                record.username,
                record.timestamp if record.timestamp else "N/A",
                punch_text,
                processed_text
            ))

        # Add right-click menu
        self.create_context_menu()

    def reset_search(self):
        """Reset search field and reload records."""
        self.search_var.set("")
        self.apply_filter()

    def apply_filter(self):
        """Apply the selected filter and sort options."""
        self.load_records()
        self.display_records()

    def sort_treeview(self, column):
        """Set the sort column and refresh the display."""
        self.sort_var.set(column)
        self.apply_filter()

    def create_context_menu(self):
        """Create a right-click context menu for the treeview."""
        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label="Modifier l'Enregistrement", command=self.update_record)
        self.context_menu.add_command(label="Supprimer l'Enregistrement", command=self.delete_record)
        self.context_menu.add_command(label="Voir les Erreurs", command=self.view_errors)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Marquer comme Traité",
                                      command=lambda: self.toggle_processed_status(ProcessedStatus.PROCESSED))
        self.context_menu.add_command(label="Marquer comme Non Traité",
                                      command=lambda: self.toggle_processed_status(ProcessedStatus.UNPROCESSED))
        self.context_menu.add_command(label="Marquer comme Erreur",
                                      command=lambda: self.toggle_processed_status(ProcessedStatus.ERROR))

        self.tree.bind("<Button-3>", self.show_context_menu)
        # Double-click to view errors if record has error status
        self.tree.bind("<Double-1>", self.on_double_click)

    def show_context_menu(self, event):
        """Show the context menu on right-click."""
        # Select row under mouse
        iid = self.tree.identify_row(event.y)
        if iid:
            self.tree.selection_set(iid)
            self.context_menu.post(event.x_root, event.y_root)

    def on_double_click(self, event):
        """Handle double-click on treeview items."""
        selected_item = self.tree.selection()
        if not selected_item:
            return

        record_values = self.tree.item(selected_item, "values")
        processed_status = record_values[4]

        # If the record has error status, show errors
        if "Erreur" in processed_status:
            self.view_errors()

    def toggle_processed_status(self, processed_status):
        """Toggle the processed status of a record."""
        if not self.attendance_service:
            self.show_error("Service d'enregistrement non disponible")
            return

        selected_item = self.tree.selection()
        if not selected_item:
            self.show_error("Veuillez sélectionner un enregistrement.")
            return

        record_values = self.tree.item(selected_item, "values")
        record_id = int(record_values[0])

        record = next((r for r in self.records if r.id == record_id), None)
        if not record:
            self.show_error("Enregistrement non trouvé.")
            return

        try:
            # Update record processed status
            record.processed = processed_status

            # If changing to error status, prompt for error details
            if processed_status == ProcessedStatus.ERROR and (not hasattr(record, 'errors') or not record.errors):
                self.add_error_to_record(record)

            # If changing from error to another status, clear errors
            if processed_status != ProcessedStatus.ERROR and hasattr(record, 'errors') and record.errors:
                record.errors = []

            # Update record in repository
            self.attendance_repository.update_record(record)

            # Show success message
            status_map = {
                ProcessedStatus.PROCESSED: "Traité",
                ProcessedStatus.UNPROCESSED: "Non Traité",
                ProcessedStatus.ERROR: "Erreur"
            }
            self.show_success(f"Enregistrement marqué comme {status_map.get(processed_status, 'inconnu')} avec succès.")

            # Refresh display
            self.load_records()
            self.display_records()

        except Exception as e:
            self.handle_error(f"Erreur lors de la mise à jour de l'enregistrement", e)

    def add_error_to_record(self, record):
        """Add error information to a record."""
        # Create a dialog to add error details
        error_window = tk.Toplevel(self.root)
        error_window.title("Ajouter des Détails d'Erreur")
        error_window.geometry("400x300")
        error_window.transient(self.root)
        error_window.grab_set()

        # Set window style
        error_window.configure(background=self.COLOR_BACKGROUND)

        # Create a frame with padding
        main_frame = ttk.Frame(error_window, padding=10, style='TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="Ajouter des Détails d'Erreur",
                                font=("Segoe UI", 12, "bold"), style='Title.TLabel')
        title_label.pack(pady=(0, 10))

        # Form fields
        form_frame = ttk.Frame(main_frame, style='TFrame')
        form_frame.pack(fill=tk.BOTH, expand=True)

        # Field entry
        ttk.Label(form_frame, text="Champ:", style='TLabel').grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        field_var = tk.StringVar(value="entry")
        field_combo = ttk.Combobox(form_frame, textvariable=field_var,
                                   values=["entry", "timestamp", "punch_type", "username"])
        field_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W + tk.E)

        # Error code entry
        ttk.Label(form_frame, text="Code d'Erreur:", style='TLabel').grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        code_var = tk.StringVar(value="E4")
        code_entry = ttk.Entry(form_frame, textvariable=code_var)
        code_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W + tk.E)

        # Error message entry
        ttk.Label(form_frame, text="Message d'Erreur:", style='TLabel').grid(row=2, column=0, sticky=tk.W, padx=5,
                                                                             pady=5)
        message_var = tk.StringVar(value="Pointages qui se chevauchent")
        message_entry = ttk.Entry(form_frame, textvariable=message_var)
        message_entry.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W + tk.E)

        # Validation and submission
        def submit():
            field = field_var.get().strip()
            code = code_var.get().strip()
            message = message_var.get().strip()

            if not field or not code or not message:
                messagebox.showerror("Erreur de Validation", "Tous les champs sont obligatoires", parent=error_window)
                return

            # Add error to record
            if not hasattr(record, 'errors') or record.errors is None:
                record.errors = []

            record.errors.append({
                "field": field,
                "code": code,
                "message": message
            })

            # Ensure processed status is set to ERROR
            record.processed = ProcessedStatus.ERROR

            # Update database
            self.attendance_repository.update_record(record)

            # Refresh display
            self.load_records()
            self.display_records()
            error_window.destroy()

        # Buttons
        button_frame = ttk.Frame(main_frame, style='TFrame')
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(button_frame, text="Annuler", command=error_window.destroy,
                   style='TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Ajouter Erreur", command=submit,
                   style='Action.TButton').pack(side=tk.RIGHT, padx=5)

    def view_errors(self):
        """View errors for the selected record."""
        selected_item = self.tree.selection()
        if not selected_item:
            self.show_error("Veuillez sélectionner un enregistrement pour voir les erreurs.")
            return

        record_values = self.tree.item(selected_item, "values")
        record_id = int(record_values[0])
        processed_status = record_values[4]

        record = next((r for r in self.records if r.id == record_id), None)
        if not record:
            self.show_error("Enregistrement non trouvé.")
            return

        if not "Erreur" in processed_status or not hasattr(record, 'errors') or not record.errors:
            self.show_error("Aucune erreur à afficher pour cet enregistrement.")
            return

        # Display errors in a new window
        error_window = tk.Toplevel(self.root)
        error_window.title(f"Erreurs pour l'Enregistrement #{record_id}")
        error_window.geometry("600x400")
        error_window.transient(self.root)
        error_window.grab_set()

        # Set window style
        error_window.configure(background=self.COLOR_BACKGROUND)

        # Create a frame with padding
        main_frame = ttk.Frame(error_window, padding=10, style='TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text=f"Erreurs pour l'Enregistrement #{record_id}",
                                font=("Segoe UI", 12, "bold"), style='Title.TLabel')
        title_label.pack(pady=(0, 10))

        # Create a treeview to display errors
        error_frame = ttk.Frame(main_frame, style='TFrame')
        error_frame.pack(fill=tk.BOTH, expand=True)

        # Create the Treeview for errors
        error_tree = ttk.Treeview(error_frame, columns=("field", "code", "message"), show="headings")
        error_tree.heading("field", text="Champ")
        error_tree.heading("code", text="Code d'Erreur")
        error_tree.heading("message", text="Message")

        error_tree.column("field", width=100, anchor=tk.CENTER)
        error_tree.column("code", width=100, anchor=tk.CENTER)
        error_tree.column("message", width=350, anchor=tk.W)

        # Add scrollbars
        v_scrollbar = ttk.Scrollbar(error_frame, orient=tk.VERTICAL, command=error_tree.yview)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        h_scrollbar = ttk.Scrollbar(error_frame, orient=tk.HORIZONTAL, command=error_tree.xview)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        error_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        error_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Process errors list
        errors = record.errors
        if isinstance(errors, str):
            errors = self.convert_error_string_to_table(errors)

        # Insert errors into the treeview
        for error in errors:
            if isinstance(error, dict):
                field = error.get("field", "N/A")
                code = error.get("code", "N/A")
                message = error.get("message", "N/A")
            else:
                field = "N/A"
                code = "N/A"
                message = str(error)

            error_tree.insert("", tk.END, values=(field, code, message))

        # Buttons for error management
        button_frame = ttk.Frame(main_frame, style='TFrame')
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(button_frame, text="Ajouter Erreur",
                   command=lambda: self.add_error_to_record(record),
                   style='Action.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Supprimer l'Erreur Sélectionnée",
                   command=lambda: self.delete_selected_error(record, error_tree),
                   style='Action.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Fermer",
                   command=lambda: self.close_error_window(error_window, record),
                   style='TButton').pack(side=tk.RIGHT, padx=5)

    def convert_error_string_to_table(self, errors_str):
        """Convert an error string to a list of error dictionaries."""
        try:
            table = ast.literal_eval(errors_str)
            if isinstance(table, dict):
                table = [table]
            return table
        except Exception as e:
            logger.error(f"Error converting error string to table: {e}")
            return []

    def delete_selected_error(self, record, error_tree):
        """Delete the selected error from a record."""
        selected_item = error_tree.selection()
        if not selected_item:
            messagebox.showerror("Erreur", "Veuillez sélectionner une erreur à supprimer",
                                 parent=error_tree.winfo_toplevel())
            return

        index = error_tree.index(selected_item)
        if 0 <= index < len(record.errors):
            # Remove error from record
            record.errors.pop(index)
            error_tree.delete(selected_item)

            # If no more errors, change status to unprocessed
            if not record.errors:
                record.processed = ProcessedStatus.UNPROCESSED

            # Update record in database
            self.attendance_repository.update_record(record)

            # Refresh display
            self.load_records()
            self.display_records()

    def close_error_window(self, window, record=None):
        """Close the error window and update the record if needed."""
        if record:
            self.attendance_repository.update_record(record)
            self.load_records()
            self.display_records()
        window.destroy()

    def add_record(self):
        """Open a form to add a new attendance record."""
        form = tk.Toplevel(self.root)
        form.title("Ajouter un Enregistrement de Présence")
        form.transient(self.root)
        form.grab_set()
        form.configure(background=self.COLOR_BACKGROUND)

        # Create a frame with padding
        main_frame = ttk.Frame(form, padding=10, style='TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="Ajouter un Nouvel Enregistrement",
                                font=("Segoe UI", 12, "bold"), style='Title.TLabel')
        title_label.pack(pady=(0, 10))

        # Form fields in a grid layout
        form_frame = ttk.Frame(main_frame, style='TFrame')
        form_frame.pack(fill=tk.BOTH, padx=5, pady=5)

        # Create form fields
        fields = (
            ("username", "Code Employé"),
            ("timestamp", "Horodatage (AAAA-MM-JJ HH:MM:SS)"),
            ("punch_type", "Type de Pointage"),
            ("processed", "Statut")
        )
        entries = {}

        # Build form fields
        for idx, (field, label) in enumerate(fields):
            ttk.Label(form_frame, text=label + ":", style='TLabel').grid(row=idx, column=0, sticky=tk.W, padx=5, pady=5)

            if field == "punch_type":
                var = tk.IntVar(value=0)  # Default to IN (0)
                combo = ttk.Combobox(form_frame, textvariable=var, values=[
                    "0 - Entrée",
                    "1 - Sortie"
                ])
                combo.current(0)
                combo.grid(row=idx, column=1, padx=5, pady=5, sticky=tk.W + tk.E)
                entries[field] = var
            elif field == "processed":
                var = tk.StringVar(value=ProcessedStatus.UNPROCESSED)
                combo = ttk.Combobox(form_frame, textvariable=var, values=[
                    ProcessedStatus.UNPROCESSED + " - Non Traité",
                    ProcessedStatus.PROCESSED + " - Traité",
                    ProcessedStatus.ERROR + " - Erreur"
                ])
                combo.current(0)
                combo.grid(row=idx, column=1, padx=5, pady=5, sticky=tk.W + tk.E)
                entries[field] = var
            else:
                var = tk.StringVar()
                entry = ttk.Entry(form_frame, textvariable=var)
                entry.grid(row=idx, column=1, padx=5, pady=5, sticky=tk.W + tk.E)
                entries[field] = var

        def submit():
            try:
                # Validate fields
                username = entries["username"].get().strip()
                timestamp = entries["timestamp"].get().strip()

                if not username or not timestamp:
                    self.show_error("Le code employé et l'horodatage sont des champs obligatoires.")
                    return

                # Get punch type value
                punch_type_val = entries["punch_type"].get()
                if isinstance(punch_type_val, str) and " - " in punch_type_val:
                    punch_type = int(punch_type_val.split(" - ")[0])
                else:
                    punch_type = int(punch_type_val)

                # Get processed status value
                processed_val = entries["processed"].get()
                if isinstance(processed_val, str) and " - " in processed_val:
                    processed = processed_val.split(" - ")[0]
                else:
                    processed = processed_val

                # Create new record
                record = AttendanceRecord(
                    username=username,
                    timestamp=timestamp,
                    punch_type=punch_type,
                    processed=processed,
                    user_id=0,  # This would be set based on username lookup
                    status=1  # Default status
                )

                # Find user ID if possible
                if self.users:
                    user = next((u for u in self.users if u.name == username), None)
                    if user:
                        record.user_id = user.user_id

                # Save record using service or repository
                if self.attendance_service:
                    self.attendance_service.attendance_repository.save_record(record)
                else:
                    self.attendance_repository.save_record(record)

                # Handle error status if needed
                if record.processed == ProcessedStatus.ERROR:
                    # Need to get the saved record with ID first
                    self.load_records()
                    saved_record = next((r for r in self.records if r.username == record.username and
                                         r.timestamp == record.timestamp), None)
                    if saved_record:
                        self.add_error_to_record(saved_record)

                self.show_success("Enregistrement ajouté avec succès.")
                form.destroy()
                self.load_records()
                self.display_records()

            except Exception as e:
                self.handle_error("Erreur lors de l'ajout de l'enregistrement", e)

        # Button frame at the bottom
        button_frame = ttk.Frame(main_frame, style='TFrame')
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(button_frame, text="Annuler", command=form.destroy,
                   style='TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Soumettre", command=submit,
                   style='Action.TButton').pack(side=tk.RIGHT, padx=5)

    def update_record(self):
        """Update the selected attendance record."""
        selected_item = self.tree.selection()
        if not selected_item:
            self.show_error("Veuillez sélectionner un enregistrement à mettre à jour.")
            return

        # Get the selected record's values
        record_values = self.tree.item(selected_item, "values")
        record_id = int(record_values[0])

        # Retrieve the full record
        record = next((r for r in self.records if r.id == record_id), None)
        if not record:
            self.show_error("Enregistrement non trouvé.")
            return

        form = tk.Toplevel(self.root)
        form.title("Mettre à jour l'Enregistrement de Présence")
        form.transient(self.root)
        form.grab_set()
        form.configure(background=self.COLOR_BACKGROUND)

        # Create a frame with padding
        main_frame = ttk.Frame(form, padding=10, style='TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title with record ID
        title_label = ttk.Label(main_frame, text=f"Mettre à jour l'Enregistrement #{record_id}",
                                font=("Segoe UI", 12, "bold"), style='Title.TLabel')
        title_label.pack(pady=(0, 10))

        # Form fields in a grid layout
        form_frame = ttk.Frame(main_frame, style='TFrame')
        form_frame.pack(fill=tk.BOTH, padx=5, pady=5)

        fields = (
            ("username", "Code Employé", record.username),
            ("timestamp", "Horodatage", record.timestamp),
            ("status", "Code Statut", record.status),
            ("punch_type", "Type de Pointage", record.punch_type),
            ("processed", "Statut de Traitement", record.processed)
        )
        entries = {}

        # Create form fields with initial values
        for idx, (field, label, value) in enumerate(fields):
            ttk.Label(form_frame, text=label + ":", style='TLabel').grid(row=idx, column=0, sticky=tk.W, padx=5, pady=5)

            if field == "punch_type":
                var = tk.IntVar(value=value)
                combo = ttk.Combobox(form_frame, textvariable=var, values=[
                    "0 - Entrée",
                    "1 - Sortie"
                ])
                combo.current(value)
                combo.grid(row=idx, column=1, padx=5, pady=5, sticky=tk.W + tk.E)
                entries[field] = var
            elif field == "processed":
                var = tk.StringVar(value=value)
                combo = ttk.Combobox(form_frame, textvariable=var, values=[
                    ProcessedStatus.UNPROCESSED + " - Non Traité",
                    ProcessedStatus.PROCESSED + " - Traité",
                    ProcessedStatus.ERROR + " - Erreur"
                ])

                # Find the index of the current value
                values = [ProcessedStatus.UNPROCESSED, ProcessedStatus.PROCESSED, ProcessedStatus.ERROR]
                try:
                    index = values.index(value)
                    combo.current(index)
                except ValueError:
                    combo.set(value)

                combo.grid(row=idx, column=1, padx=5, pady=5, sticky=tk.W + tk.E)
                entries[field] = var
            else:
                var = tk.StringVar(value=value)
                entry = ttk.Entry(form_frame, textvariable=var)
                entry.grid(row=idx, column=1, padx=5, pady=5, sticky=tk.W + tk.E)
                entries[field] = var

        def submit():
            try:
                # Update record with form values
                record.username = entries["username"].get()
                record.timestamp = entries["timestamp"].get()
                record.status = int(entries["status"].get())

                # Get punch type value
                punch_type_val = entries["punch_type"].get()
                if isinstance(punch_type_val, str) and " - " in punch_type_val:
                    record.punch_type = int(punch_type_val.split(" - ")[0])
                else:
                    record.punch_type = int(punch_type_val)

                # Get processed status value
                processed_val = entries["processed"].get()
                if isinstance(processed_val, str) and " - " in processed_val:
                    record.processed = processed_val.split(" - ")[0]
                else:
                    record.processed = processed_val

                # Call update in the repository
                self.attendance_repository.update_record(record)
                self.show_success("Enregistrement mis à jour avec succès.")
                form.destroy()
                self.load_records()
                self.display_records()
            except Exception as e:
                self.handle_error("Erreur lors de la mise à jour de l'enregistrement", e)

        # Button frame at the bottom
        button_frame = ttk.Frame(main_frame, style='TFrame')
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(button_frame, text="Annuler", command=form.destroy,
                   style='TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Enregistrer les Modifications", command=submit,
                   style='Action.TButton').pack(side=tk.RIGHT, padx=5)

    def delete_record(self):
        """Delete the selected attendance record."""
        if not self.attendance_repository:
            self.show_error("Référentiel d'enregistrements non disponible")
            return

        selected_item = self.tree.selection()
        if not selected_item:
            self.show_error("Veuillez sélectionner un enregistrement à supprimer.")
            return

        # Confirm deletion
        if not messagebox.askyesno("Confirmer la Suppression",
                                   "Êtes-vous sûr de vouloir supprimer l'enregistrement sélectionné?",
                                   parent=self.root):
            return

        record_values = self.tree.item(selected_item, "values")
        record_id = int(record_values[0])

        try:
            # Delete the record
            self.attendance_repository.delete_record(record_id)
            self.show_success("Enregistrement supprimé avec succès.")
            self.load_records()
            self.display_records()
        except Exception as e:
            self.handle_error("Erreur lors de la suppression de l'enregistrement", e)

    def synchronize_records(self):
        """Synchronize attendance records with the API."""
        if not self.sync_service:
            self.show_error("Service de synchronisation non disponible")
            return

        try:
            # Show synchronizing status
            self.status_var.set("Synchronisation des enregistrements...")
            self.status_label.config(style='Warning.TLabel')
            self.root.update()

            # Perform synchronization
            result = self.sync_service.upload_attendance_to_api()

            # Update status based on result
            if result.get('success', False):
                message = result.get('message',
                                     f"Synchronisé avec succès: {result.get('processed', 0)} enregistrements traités")
                self.status_var.set(message)
                self.status_label.config(style='Success.TLabel')
                self.show_success(message)
            else:
                message = result.get('message', "Échec de la synchronisation")
                self.status_var.set(f"Erreur: {message}")
                self.status_label.config(style='Error.TLabel')
                self.show_error(message)

            # Refresh display
            self.load_records()
            self.display_records()

        except Exception as e:
            self.handle_error("Erreur lors de la synchronisation des enregistrements", e)

    def show_error(self, message: str):
        """Display an error message to the user."""
        self.status_var.set(message)
        self.status_label.config(style='Error.TLabel')
        messagebox.showerror("Erreur", message, parent=self.root)

    def show_success(self, message: str):
        """Display a success message to the user."""
        self.status_var.set(message)
        self.status_label.config(style='Success.TLabel')
        messagebox.showinfo("Succès", message, parent=self.root)

    def handle_error(self, message: str, exception: Exception):
        """Log and display an error message."""
        error_msg = f"{message}: {exception}"
        logger.error(error_msg)
        self.show_error(error_msg)