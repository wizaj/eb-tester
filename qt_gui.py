#!/usr/bin/env python3
"""
EBANX PTP Tester – Qt GUI
=========================
A lightweight GUI implemented with PySide6 (Qt for Python) that replicates the
core workflow of the original Tkinter interface but without any Tk dependency –
it should run fine on macOS even when Tk is broken.

Launch:
  python3 qt_gui.py

(Ensure you `pip install -r requirements.txt` after the new PySide6 dependency
was added.)
"""
from __future__ import annotations

import json
import os
import sys
import traceback
import copy  # NEW: for deep copying payload structures
import webbrowser  # NEW: for opening 3DS URLs
from datetime import datetime
from typing import Dict, List, Optional

import requests
# Added: QObject, Signal, QThread for async API worker
from PySide6.QtCore import Qt, QObject, Signal, QThread
from PySide6.QtGui import QTextOption, QFont, QSyntaxHighlighter, QTextCharFormat, QColor, QFontDatabase
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QInputDialog,
    QPlainTextEdit,  # NEW: Better for code display
    QSplitter,       # NEW: For resizable panels
    QCheckBox,      # NEW: For soft descriptor checkbox
    QTabWidget,     # NEW: For tab-based interface
)

# Persistent config helper
from config_util import load_config, save_config

# ---------------------------------------------------------------------------
# Logging System
# ---------------------------------------------------------------------------
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Setup comprehensive logging system for the application."""
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logs_dir = os.path.join(script_dir, 'logs')
    
    # Create logs directory if it doesn't exist
    os.makedirs(logs_dir, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger('EBANXTester')
    logger.setLevel(logging.INFO)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # File handler with daily rotation
    today = datetime.now().strftime('%Y%m%d')
    log_file_path = os.path.join(logs_dir, f'ebanx_tester_{today}.log')
    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# ---------------------------------------------------------------------------
# JSON Syntax Highlighter
# ---------------------------------------------------------------------------
class JSONHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for JSON text."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_formats()
    
    def setup_formats(self):
        """Setup color formats for different JSON elements."""
        # String format (green)
        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor("#228B22"))  # Forest green
        self.string_format.setFontWeight(QFont.Weight.Bold)
        
        # Number format (blue)
        self.number_format = QTextCharFormat()
        self.number_format.setForeground(QColor("#0000CD"))  # Medium blue
        self.number_format.setFontWeight(QFont.Weight.Bold)
        
        # Boolean format (purple)
        self.boolean_format = QTextCharFormat()
        self.boolean_format.setForeground(QColor("#8A2BE2"))  # Blue violet
        self.boolean_format.setFontWeight(QFont.Weight.Bold)
        
        # Null format (red)
        self.null_format = QTextCharFormat()
        self.null_format.setForeground(QColor("#DC143C"))  # Crimson
        self.null_format.setFontWeight(QFont.Weight.Bold)
        
        # Key format (dark blue)
        self.key_format = QTextCharFormat()
        self.key_format.setForeground(QColor("#191970"))  # Midnight blue
        self.key_format.setFontWeight(QFont.Weight.Bold)
    
    def highlightBlock(self, text):
        """Highlight a block of text."""
        import re
        
        # Highlight strings (quoted text)
        string_pattern = r'"[^"\\]*(?:\\.[^"\\]*)*"'
        for match in re.finditer(string_pattern, text):
            start = match.start()
            end = match.end()
            self.setFormat(start, end - start, self.string_format)
        
        # Highlight numbers
        number_pattern = r'\b\d+\.?\d*\b'
        for match in re.finditer(number_pattern, text):
            start = match.start()
            end = match.end()
            self.setFormat(start, end - start, self.number_format)
        
        # Highlight booleans
        boolean_pattern = r'\b(true|false)\b'
        for match in re.finditer(boolean_pattern, text, re.IGNORECASE):
            start = match.start()
            end = match.end()
            self.setFormat(start, end - start, self.boolean_format)
        
        # Highlight null
        null_pattern = r'\bnull\b'
        for match in re.finditer(null_pattern, text, re.IGNORECASE):
            start = match.start()
            end = match.end()
            self.setFormat(start, end - start, self.null_format)
        
        # Highlight keys (text before colon)
        key_pattern = r'(\s*"[^"]+")\s*:'
        for match in re.finditer(key_pattern, text):
            start = match.start(1)
            end = match.end(1)
            self.setFormat(start, end - start, self.key_format)

# ---------------------------------------------------------------------------
# Enhanced JSON Text Editor
# ---------------------------------------------------------------------------
class JSONTextEdit(QPlainTextEdit):
    """Enhanced text editor for JSON with syntax highlighting and formatting."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_editor()
    
    def setup_editor(self):
        """Setup the editor with monospace font and syntax highlighting."""
        # Set monospace font
        font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        font.setPointSize(10)
        self.setFont(font)
        
        # Set line wrap mode
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        
        # Add syntax highlighter
        self.highlighter = JSONHighlighter(self.document())
        
        # Set tab width
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(' ') * 4)
    
    def set_json_text(self, data):
        """Set JSON data with proper formatting."""
        if isinstance(data, str):
            try:
                # Try to parse and re-format if it's JSON string
                parsed = json.loads(data)
                formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
            except (json.JSONDecodeError, TypeError):
                # If not valid JSON, just use as-is
                formatted = data
        else:
            # If it's already a dict/list, format it
            formatted = json.dumps(data, indent=2, ensure_ascii=False)
        
        self.setPlainText(formatted)
    
    def get_json_data(self):
        """Get the current text as JSON data."""
        text = self.toPlainText().strip()
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None
    
    def format_json(self):
        """Format the current JSON text."""
        data = self.get_json_data()
        if data is not None:
            self.set_json_text(data)
            return True
        return False

# ---------------------------------------------------------------------------
# Background worker for API requests
# ---------------------------------------------------------------------------


class APICallWorker(QObject):
    """Runs the blocking requests.post call in a separate thread."""

    finished = Signal(object)  # emits requests.Response on success
    error = Signal(str)        # emits error string

    def __init__(self, url: str, payload_data: dict, headers: dict):
        super().__init__()
        self.url = url
        self.payload_data = payload_data
        self.headers = headers

    def run(self):
        """Execute the HTTP request (runs inside a QThread)."""
        try:
            resp = requests.post(
                self.url,
                json=self.payload_data,
                headers=self.headers,
                timeout=30,
            )
            self.finished.emit(resp)
        except requests.exceptions.RequestException as exc:
            self.error.emit(str(exc))

# ---------------------------------------------------------------------------
# Helpers for loading data
# ---------------------------------------------------------------------------
ROOT = os.path.dirname(__file__)
DATA_DIR = os.path.join(ROOT, "data")

CARDS_FILE = os.path.join(DATA_DIR, "test-cards.json")
PTP_FILE = os.path.join(DATA_DIR, "ptp-list.txt")

def create_dummy_test_data():
    """Create dummy test data for first-time users."""
    return {
        "NG": {
            "customer_data": {
                "name": "Test User",
                "email": "test+ng@ebanx.com",
                "phone_number": "+2348089895495",
                "birth_date": "01/01/1990",
                "country": "ng",
                "currency_code": "NGN",
                "default_amount": 100
            },
            "debitcard": {
                "visa": [
                    {
                        "card_number": "4111111111111111",
                        "card_name": "Test User",
                        "card_due_date": "12/2025",
                        "card_cvv": "123",
                        "description": "NG - Test Visa Card - NGN",
                        "custom_payload": {
                            "integration_key": "{integration_key}",
                            "operation": "request",
                            "payment": {
                                "amount_total": 100,
                                "currency_code": "NGN",
                                "name": "Test User",
                                "email": "test+ng@ebanx.com",
                                "birth_date": "01/01/1990",
                                "country": "ng",
                                "phone_number": "+2348089895495",
                                "card": {
                                    "card_number": "4111111111111111",
                                    "card_name": "Test User",
                                    "card_due_date": "12/2025",
                                    "card_cvv": "123",
                                    "auto_capture": True,
                                    "threeds_force": False
                                }
                            }
                        }
                    }
                ],
                "mastercard": [
                    {
                        "card_number": "5555555555554444",
                        "card_name": "Test User",
                        "card_due_date": "12/2025",
                        "card_cvv": "123",
                        "description": "NG - Test Mastercard - NGN"
                    }
                ]
            }
        },
        "KE": {
            "customer_data": {
                "name": "Test User",
                "email": "test+ke@ebanx.com",
                "phone_number": "+254708663158",
                "birth_date": "01/01/1990",
                "country": "ke",
                "currency_code": "KES",
                "default_amount": 75
            },
            "debitcard": {
                "visa": [
                    {
                        "card_number": "4111111111111111",
                        "card_name": "Test User",
                        "card_due_date": "12/2025",
                        "card_cvv": "123",
                        "description": "KE - Test Visa Card - KES"
                    }
                ]
            },
            "mobile_money": {
                "mpesa": {
                    "phone_number": "254708663158",
                    "description": "KE - MPESA Test Number"
                }
            }
        },
        "ZA": {
            "customer_data": {
                "name": "Test User",
                "email": "test+za@ebanx.com",
                "phone_number": "+27123456789",
                "birth_date": "01/01/1990",
                "country": "za",
                "currency_code": "ZAR",
                "default_amount": 10
            },
            "debitcard": {
                "mastercard": [
                    {
                        "card_number": "5555555555554444",
                        "card_name": "Test User",
                        "card_due_date": "12/2025",
                        "card_cvv": "123",
                        "description": "ZA - Test Mastercard - ZAR"
                    }
                ]
            }
        },
        "EG": {
            "customer_data": {
                "name": "Test User",
                "email": "test+eg@ebanx.com",
                "phone_number": "+201234567890",
                "birth_date": "01/01/1990",
                "country": "eg",
                "currency_code": "EGP",
                "default_amount": 50
            },
            "debitcard": {
                "visa": [
                    {
                        "card_number": "4111111111111111",
                        "card_name": "Test User",
                        "card_due_date": "12/2025",
                        "card_cvv": "123",
                        "description": "EG - Test Visa Card - EGP"
                    }
                ]
            }
        }
    }

def load_json(path: str):
    if not os.path.exists(path):
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # If this is the test-cards.json file, create it with dummy data
        if path.endswith("test-cards.json"):
            dummy_data = create_dummy_test_data()
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(dummy_data, fh, indent=2)
            return dummy_data
        else:
            raise FileNotFoundError(path)
    
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)

def load_lines(path: str) -> List[str]:
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    with open(path, "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip()]

# ---------------------------------------------------------------------------
# Main Window
# ---------------------------------------------------------------------------
class TesterWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EBANX PTP Tester – Qt Edition")
        self.resize(1400, 900)  # Increased size for better layout

        # Setup logging for this instance
        self.logger = setup_logging()
        self.logger.info("Initializing TesterWindow")

        try:
            self.test_data: Dict = load_json(CARDS_FILE)
            self.logger.info(f"Loaded test data: {len(self.test_data)} countries")
            self.ptp_list: List[str] = load_lines(PTP_FILE)
            self.logger.info(f"Loaded PTP list: {len(self.ptp_list)} profiles")
        except Exception as exc:
            self.logger.error(f"Failed to load data: {exc}")
            QMessageBox.critical(self, "Data error", str(exc))
            raise SystemExit(1)

        # Flag to avoid feedback loops when syncing between editors
        self._syncing: bool = False

        # Load persisted settings
        self.cfg = load_config()

        # ------------------------------------------------------------------
        # Top-level widgets
        # ------------------------------------------------------------------
        central = QWidget()
        self.setCentralWidget(central)
        outer_vbox = QVBoxLayout(central)

        # API config row
        config_row = QHBoxLayout()
        outer_vbox.addLayout(config_row)

        # Base URL
        config_row.addWidget(QLabel("Base URL:"))
        self.base_url_edit = QLineEdit(self.cfg.get("base_url", "https://api.ebanx.com/"))
        self.base_url_edit.setMinimumWidth(300)
        config_row.addWidget(self.base_url_edit)

        # Integration Key
        config_row.addWidget(QLabel("Integration Key:"))
        self.key_edit = QLineEdit(self.cfg.get("integration_key", ""))
        self.key_edit.setMinimumWidth(300)
        config_row.addWidget(self.key_edit)
        
        # Connect API key changes to payload updates
        self.key_edit.textChanged.connect(self.on_api_key_changed)

        # Soft Descriptor
        config_row.addWidget(QLabel("Soft Descriptor:"))
        self.soft_descriptor_edit = QLineEdit(self.cfg.get("soft_descriptor", ""))
        self.soft_descriptor_edit.setMinimumWidth(200)
        self.soft_descriptor_edit.setPlaceholderText("Enter soft descriptor...")
        config_row.addWidget(self.soft_descriptor_edit)
        
        # Soft Descriptor Checkbox
        self.soft_descriptor_checkbox = QCheckBox("Use Soft Descriptor")
        self.soft_descriptor_checkbox.setChecked(self.cfg.get("use_soft_descriptor", False))
        config_row.addWidget(self.soft_descriptor_checkbox)
        
        # Connect soft descriptor changes to payload updates
        self.soft_descriptor_edit.textChanged.connect(self.on_soft_descriptor_changed)
        self.soft_descriptor_checkbox.toggled.connect(self.on_soft_descriptor_changed)

        # Removed Test Connection button
        config_row.addStretch(1)

        # ------------------------------------------------------------------
        # Tab-based interface
        # ------------------------------------------------------------------
        self.tab_widget = QTabWidget()
        outer_vbox.addWidget(self.tab_widget, stretch=1)

        # Create the three tabs
        self.create_non3ds_tab()
        self.create_3ds_tab()
        self.create_apms_tab()

        # Set uniform tab widths
        self.setup_uniform_tabs()

        # Initial payload display for the first tab
        self.update_payload_preview()

    # ------------------------------------------------------------------
    # Tab creation methods
    # ------------------------------------------------------------------
    def create_non3ds_tab(self):
        """Create the Non-3DS (Unauthenticated) tab with existing functionality."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Create splitter for left/right layout
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(content_splitter)

        # Left – card selector + payload preview
        left_widget = QWidget()
        left_box = QVBoxLayout(left_widget)
        content_splitter.addWidget(left_widget)

        left_box.addWidget(QLabel("Select Card:"))
        self.card_combo = QComboBox()
        # card_fields will be created below; populate after that
        self.card_combo.currentIndexChanged.connect(self.on_card_changed)
        # Connect card selection change to save settings
        self.card_combo.currentIndexChanged.connect(self._persist_settings)
        left_box.addWidget(self.card_combo)

        # Card form (number, name, expiry, cvv)
        form_labels = ["Card Number", "Cardholder Name", "Expiry (MM/YY)", "CVV"]
        self.card_fields: List[QLineEdit] = []
        for label_text in form_labels:
            lbl = QLabel(label_text + ":")
            edit = QLineEdit()
            left_box.addWidget(lbl)
            left_box.addWidget(edit)
            self.card_fields.append(edit)

        # --- Sync card form <-> payload ------------------------------------
        for edit in self.card_fields:
            # textEdited fires on each change but does not fire when text is set programmatically
            edit.textEdited.connect(self.on_card_field_changed)

        # Card management buttons -------------------------------------------------
        btn_row = QHBoxLayout()
        self.save_existing_btn = QPushButton("Save Existing")
        self.save_existing_btn.clicked.connect(self.save_existing_card)
        btn_row.addWidget(self.save_existing_btn)

        self.save_new_btn = QPushButton("Save New")
        self.save_new_btn.clicked.connect(self.save_new_card)
        btn_row.addWidget(self.save_new_btn)

        self.load_btn = QPushButton("Load")
        self.load_btn.clicked.connect(self.reload_cards_from_disk)
        btn_row.addWidget(self.load_btn)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_current_card)
        btn_row.addWidget(self.delete_btn)
        left_box.addLayout(btn_row)

        # ------------------------------------------------------------------------

        # Payload section with format button
        payload_header = QHBoxLayout()
        payload_header.addWidget(QLabel("Payload Preview:"))
        self.format_payload_btn = QPushButton("Format JSON")
        self.format_payload_btn.clicked.connect(self.format_payload_json)
        payload_header.addWidget(self.format_payload_btn)
        payload_header.addStretch(1)
        left_box.addLayout(payload_header)
        
        # Use enhanced JSON editor for payload
        self.payload_edit = JSONTextEdit()
        # Sync payload changes back to card fields
        self.payload_edit.textChanged.connect(self.on_payload_changed)
        left_box.addWidget(self.payload_edit, stretch=1)

        # Now that payload editor exists, we can safely populate the card combo
        self.populate_card_combo()
        # Set the last selected card if available
        last_card_index = self.cfg.get("last_card_index", 0)
        if 0 <= last_card_index < self.card_combo.count():
            self.card_combo.setCurrentIndex(last_card_index)

        # Right – PTP, run button, response
        right_widget = QWidget()
        right_box = QVBoxLayout(right_widget)
        content_splitter.addWidget(right_widget)

        right_box.addWidget(QLabel("Select PTP:"))

        # NEW: filter textbox for PTPs
        self.ptp_filter_edit = QLineEdit()
        self.ptp_filter_edit.setPlaceholderText("Filter PTP…")
        self.ptp_filter_edit.textChanged.connect(self.update_ptp_filter)
        right_box.addWidget(self.ptp_filter_edit)

        self.ptp_combo = QComboBox()
        self.ptp_combo.addItems(self.ptp_list)
        # Set the last selected PTP if available
        last_ptp = self.cfg.get("last_ptp", "")
        if last_ptp and last_ptp in self.ptp_list:
            self.ptp_combo.setCurrentText(last_ptp)
        # Connect PTP selection change to save settings
        self.ptp_combo.currentTextChanged.connect(self._persist_settings)
        right_box.addWidget(self.ptp_combo)

        self.run_btn = QPushButton("Run Test")
        self.run_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.run_btn.clicked.connect(self.run_test)
        right_box.addWidget(self.run_btn)

        # Response section with clear button
        response_header = QHBoxLayout()
        response_header.addWidget(QLabel("API Response:"))
        self.clear_response_btn = QPushButton("Clear")
        self.clear_response_btn.clicked.connect(self.clear_response)
        response_header.addWidget(self.clear_response_btn)
        response_header.addStretch(1)
        right_box.addLayout(response_header)
        
        # Use enhanced JSON editor for response
        self.response_edit = JSONTextEdit()
        self.response_edit.setReadOnly(True)
        # Enable text wrapping for better readability of long responses
        self.response_edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        right_box.addWidget(self.response_edit, stretch=1)

        # Set splitter proportions (60% left, 40% right)
        content_splitter.setSizes([840, 560])

        # Add tab to widget
        self.tab_widget.addTab(tab, "Non-3DS (Unauthenticated)")

    def create_3ds_tab(self):
        """Create the 3DS (Authenticated) tab with same UI as Non-3DS but different API parameters."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Create splitter for left/right layout
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(content_splitter)

        # Left – card selector + payload preview
        left_widget = QWidget()
        left_box = QVBoxLayout(left_widget)
        content_splitter.addWidget(left_widget)

        left_box.addWidget(QLabel("Select Card:"))
        self.card_combo_3ds = QComboBox()
        # card_fields_3ds will be created below; populate after that
        self.card_combo_3ds.currentIndexChanged.connect(self.on_card_changed_3ds)
        # Connect card selection change to save settings
        self.card_combo_3ds.currentIndexChanged.connect(self._persist_settings)
        left_box.addWidget(self.card_combo_3ds)

        # Card form (number, name, expiry, cvv)
        form_labels = ["Card Number", "Cardholder Name", "Expiry (MM/YY)", "CVV"]
        self.card_fields_3ds: List[QLineEdit] = []
        for label_text in form_labels:
            lbl = QLabel(label_text + ":")
            edit = QLineEdit()
            left_box.addWidget(lbl)
            left_box.addWidget(edit)
            self.card_fields_3ds.append(edit)

        # --- Sync card form <-> payload ------------------------------------
        for edit in self.card_fields_3ds:
            # textEdited fires on each change but does not fire when text is set programmatically
            edit.textEdited.connect(self.on_card_field_changed_3ds)

        # Card management buttons -------------------------------------------------
        btn_row = QHBoxLayout()
        self.save_existing_btn_3ds = QPushButton("Save Existing")
        self.save_existing_btn_3ds.clicked.connect(self.save_existing_card_3ds)
        btn_row.addWidget(self.save_existing_btn_3ds)

        self.save_new_btn_3ds = QPushButton("Save New")
        self.save_new_btn_3ds.clicked.connect(self.save_new_card_3ds)
        btn_row.addWidget(self.save_new_btn_3ds)

        self.load_btn_3ds = QPushButton("Load")
        self.load_btn_3ds.clicked.connect(self.reload_cards_from_disk_3ds)
        btn_row.addWidget(self.load_btn_3ds)

        self.delete_btn_3ds = QPushButton("Delete")
        self.delete_btn_3ds.clicked.connect(self.delete_current_card_3ds)
        btn_row.addWidget(self.delete_btn_3ds)
        left_box.addLayout(btn_row)

        # ------------------------------------------------------------------------

        # Payload section with format button
        payload_header = QHBoxLayout()
        payload_header.addWidget(QLabel("Payload Preview:"))
        self.format_payload_btn_3ds = QPushButton("Format JSON")
        self.format_payload_btn_3ds.clicked.connect(self.format_payload_json_3ds)
        payload_header.addWidget(self.format_payload_btn_3ds)
        payload_header.addStretch(1)
        left_box.addLayout(payload_header)
        
        # Use enhanced JSON editor for payload
        self.payload_edit_3ds = JSONTextEdit()
        # Sync payload changes back to card fields
        self.payload_edit_3ds.textChanged.connect(self.on_payload_changed_3ds)
        left_box.addWidget(self.payload_edit_3ds, stretch=1)

        # Now that payload editor exists, we can safely populate the card combo
        self.populate_card_combo_3ds()
        # Set the last selected card for 3DS tab if available
        last_card_index_3ds = self.cfg.get("last_card_index_3ds", 0)
        if 0 <= last_card_index_3ds < self.card_combo_3ds.count():
            self.card_combo_3ds.setCurrentIndex(last_card_index_3ds)

        # Right – PTP, run button, response
        right_widget = QWidget()
        right_box = QVBoxLayout(right_widget)
        content_splitter.addWidget(right_widget)

        right_box.addWidget(QLabel("Select PTP:"))

        # NEW: filter textbox for PTPs
        self.ptp_filter_edit_3ds = QLineEdit()
        self.ptp_filter_edit_3ds.setPlaceholderText("Filter PTP…")
        self.ptp_filter_edit_3ds.textChanged.connect(self.update_ptp_filter_3ds)
        right_box.addWidget(self.ptp_filter_edit_3ds)

        self.ptp_combo_3ds = QComboBox()
        self.ptp_combo_3ds.addItems(self.ptp_list)
        # Set the last selected PTP for 3DS tab if available
        last_ptp_3ds = self.cfg.get("last_ptp_3ds", "")
        if last_ptp_3ds and last_ptp_3ds in self.ptp_list:
            self.ptp_combo_3ds.setCurrentText(last_ptp_3ds)
        # Connect PTP selection change to save settings
        self.ptp_combo_3ds.currentTextChanged.connect(self._persist_settings)
        right_box.addWidget(self.ptp_combo_3ds)

        self.run_btn_3ds = QPushButton("Run Test")
        self.run_btn_3ds.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.run_btn_3ds.clicked.connect(self.run_test_3ds)
        right_box.addWidget(self.run_btn_3ds)

        # Response section with clear button
        response_header = QHBoxLayout()
        response_header.addWidget(QLabel("API Response:"))
        self.clear_response_btn_3ds = QPushButton("Clear")
        self.clear_response_btn_3ds.clicked.connect(self.clear_response_3ds)
        response_header.addWidget(self.clear_response_btn_3ds)
        
        # 3DS Authentication button
        self.authenticate_3ds_btn_3ds = QPushButton("Authenticate 3DS in Browser")
        self.authenticate_3ds_btn_3ds.setEnabled(False)  # Initially disabled
        self.authenticate_3ds_btn_3ds.clicked.connect(self.authenticate_3ds_in_browser_3ds)
        response_header.addWidget(self.authenticate_3ds_btn_3ds)
        
        response_header.addStretch(1)
        right_box.addLayout(response_header)
        
        # Use enhanced JSON editor for response
        self.response_edit_3ds = JSONTextEdit()
        self.response_edit_3ds.setReadOnly(True)
        # Enable text wrapping for better readability of long responses
        self.response_edit_3ds.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        right_box.addWidget(self.response_edit_3ds, stretch=1)

        # Set splitter proportions (60% left, 40% right)
        content_splitter.setSizes([840, 560])

        # Add tab to widget
        self.tab_widget.addTab(tab, "3DS (Authenticated)")

    def create_apms_tab(self):
        """Create the APMs (Alternative Payment Methods) tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Placeholder content for APMs tab
        placeholder = QLabel("Alternative Payment Methods (APMs)\n\nThis tab will contain functionality for testing alternative payment methods.\n\nFeatures to be implemented:\n• Mobile money (M-Pesa, etc.)\n• Bank transfers\n• Digital wallets\n• Local payment methods")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("QLabel { font-size: 14px; color: #666; }")
        layout.addWidget(placeholder)
        
        # Add tab to widget
        self.tab_widget.addTab(tab, "APMs")

    def setup_uniform_tabs(self):
        """Set all tabs to have uniform width based on the longest tab."""
        # Get the tab bar
        tab_bar = self.tab_widget.tabBar()
        
        # Calculate the width needed for the longest tab text
        font_metrics = tab_bar.fontMetrics()
        max_width = 0
        
        # Check all tab texts to find the longest one
        for i in range(self.tab_widget.count()):
            tab_text = self.tab_widget.tabText(i)
            text_width = font_metrics.horizontalAdvance(tab_text)
            max_width = max(max_width, text_width)
        
        # Add padding for tab styling (borders, margins, etc.)
        tab_width = max_width + 40  # Add 40px padding
        
        # Set the minimum width for each tab
        tab_bar.setStyleSheet(f"""
            QTabBar::tab {{
                min-width: {tab_width}px;
                padding: 8px 12px;
            }}
        """)

    # ------------------------------------------------------------------
    # Data helpers
    # ------------------------------------------------------------------
    def flatten_cards(self):
        cards = []
        for country, data in self.test_data.items():
            for card_list in data.get("debitcard", {}).values():
                for card in card_list:
                    display = f"{country} – {card['description']}"
                    cards.append((display, country, card))
        return cards

    # ------------------------------------------------------------------
    # UI population / events
    # ------------------------------------------------------------------
    def populate_card_combo(self):
        self.flat_cards = self.flatten_cards()
        self.card_combo.clear()
        self.card_combo.addItems([t[0] for t in self.flat_cards])
        if self.flat_cards:
            self.card_combo.setCurrentIndex(0)
            self.apply_card_to_form(self.flat_cards[0][2])

    def on_card_changed(self, idx: int):
        if 0 <= idx < len(self.flat_cards):
            _, _, card = self.flat_cards[idx]
            self.apply_card_to_form(card)
            self.update_payload_preview()

    def apply_card_to_form(self, card: Dict):
        self.card_fields[0].setText(card["card_number"])
        self.card_fields[1].setText(card["card_name"])
        self.card_fields[2].setText(card["card_due_date"])
        self.card_fields[3].setText(card["card_cvv"])

    def current_card_country_and_data(self):
        idx = self.card_combo.currentIndex()
        if not (0 <= idx < len(self.flat_cards)):
            return None, None, None
        display, country, card = self.flat_cards[idx]
        customer = self.test_data[country]["customer_data"]
        return country, card, customer

    def update_payload_preview(self):
        """Regenerate the payload preview based on current UI state.

        This method builds a payload that reflects *both* the underlying card
        profile and any unsaved edits in the card form fields. If a custom
        payload exists for the selected card we respect all of its keys and
        simply override the nested `payment.card` block so that card edits are
        always mirrored. The API key is always taken from the UI field as the
        single source of truth.
        """

        if self._syncing:
            return  # Prevent feedback loops

        country, card, customer = self.current_card_country_and_data()
        if not card:
            return

        # Prepare the up-to-date card dict based on current UI entries
        ui_card = {
            "card_number": self.card_fields[0].text().strip(),
            "card_name": self.card_fields[1].text().strip(),
            "card_due_date": self.card_fields[2].text().strip(),
            "card_cvv": self.card_fields[3].text().strip(),
        }

        # Start from saved custom payload (if any) so we don't discard user tuning
        if card.get("custom_payload"):
            payload = copy.deepcopy(card["custom_payload"])
            try:
                payload["payment"]["card"].update(ui_card)
                # Always use the current API key from UI, never from saved payload
                payload["integration_key"] = self.key_edit.text() or "{integration_key}"
                
                # Handle soft descriptor in card object
                if self.soft_descriptor_checkbox.isChecked() and self.soft_descriptor_edit.text().strip():
                    payload["payment"]["card"]["soft_descriptor"] = self.soft_descriptor_edit.text().strip()
                elif "soft_descriptor" in payload["payment"]["card"]:
                    # Remove soft descriptor if checkbox is unchecked
                    del payload["payment"]["card"]["soft_descriptor"]
            except (KeyError, TypeError):
                # Fallback to rebuilding if structure is unexpected
                payload = self.build_payload(country, ui_card, customer)
        else:
            payload = self.build_payload(country, ui_card, customer)

        # Temporarily block signals to avoid recursive updates when we set text
        self._syncing = True
        self.payload_edit.set_json_text(payload)
        self._syncing = False

    # ------------------------------------------------------------------
    # Sync helpers
    # ------------------------------------------------------------------
    def on_card_field_changed(self):
        """Called whenever the user edits one of the card QLineEdits."""
        if self._syncing:
            return
        self.update_payload_preview()

    def on_api_key_changed(self):
        """Called when the API key field changes - update payload and save config."""
        if self._syncing:
            return
        self.update_payload_preview()
        self._persist_settings()

    def on_soft_descriptor_changed(self):
        """Called when the soft descriptor field or checkbox changes - update payload and save config."""
        if self._syncing:
            return
        self.update_payload_preview()
        self._persist_settings()

    def on_payload_changed(self):
        """Keep card form fields and API key in sync when the payload editor changes.

        We attempt to parse the JSON on each change. On valid JSON we extract
        the card block and update form fields. We also sync the integration_key
        from the payload to the UI field. This direction-of-sync ensures
        that manual edits in the JSON view are reflected back in the card
        selector UI and API key field.
        """
        if self._syncing:
            return

        data = self.payload_edit.get_json_data()
        if not data:
            return  # Invalid / incomplete JSON – ignore until valid

        self._syncing = True
        
        # Update card form fields
        try:
            card_data = data["payment"]["card"]
            for fld, key in zip(self.card_fields, ["card_number", "card_name", "card_due_date", "card_cvv"]):
                fld.setText(str(card_data.get(key, "")))
        except (KeyError, TypeError):
            pass  # Card data not available or structure unexpected
        
        # Update API key field if present in payload
        if "integration_key" in data:
            api_key = data["integration_key"]
            if api_key and api_key != "{integration_key}":
                self.key_edit.setText(str(api_key))
        
        # Update soft descriptor settings from payload
        try:
            card_data = data["payment"]["card"]
            if "soft_descriptor" in card_data:
                self.soft_descriptor_edit.setText(str(card_data["soft_descriptor"]))
                self.soft_descriptor_checkbox.setChecked(True)
            else:
                self.soft_descriptor_checkbox.setChecked(False)
        except (KeyError, TypeError):
            pass  # Card data not available or structure unexpected
        
        self._syncing = False

    def format_payload_json(self):
        """Format the payload JSON."""
        if self.payload_edit.format_json():
            QMessageBox.information(self, "Formatted", "JSON has been formatted successfully.")
        else:
            QMessageBox.warning(self, "Invalid JSON", "The payload contains invalid JSON that cannot be formatted.")

    def clear_response(self):
        """Clear the response display."""
        self.response_edit.clear()

    # ------------------------------------------------------------------
    # API interaction
    # ------------------------------------------------------------------
    def build_payload(self, country: str, card: Dict, customer: Dict):
        payload = {
            "integration_key": self.key_edit.text() or "{integration_key}",
            "operation": "request",
            "payment": {
                "amount_total": customer["default_amount"],
                "currency_code": customer["currency_code"],
                "name": customer["name"],
                "email": customer["email"],
                "birth_date": customer["birth_date"],
                "country": customer["country"],
                "phone_number": customer["phone_number"],
                "card": {
                    "card_number": card["card_number"],
                    "card_name": card["card_name"],
                    "card_due_date": card["card_due_date"],
                    "card_cvv": card["card_cvv"],
                    "auto_capture": True,
                    "threeds_force": False,
                },
            },
        }

        # Add soft descriptor to card object if checkbox is checked
        if self.soft_descriptor_checkbox.isChecked() and self.soft_descriptor_edit.text().strip():
            payload["payment"]["card"]["soft_descriptor"] = self.soft_descriptor_edit.text().strip()

        return payload

    def _build_curl_command(self, url: str, ptp: str, payload) -> str:
        """Return a formatted multi-line cURL command for debugging purposes."""
        import json  # local import to avoid issues if module name is shadowed

        json_str = json.dumps(payload, separators=(',', ':'))
        # Escape any single quotes in the JSON so the command remains valid inside single quotes
        json_str = json_str.replace("'", "'\"'\"'")

        cmd = (
            f"curl -X POST '{url}' \\\n"  # newline retained
            f"  -H 'Content-Type: application/json' \\\n"  # newline retained
            f"  -H 'X-EBANX-Custom-Payment-Type-Profile: {ptp}' \\\n"  # newline retained
            f"  -d '{json_str}'"
        )
        return cmd

    def save_payload_for_card(self):
        idx = self.card_combo.currentIndex()
        if not (0 <= idx < len(self.flat_cards)):
            QMessageBox.warning(self, "No card selected", "Select a card first.")
            return
        _, _, card = self.flat_cards[idx]
        
        payload_data = self.payload_edit.get_json_data()
        if payload_data is None:
            QMessageBox.critical(self, "Invalid JSON", "Payload contains invalid JSON.")
            return

        # Remove the integration_key from the payload before saving
        # since it should always come from the UI field
        if "integration_key" in payload_data:
            del payload_data["integration_key"]

        card["custom_payload"] = payload_data
        self._write_cards_file()
        QMessageBox.information(self, "Saved", "Payload saved as part of card profile (API key excluded).")

    def run_test(self):
        self.logger.info("Starting API test")
        
        country, card, customer = self.current_card_country_and_data()
        if not card:
            self.logger.warning("No card selected for test")
            QMessageBox.warning(self, "No card", "Please select a card first")
            return

        ptp = self.ptp_combo.currentText()
        if not ptp:
            self.logger.warning("No PTP selected for test")
            QMessageBox.warning(self, "No PTP", "Please select a PTP first")
            return

        if not self.key_edit.text():
            self.logger.warning("No integration key provided")
            QMessageBox.warning(self, "No key", "Please enter Integration Key")
            return

        # Use the JSON currently in the payload editor as the request body
        payload_data = self.payload_edit.get_json_data()
        if payload_data is None:
            self.logger.error("Invalid JSON payload")
            QMessageBox.critical(self, "Invalid JSON", "Payload JSON is invalid.")
            return

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "EBANX-PTP-Tester/Qt",
            "X-EBANX-Custom-Payment-Type-Profile": ptp,
        }
        url = f"{self.base_url_edit.text().rstrip('/')}/ws/direct"
        
        self.logger.info(f"Making API call to {url} with PTP: {ptp}")
        self.logger.info(f"Card: {card.get('description', 'Unknown')}")
        self.logger.info(f"Country: {country}")

        # ------------------------------------------------------------------
        # Observability – show the cURL command first
        # ------------------------------------------------------------------
        self.run_btn.setEnabled(False)

        curl_cmd = self._build_curl_command(url, ptp, payload_data)

        # Show cURL preview and waiting message
        self.response_edit.appendPlainText("🔧 cURL Command:\n")
        self.response_edit.appendPlainText(curl_cmd)
        self.response_edit.appendPlainText("\n\n⏳ Waiting for response...\n")
        QApplication.processEvents()

        # Prepare header that will be shown once the response is available
        request_info = (
            f"🌐 POST {url}\n"
            f"📋 PTP: {ptp}\n"
            f"💳 Card: {card['description']}\n"
            f"⏰ {datetime.now().strftime('%H:%M:%S')}\n"
            + "─" * 50 + "\n"
        )
 
        # Create a worker and a QThread to run the network request without blocking the UI
        self._api_thread = QThread(self)  # Keep reference as attribute
        worker = APICallWorker(url, payload_data, headers)
        worker.moveToThread(self._api_thread)
        self._api_worker = worker  # Prevent garbage collection

        # Wire up signals
        self._api_thread.started.connect(worker.run)
        worker.finished.connect(self._handle_api_response)
        worker.error.connect(self._handle_api_error)

        # Ensure thread stops/cleans up
        worker.finished.connect(self._api_thread.quit)
        worker.error.connect(self._api_thread.quit)
        self._api_thread.finished.connect(worker.deleteLater)
        self._api_thread.finished.connect(self._api_thread.deleteLater)

        # Persist request info for handlers
        self._latest_request_info = request_info

        # Start the background job
        self._api_thread.start()

    def _handle_api_response(self, resp):
        self.logger.info(f"API response received: {resp.status_code} {resp.reason}")
        
        # Append response header below the existing cURL preview so it's not lost
        self.response_edit.appendPlainText("\n" + self._latest_request_info)
        
        # Enhanced response display with status color coding
        status_text = f"📊 Status: {resp.status_code} {resp.reason}\n"
        if resp.status_code >= 200 and resp.status_code < 300:
            status_text += "✅ Success\n"
            self.logger.info("API call successful")
        elif resp.status_code >= 400 and resp.status_code < 500:
            status_text += "❌ Client Error\n"
            self.logger.warning(f"API client error: {resp.status_code}")
        elif resp.status_code >= 500:
            status_text += "🔥 Server Error\n"
            self.logger.error(f"API server error: {resp.status_code}")
        else:
            status_text += "⚠️  Other Status\n"
            self.logger.warning(f"API unexpected status: {resp.status_code}")
        
        self.response_edit.appendPlainText(status_text)
        
        try:
            response_data = resp.json()
            self.response_edit.appendPlainText("📄 Response Body:\n")
            self.response_edit.set_json_text(response_data)
        except ValueError:
            self.response_edit.appendPlainText("📄 Response Text:\n")
            self.response_edit.appendPlainText(resp.text)
                
        self.run_btn.setEnabled(True)
        # Persist latest settings
        self._persist_settings()

    def _handle_api_error(self, error_msg: str):
        self.logger.error(f"API call failed: {error_msg}")
        
        # Append error information below preview
        self.response_edit.appendPlainText("\n" + self._latest_request_info)
        self.response_edit.appendPlainText(f"❌ Error: {error_msg}")
        self.run_btn.setEnabled(True)
        # Persist latest settings
        self._persist_settings()

    # ------------------------------------------------------------------
    # PTP filter helper
    # ------------------------------------------------------------------
    def update_ptp_filter(self, text: str):
        """Filter the PTP combo box items based on *text*."""
        text = text.strip().lower()
        current = self.ptp_combo.currentText()
        self.ptp_combo.blockSignals(True)
        self.ptp_combo.clear()
        if text:
            filtered = [ptp for ptp in self.ptp_list if text in ptp.lower()]
        else:
            filtered = self.ptp_list
        self.ptp_combo.addItems(filtered)
        self.ptp_combo.blockSignals(False)
        # Try to keep previous selection if still available, else select first
        if current in filtered:
            self.ptp_combo.setCurrentText(current)
        elif self.ptp_combo.count():
            self.ptp_combo.setCurrentIndex(0)

    # ------------------------------------------------------------------
    # Connection test – removed
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Config persistence helpers
    # ------------------------------------------------------------------
    def _persist_settings(self):
        save_config({
            "integration_key": self.key_edit.text(),
            "base_url": self.base_url_edit.text(),
            "soft_descriptor": self.soft_descriptor_edit.text(),
            "use_soft_descriptor": self.soft_descriptor_checkbox.isChecked(),
            "last_ptp": self.ptp_combo.currentText(),
            "last_ptp_3ds": self.ptp_combo_3ds.currentText(),
            "last_card_index": self.card_combo.currentIndex(),
            "last_card_index_3ds": self.card_combo_3ds.currentIndex(),
        })

    def _find_card_path(self, target_card):
        """Return tuple (country, card_type, index) where *target_card* resides.
        Returns (None, None, None) if not found."""
        for country, data in self.test_data.items():
            dc = data.get("debitcard", {})
            for card_type, card_list in dc.items():
                for idx, c in enumerate(card_list):
                    if c is target_card:
                        return country, card_type, idx
        return None, None, None

    def _write_cards_file(self):
        """Persist current *self.test_data* structure to *CARDS_FILE*."""
        try:
            os.makedirs(os.path.dirname(CARDS_FILE), exist_ok=True)
            with open(CARDS_FILE, "w", encoding="utf-8") as fh:
                json.dump(self.test_data, fh, indent=2)
        except OSError as exc:
            QMessageBox.critical(self, "Save error", f"Could not write cards file: {exc}")

    # ------------------------------------------------------------------
    # Card management actions
    # ------------------------------------------------------------------
    def save_existing_card(self):
        idx = self.card_combo.currentIndex()
        if not (0 <= idx < len(self.flat_cards)):
            QMessageBox.warning(self, "No card selected", "Please select a card to save.")
            return
        _, _, card = self.flat_cards[idx]

        # Update card fields from form
        card["card_number"] = self.card_fields[0].text().strip()
        card["card_name"] = self.card_fields[1].text().strip()
        card["card_due_date"] = self.card_fields[2].text().strip()
        card["card_cvv"] = self.card_fields[3].text().strip()

        # Also persist the current payload editor contents
        payload_data = self.payload_edit.get_json_data()
        if payload_data is None:
            QMessageBox.warning(self, "Invalid JSON", "Payload JSON is invalid and was not saved.")
        else:
            card["custom_payload"] = payload_data

        self._write_cards_file()
        QMessageBox.information(self, "Card saved", "Existing card updated successfully.")
        # Re-populate to refresh display names etc.
        self.populate_card_combo()

    def save_new_card(self):
        idx = self.card_combo.currentIndex()
        if not (0 <= idx < len(self.flat_cards)):
            QMessageBox.warning(self, "No reference card", "Please select a reference card (for country & type) before adding a new one.")
            return
        _, country, ref_card = self.flat_cards[idx]
        # Find card type based on reference card position
        country_ref, card_type, _ = self._find_card_path(ref_card)
        if country_ref is None:
            QMessageBox.critical(self, "Error", "Could not determine card type for new card.")
            return

        # Ask description
        desc, ok = QInputDialog.getText(self, "Card Description", "Description for new card:")
        if not ok or not desc.strip():
            return  # cancelled

        new_card = {
            "card_number": self.card_fields[0].text().strip(),
            "card_name": self.card_fields[1].text().strip(),
            "card_due_date": self.card_fields[2].text().strip(),
            "card_cvv": self.card_fields[3].text().strip(),
            "description": desc.strip(),
        }

        # Include payload if valid
        payload_data = self.payload_edit.get_json_data()
        if payload_data is not None:
            new_card["custom_payload"] = payload_data

        self.test_data[country_ref]["debitcard"].setdefault(card_type, []).append(new_card)
        self._write_cards_file()
        QMessageBox.information(self, "Card added", "New card added successfully.")
        self.populate_card_combo()
        # Select the newly added card (last index)
        self.card_combo.setCurrentIndex(self.card_combo.count() - 1)

    def delete_current_card(self):
        idx = self.card_combo.currentIndex()
        if not (0 <= idx < len(self.flat_cards)):
            QMessageBox.warning(self, "No card selected", "Please select a card to delete.")
            return
        display, _, card = self.flat_cards[idx]
        reply = QMessageBox.question(self, "Confirm Delete", f"Delete card '{display}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return

        country, card_type, card_idx = self._find_card_path(card)
        if country is None:
            QMessageBox.critical(self, "Error", "Could not locate card in data structure.")
            return
        del self.test_data[country]["debitcard"][card_type][card_idx]
        # Clean up if list empty
        if not self.test_data[country]["debitcard"][card_type]:
            del self.test_data[country]["debitcard"][card_type]
        self._write_cards_file()
        QMessageBox.information(self, "Card deleted", "Card removed successfully.")
        self.populate_card_combo()

    def reload_cards_from_disk(self):
        try:
            self.test_data = load_json(CARDS_FILE)
        except Exception as exc:
            QMessageBox.critical(self, "Load error", str(exc))
            return
        self.populate_card_combo()
        QMessageBox.information(self, "Reloaded", "Cards reloaded from disk.")

    # ------------------------------------------------------------------
    # 3DS Tab Methods
    # ------------------------------------------------------------------
    def populate_card_combo_3ds(self):
        self.flat_cards_3ds = self.flatten_cards()
        self.card_combo_3ds.clear()
        self.card_combo_3ds.addItems([t[0] for t in self.flat_cards_3ds])
        if self.flat_cards_3ds:
            self.card_combo_3ds.setCurrentIndex(0)
            self.apply_card_to_form_3ds(self.flat_cards_3ds[0][2])

    def on_card_changed_3ds(self, idx: int):
        if 0 <= idx < len(self.flat_cards_3ds):
            _, _, card = self.flat_cards_3ds[idx]
            self.apply_card_to_form_3ds(card)
            self.update_payload_preview_3ds()

    def apply_card_to_form_3ds(self, card: Dict):
        self.card_fields_3ds[0].setText(card["card_number"])
        self.card_fields_3ds[1].setText(card["card_name"])
        self.card_fields_3ds[2].setText(card["card_due_date"])
        self.card_fields_3ds[3].setText(card["card_cvv"])

    def current_card_country_and_data_3ds(self):
        idx = self.card_combo_3ds.currentIndex()
        if not (0 <= idx < len(self.flat_cards_3ds)):
            return None, None, None
        display, country, card = self.flat_cards_3ds[idx]
        customer = self.test_data[country]["customer_data"]
        return country, card, customer

    def update_payload_preview_3ds(self):
        """Regenerate the payload preview based on current UI state for 3DS tab."""
        if self._syncing:
            return  # Prevent feedback loops

        country, card, customer = self.current_card_country_and_data_3ds()
        if not card:
            return

        # Prepare the up-to-date card dict based on current UI entries
        ui_card = {
            "card_number": self.card_fields_3ds[0].text().strip(),
            "card_name": self.card_fields_3ds[1].text().strip(),
            "card_due_date": self.card_fields_3ds[2].text().strip(),
            "card_cvv": self.card_fields_3ds[3].text().strip(),
        }

        # Start from saved custom payload for 3DS (if any) so we don't discard user tuning
        if card.get("custom_payload_3ds"):
            payload = copy.deepcopy(card["custom_payload_3ds"])
            try:
                payload["payment"]["card"].update(ui_card)
                # Always use the current API key from UI, never from saved payload
                payload["integration_key"] = self.key_edit.text() or "{integration_key}"
                
                # Handle soft descriptor in card object
                if self.soft_descriptor_checkbox.isChecked() and self.soft_descriptor_edit.text().strip():
                    payload["payment"]["card"]["soft_descriptor"] = self.soft_descriptor_edit.text().strip()
                elif "soft_descriptor" in payload["payment"]["card"]:
                    # Remove soft descriptor if checkbox is unchecked
                    del payload["payment"]["card"]["soft_descriptor"]
            except (KeyError, TypeError):
                # Fallback to rebuilding if structure is unexpected
                payload = self.build_payload_3ds(country, ui_card, customer)
        else:
            payload = self.build_payload_3ds(country, ui_card, customer)

        # Temporarily block signals to avoid recursive updates when we set text
        self._syncing = True
        self.payload_edit_3ds.set_json_text(payload)
        self._syncing = False

    def on_card_field_changed_3ds(self):
        """Called whenever the user edits one of the card QLineEdits in 3DS tab."""
        if self._syncing:
            return
        self.update_payload_preview_3ds()

    def on_payload_changed_3ds(self):
        """Keep card form fields and API key in sync when the payload editor changes in 3DS tab."""
        if self._syncing:
            return

        data = self.payload_edit_3ds.get_json_data()
        if not data:
            return  # Invalid / incomplete JSON – ignore until valid

        self._syncing = True
        
        # Update card form fields
        try:
            card_data = data["payment"]["card"]
            for fld, key in zip(self.card_fields_3ds, ["card_number", "card_name", "card_due_date", "card_cvv"]):
                fld.setText(str(card_data.get(key, "")))
        except (KeyError, TypeError):
            pass  # Card data not available or structure unexpected
        
        # Update API key field if present in payload
        if "integration_key" in data:
            api_key = data["integration_key"]
            if api_key and api_key != "{integration_key}":
                self.key_edit.setText(str(api_key))
        
        # Update soft descriptor settings from payload
        try:
            card_data = data["payment"]["card"]
            if "soft_descriptor" in card_data:
                self.soft_descriptor_edit.setText(str(card_data["soft_descriptor"]))
                self.soft_descriptor_checkbox.setChecked(True)
            else:
                self.soft_descriptor_checkbox.setChecked(False)
        except (KeyError, TypeError):
            pass  # Card data not available or structure unexpected
        
        self._syncing = False

    def format_payload_json_3ds(self):
        """Format the payload JSON in 3DS tab."""
        if self.payload_edit_3ds.format_json():
            QMessageBox.information(self, "Formatted", "JSON has been formatted successfully.")
        else:
            QMessageBox.warning(self, "Invalid JSON", "The payload contains invalid JSON that cannot be formatted.")

    def clear_response_3ds(self):
        """Clear the response display in 3DS tab."""
        self.response_edit_3ds.clear()
        # Disable 3DS button when clearing response
        self.authenticate_3ds_btn_3ds.setEnabled(False)

    def build_payload_3ds(self, country: str, card: Dict, customer: Dict):
        """Build payload for 3DS with auto_capture: false and threeds_force: true."""
        payload = {
            "integration_key": self.key_edit.text() or "{integration_key}",
            "operation": "request",
            "payment": {
                "amount_total": customer["default_amount"],
                "currency_code": customer["currency_code"],
                "name": customer["name"],
                "email": customer["email"],
                "birth_date": customer["birth_date"],
                "country": customer["country"],
                "phone_number": customer["phone_number"],
                "card": {
                    "card_number": card["card_number"],
                    "card_name": card["card_name"],
                    "card_due_date": card["card_due_date"],
                    "card_cvv": card["card_cvv"],
                    "auto_capture": False,  # 3DS specific: no auto capture
                    "threeds_force": True,  # 3DS specific: force 3DS
                },
            },
        }

        # Add soft descriptor to card object if checkbox is checked
        if self.soft_descriptor_checkbox.isChecked() and self.soft_descriptor_edit.text().strip():
            payload["payment"]["card"]["soft_descriptor"] = self.soft_descriptor_edit.text().strip()

        return payload

    def run_test_3ds(self):
        """Run API test for 3DS tab."""
        self.logger.info("Starting API test for 3DS")
        
        country, card, customer = self.current_card_country_and_data_3ds()
        if not card:
            self.logger.warning("No card selected for 3DS test")
            QMessageBox.warning(self, "No card", "Please select a card first")
            return

        ptp = self.ptp_combo_3ds.currentText()
        if not ptp:
            self.logger.warning("No PTP selected for 3DS test")
            QMessageBox.warning(self, "No PTP", "Please select a PTP first")
            return

        if not self.key_edit.text():
            self.logger.warning("No integration key provided for 3DS test")
            QMessageBox.warning(self, "No key", "Please enter Integration Key")
            return

        # Use the JSON currently in the payload editor as the request body
        payload_data = self.payload_edit_3ds.get_json_data()
        if payload_data is None:
            self.logger.error("Invalid JSON payload for 3DS test")
            QMessageBox.critical(self, "Invalid JSON", "Payload JSON is invalid.")
            return

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "EBANX-PTP-Tester/Qt",
            "X-EBANX-Custom-Payment-Type-Profile": ptp,
        }
        url = f"{self.base_url_edit.text().rstrip('/')}/ws/direct"
        
        self.logger.info(f"Making 3DS API call to {url} with PTP: {ptp}")
        self.logger.info(f"Card: {card.get('description', 'Unknown')}")
        self.logger.info(f"Country: {country}")

        # ------------------------------------------------------------------
        # Observability – show the cURL command first
        # ------------------------------------------------------------------
        self.run_btn_3ds.setEnabled(False)
        # Disable 3DS button when starting new API call
        self.authenticate_3ds_btn_3ds.setEnabled(False)

        curl_cmd = self._build_curl_command(url, ptp, payload_data)

        # Show cURL preview and waiting message
        self.response_edit_3ds.appendPlainText("🔧 cURL Command:\n")
        self.response_edit_3ds.appendPlainText(curl_cmd)
        self.response_edit_3ds.appendPlainText("\n\n⏳ Waiting for response...\n")
        QApplication.processEvents()

        # Prepare header that will be shown once the response is available
        request_info = (
            f"🌐 POST {url}\n"
            f"📋 PTP: {ptp}\n"
            f"💳 Card: {card['description']}\n"
            f"🔐 3DS Mode: auto_capture=false, threeds_force=true\n"
            f"⏰ {datetime.now().strftime('%H:%M:%S')}\n"
            + "─" * 50 + "\n"
        )
 
        # Create a worker and a QThread to run the network request without blocking the UI
        self._api_thread_3ds = QThread(self)  # Keep reference as attribute
        worker = APICallWorker(url, payload_data, headers)
        worker.moveToThread(self._api_thread_3ds)
        self._api_worker_3ds = worker  # Prevent garbage collection

        # Wire up signals
        self._api_thread_3ds.started.connect(worker.run)
        worker.finished.connect(self._handle_api_response_3ds)
        worker.error.connect(self._handle_api_error_3ds)

        # Ensure thread stops/cleans up
        worker.finished.connect(self._api_thread_3ds.quit)
        worker.error.connect(self._api_thread_3ds.quit)
        self._api_thread_3ds.finished.connect(worker.deleteLater)
        self._api_thread_3ds.finished.connect(self._api_thread_3ds.deleteLater)

        # Persist request info for handlers
        self._latest_request_info_3ds = request_info

        # Start the background job
        self._api_thread_3ds.start()

    def _handle_api_response_3ds(self, resp):
        """Handle API response for 3DS tab."""
        self.logger.info(f"3DS API response received: {resp.status_code} {resp.reason}")
        
        # Append response header below the existing cURL preview so it's not lost
        self.response_edit_3ds.appendPlainText("\n" + self._latest_request_info_3ds)
        
        # Enhanced response display with status color coding
        status_text = f"📊 Status: {resp.status_code} {resp.reason}\n"
        if resp.status_code >= 200 and resp.status_code < 300:
            status_text += "✅ Success\n"
            self.logger.info("3DS API call successful")
        elif resp.status_code >= 400 and resp.status_code < 500:
            status_text += "❌ Client Error\n"
            self.logger.warning(f"3DS API client error: {resp.status_code}")
        elif resp.status_code >= 500:
            status_text += "🔥 Server Error\n"
            self.logger.error(f"3DS API server error: {resp.status_code}")
        else:
            status_text += "⚠️  Other Status\n"
            self.logger.warning(f"3DS API unexpected status: {resp.status_code}")
        
        self.response_edit_3ds.appendPlainText(status_text)
        
        try:
            response_data = resp.json()
            self.response_edit_3ds.appendPlainText("📄 Response Body:\n")
            self.response_edit_3ds.set_json_text(response_data)
            # Check for 3DS URL and enable/disable authentication button
            self._check_for_3ds_url_3ds(response_data)
        except ValueError:
            self.response_edit_3ds.appendPlainText("📄 Response Text:\n")
            self.response_edit_3ds.appendPlainText(resp.text)
            # Disable 3DS button if response is not JSON
            self.authenticate_3ds_btn_3ds.setEnabled(False)
                
        self.run_btn_3ds.setEnabled(True)
        # Persist latest settings
        self._persist_settings()

    def _handle_api_error_3ds(self, error_msg: str):
        """Handle API error for 3DS tab."""
        self.logger.error(f"3DS API call failed: {error_msg}")
        
        # Append error information below preview
        self.response_edit_3ds.appendPlainText("\n" + self._latest_request_info_3ds)
        self.response_edit_3ds.appendPlainText(f"❌ Error: {error_msg}")
        self.run_btn_3ds.setEnabled(True)
        # Persist latest settings
        self._persist_settings()

    def update_ptp_filter_3ds(self, text: str):
        """Filter the PTP combo box items based on *text* for 3DS tab."""
        text = text.strip().lower()
        current = self.ptp_combo_3ds.currentText()
        self.ptp_combo_3ds.blockSignals(True)
        self.ptp_combo_3ds.clear()
        if text:
            filtered = [ptp for ptp in self.ptp_list if text in ptp.lower()]
        else:
            filtered = self.ptp_list
        self.ptp_combo_3ds.addItems(filtered)
        self.ptp_combo_3ds.blockSignals(False)
        # Try to keep previous selection if still available, else select first
        if current in filtered:
            self.ptp_combo_3ds.setCurrentText(current)
        elif self.ptp_combo_3ds.count():
            self.ptp_combo_3ds.setCurrentIndex(0)

    def save_existing_card_3ds(self):
        """Save existing card in 3DS tab."""
        idx = self.card_combo_3ds.currentIndex()
        if not (0 <= idx < len(self.flat_cards_3ds)):
            QMessageBox.warning(self, "No card selected", "Please select a card to save.")
            return
        _, _, card = self.flat_cards_3ds[idx]

        # Update card fields from form
        card["card_number"] = self.card_fields_3ds[0].text().strip()
        card["card_name"] = self.card_fields_3ds[1].text().strip()
        card["card_due_date"] = self.card_fields_3ds[2].text().strip()
        card["card_cvv"] = self.card_fields_3ds[3].text().strip()

        # Also persist the current payload editor contents to 3DS payload
        payload_data = self.payload_edit_3ds.get_json_data()
        if payload_data is None:
            QMessageBox.warning(self, "Invalid JSON", "Payload JSON is invalid and was not saved.")
        else:
            card["custom_payload_3ds"] = payload_data

        self._write_cards_file()
        QMessageBox.information(self, "Card saved", "Existing card updated successfully.")
        # Re-populate to refresh display names etc.
        self.populate_card_combo_3ds()

    def save_new_card_3ds(self):
        """Save new card in 3DS tab."""
        idx = self.card_combo_3ds.currentIndex()
        if not (0 <= idx < len(self.flat_cards_3ds)):
            QMessageBox.warning(self, "No reference card", "Please select a reference card (for country & type) before adding a new one.")
            return
        _, country, ref_card = self.flat_cards_3ds[idx]
        # Find card type based on reference card position
        country_ref, card_type, _ = self._find_card_path(ref_card)
        if country_ref is None:
            QMessageBox.critical(self, "Error", "Could not determine card type for new card.")
            return

        # Ask description
        desc, ok = QInputDialog.getText(self, "Card Description", "Description for new card:")
        if not ok or not desc.strip():
            return  # cancelled

        new_card = {
            "card_number": self.card_fields_3ds[0].text().strip(),
            "card_name": self.card_fields_3ds[1].text().strip(),
            "card_due_date": self.card_fields_3ds[2].text().strip(),
            "card_cvv": self.card_fields_3ds[3].text().strip(),
            "description": desc.strip(),
        }

        # Include payload if valid
        payload_data = self.payload_edit_3ds.get_json_data()
        if payload_data is not None:
            new_card["custom_payload_3ds"] = payload_data

        self.test_data[country_ref]["debitcard"].setdefault(card_type, []).append(new_card)
        self._write_cards_file()
        QMessageBox.information(self, "Card added", "New card added successfully.")
        self.populate_card_combo_3ds()
        # Select the newly added card (last index)
        self.card_combo_3ds.setCurrentIndex(self.card_combo_3ds.count() - 1)

    def delete_current_card_3ds(self):
        """Delete current card in 3DS tab."""
        idx = self.card_combo_3ds.currentIndex()
        if not (0 <= idx < len(self.flat_cards_3ds)):
            QMessageBox.warning(self, "No card selected", "Please select a card to delete.")
            return
        display, _, card = self.flat_cards_3ds[idx]
        reply = QMessageBox.question(self, "Confirm Delete", f"Delete card '{display}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return

        country, card_type, card_idx = self._find_card_path(card)
        if country is None:
            QMessageBox.critical(self, "Error", "Could not locate card in data structure.")
            return
        del self.test_data[country]["debitcard"][card_type][card_idx]
        # Clean up if list empty
        if not self.test_data[country]["debitcard"][card_type]:
            del self.test_data[country]["debitcard"][card_type]
        self._write_cards_file()
        QMessageBox.information(self, "Card deleted", "Card removed successfully.")
        self.populate_card_combo_3ds()

    def reload_cards_from_disk_3ds(self):
        """Reload cards from disk for 3DS tab."""
        try:
            self.test_data = load_json(CARDS_FILE)
        except Exception as exc:
            QMessageBox.critical(self, "Load error", str(exc))
            return
        self.populate_card_combo_3ds()
        QMessageBox.information(self, "Reloaded", "Cards reloaded from disk.")

    # ------------------------------------------------------------------
    # 3DS Authentication Methods
    # ------------------------------------------------------------------
    def _check_for_3ds_url_3ds(self, response_data):
        """Check for 3DS redirect URL in response for 3DS tab and enable/disable authentication button."""
        try:
            # Look for threeds_redirect_url in the response
            if (isinstance(response_data, dict) and 
                response_data.get("payment", {}).get("threedsecure", {}).get("threeds_redirect_url")):
                
                redirect_url = response_data["payment"]["threedsecure"]["threeds_redirect_url"]
                if redirect_url and redirect_url.startswith("http"):
                    # Store the URL for later use
                    self._current_3ds_url_3ds = redirect_url
                    self.authenticate_3ds_btn_3ds.setEnabled(True)
                    self.logger.info(f"3DS URL detected in 3DS tab: {redirect_url}")
                    return
            
            # No valid 3DS URL found
            self.authenticate_3ds_btn_3ds.setEnabled(False)
            self._current_3ds_url_3ds = None
            
        except (KeyError, TypeError, AttributeError):
            # Disable button if there's any error parsing the response
            self.authenticate_3ds_btn_3ds.setEnabled(False)
            self._current_3ds_url_3ds = None

    def authenticate_3ds_in_browser_3ds(self):
        """Open the 3DS authentication URL in the user's default browser for 3DS tab."""
        if hasattr(self, '_current_3ds_url_3ds') and self._current_3ds_url_3ds:
            try:
                webbrowser.open(self._current_3ds_url_3ds)
                self.logger.info(f"Opened 3DS URL in browser (3DS tab): {self._current_3ds_url_3ds}")
                QMessageBox.information(self, "3DS Authentication", 
                    f"3DS authentication page opened in your browser.\n\n"
                    f"Complete the authentication process in your browser, then return to this app.")
            except Exception as e:
                self.logger.error(f"Failed to open 3DS URL (3DS tab): {e}")
                QMessageBox.critical(self, "Browser Error", 
                    f"Failed to open browser: {str(e)}\n\n"
                    f"Please manually open this URL:\n{self._current_3ds_url_3ds}")
        else:
            QMessageBox.warning(self, "No 3DS URL", "No valid 3DS authentication URL found.")

    def closeEvent(self, event):
        self._persist_settings()
        super().closeEvent(event)

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    # Setup logging
    logger = setup_logging()
    logger.info("Starting EBANX PTP Tester application")
    
    app = QApplication(sys.argv)
    logger.info("QApplication created")
    
    w = TesterWindow()
    logger.info("TesterWindow created")
    
    w.show()
    logger.info("Window displayed, entering event loop")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 