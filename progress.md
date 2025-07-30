# EBANX PTP Testing Tool - Progress Tracking

## Project Overview
Python-based GUI application for testing payment methods across multiple Payment Type Profiles (PTPs) using the EBANX API. This is an internal testing tool for corporate use behind firewall with daily-changing API keys.

## MVP Implementation (Today)

### **✅ COMPLETED - Foundation & Core Structure**
- [x] Project setup with Python structure
- [x] Choose GUI framework (PySide6 Qt)
- [x] Create requirements.txt with dependencies
- [x] Set up project structure with src/gui/
- [x] Basic GUI framework with two-panel layout
- [x] Data loading (test-cards.json, ptp-list.txt)

### **✅ COMPLETED - Card Testing Interface**
- [x] Card selector dropdown with search
- [x] PTP selector dropdown (all PTPs, no filtering)
- [x] Card payment form (number, name, expiry, CVV)
- [x] Live JSON payload generation
- [x] Response display area
- [x] Auto-populate form from selected cards

### **✅ COMPLETED - API Integration**
- [x] Add API configuration (base URL, integration key)
- [x] Implement actual API calls to ws/direct
- [x] Handle API responses and errors
- [x] Add PTP header (X-EBANX-Custom-Payment-Type-Profile)

**Implementation Details:**
- API Configuration panel with Base URL and Integration Key fields
- Test Connection functionality for API validation
- Full API integration with EBANX ws/direct endpoint
- PTP header (X-EBANX-Custom-Payment-Type-Profile) automatically added
- Comprehensive error handling (timeout, connection, request errors)
- Rich response display with JSON formatting and analysis
- Real-time status updates during API calls
- Response analysis with payment status interpretation
- Support for all EBANX response scenarios (SUCCESS, ERROR, PENDING, 3DS)

**Bug Fix - GUI Layout Issues:**
- Identified and resolved broken GUI layout causing empty/broken display
- Simplified widget structure and frame layout
- Removed unnecessary complex components causing layout conflicts
- Improved panel organization and widget placement
- Fixed data loading and widget population issues

**Comprehensive Logging System:**
- ✅ **COMPLETED** - Daily rotating log files in `logs/ebanx_tester_YYYYMMDD.log`
- ✅ **COMPLETED** - Application lifecycle logging (startup, initialization, shutdown)
- ✅ **COMPLETED** - Data loading progress (test cards, PTP list)
- ✅ **COMPLETED** - GUI widget creation and user interaction events
- ✅ **COMPLETED** - API configuration and connection testing
- ✅ **COMPLETED** - Complete API call logging (requests, responses, timing)
- ✅ **COMPLETED** - Error handling and exception tracking with full tracebacks
- ✅ **COMPLETED** - Payment analysis and response interpretation
- ✅ **COMPLETED** - Console and file output for real-time and historical debugging

### **✅ COMPLETED - MVP Polish & Bug Fixes**
- [x] Fixed GUI layout issues and broken widget display
- [x] Simplified and improved UI structure
- [x] Add basic error handling and validation
- [x] Test with actual API calls
- [x] Add comprehensive logging system for debugging
- [x] Handle different response scenarios (success/error/3DS)

## Technical Specifications

### Dependencies (requirements.txt)
```
PySide6>=6.7.0
typer>=0.9.0
rich>=13.7.0
requests>=2.31.0
json5>=0.9.0
```

### Current Project Structure
```
ebanx-ptp-tester/
├── data/
│   ├── ptp-list.txt ✅
│   ├── postman.json ✅
│   └── test-cards.json ✅ (gitignored)
├── run.py ✅ (Primary GUI using Qt)
├── test_data_only.py ✅ (headless logic test)
├── requirements.txt ✅
├── progress.md ✅
└── .gitignore ✅
```

### Test Data File
- **test-cards.json** - Contains all test data organized by country (gitignored for security)

This file contains sensitive test data and is excluded from version control. The structure includes:
- Customer data (name, email, phone, currency) per country
- Test cards organized by country (NG, KE, ZA, EG) and card type
- Mobile money test data (MPESA for Kenya)

## API Endpoints Supported
- `ws/direct` - Direct payment processing
- `ws/capture` - Payment capture
- `ws/query` - Payment status query
- `ws/refund` - Payment refund
- `ws/verifycard` - Card verification

## PTP Categories Identified
From ptp-list.txt analysis:
- **Payment Types**: banktransfer, debitcard
- **Acquirers**: flutterwave, paystack, cellulant, peach, payu
- **Countries**: ng (Nigeria), ke (Kenya), za (South Africa), eg (Egypt)
- **Features**: 3ds, otp, cof, hosted-url, recurrent, sandbox

## Current Status - MVP Complete + 3DS Feature
The application now has a fully functional Qt-based GUI (`run.py`) with both Non-3DS and 3DS testing capabilities. The previous Tkinter implementation has been removed, resolving macOS display issues. The 3DS tab provides the same UI as the Non-3DS tab but sends API calls with `auto_capture: false` and `threeds_force: true` parameters.

## Recent Updates
- **✅ First-Time User Support**: Added automatic creation of `test-cards.json` with dummy data if the file doesn't exist. New users will get test cards for all supported countries (NG, KE, ZA, EG) with proper API payloads.
- **✅ Added ZA Test Card**: South Africa Mastercard (5274600000493614) added to test-cards.json with proper ZAR currency and customer data
- **✅ Data Validation**: Confirmed JSON syntax is valid and test data loads correctly (5 total cards across 4 countries)
- **🔄 Unified State Management**: Card form fields and JSON payload are now bi-directionally synced. Editing card details updates the payload automatically, and modifying the payload JSON updates the card form in real-time.
- **🔍 PTP Filter Added**: Introduced a filter textbox above the PTP dropdown to quickly narrow down profiles.
- **❌ Removed Test Connection**: Test Connection button and its underlying network check were removed to streamline the UI.
- **👁️ Improved Observability (2024-07-27)**: The GUI now displays the full cURL command while the request is in flight, replacing it with the final API response once complete. Added `_build_curl_command` helper and updated `run_test` flow.
- **⚙️ Non-blocking API Calls (2024-07-27)**: `Run Test` now executes the API request in a background `QThread`, disabling the button (greyed out) until the call finishes, so the UI stays responsive.
- **💳 Soft Descriptor Feature (2024-12-19)**: Added soft descriptor support with text input field and checkbox next to the integration key. When enabled, the soft descriptor is added to the card object in the payload. The feature includes bi-directional sync with the JSON payload editor and persistent configuration.
- **📁 Fixed Logs Directory Path (2024-12-19)**: Fixed logs directory creation to be relative to the script's location rather than the current working directory. Now logs will always be created in the project directory regardless of where the script is called from.
- **📑 Tab-Based UI Implementation (2024-12-19)**: Refactored the application to use a tab-based interface with three tabs:
  - **Non-3DS (Unauthenticated)**: Contains all existing functionality for testing unauthenticated card payments
  - **3DS (Authenticated)**: Placeholder tab for future 3DS authentication testing functionality
  - **APMs**: Placeholder tab for future Alternative Payment Methods testing functionality
  The existing card testing interface has been moved to the first tab, maintaining all current functionality while preparing for future feature expansion.
- **🔐 3DS (Authenticated) Implementation (2024-12-19)**: Implemented the 3DS tab with full functionality mirroring the Non-3DS tab but with different API parameters:
  - **auto_capture**: false (no automatic capture)
  - **threeds_force**: true (force 3DS authentication)
  - Complete UI replication with separate card management, payload editing, and API testing
  - Independent card selection, PTP filtering, and response handling
  - All existing features (soft descriptor, logging, error handling) work in 3DS mode
  - **📊 Dual Payload Support**: Updated data structure to support both `custom_payload` (Non-3DS) and `custom_payload_3ds` (3DS) fields in test-cards.json
  - **🔄 Tab-Specific Payloads**: App now uses the appropriate payload based on active tab - Non-3DS tab uses `custom_payload`, 3DS tab uses `custom_payload_3ds`
  - **🔐 3DS Authentication Integration**: Added "Authenticate 3DS in Browser" button in the 3DS tab that automatically detects 3DS redirect URLs in API responses and opens them in the user's default browser
  - **💾 PTP Selection Memory**: App now remembers the last selected PTP for each tab (Non-3DS, 3DS, and APMs) and restores them on startup
- **💳 Card Selection Memory**: App now remembers the last selected card for each tab and restores them on startup
- **💳 APMs Implementation (2024-12-19)**: Implemented full APM (Alternative Payment Methods) functionality with dedicated tab:
  - **📁 APM Data Management**: New `test-apms.json` file with structured APM data organized by country → payment method → profile name
  - **🔄 APM Profile Management**: Complete CRUD operations for APM profiles (Create, Read, Update, Delete)
  - **📋 Dynamic Form Fields**: Smart form that shows/hides fields based on APM type (payment-nested vs direct structure)
  - **🎯 Payload Structure Support**: Handles both payment-nested structures (MPESA, Ozow) and direct structures (Bank Transfer)
  - **💾 Persistent Configuration**: APM tab remembers last selected PTP and maintains state across sessions
  - **🔄 Bidirectional Sync**: APM form fields and JSON payload are fully synchronized - editing the JSON updates the form fields and vice versa
  - **📐 Consistent Layout**: PTP filter and dropdown now span full width of right panel, matching card view layout
  - **🔧 API Integration**: Full API testing with proper payload building, cURL command display, and response analysis
  - **📊 Example APMs Included**: Pre-configured examples for KE-MPESA-Wiza, ZA-Ozow-Wiza RMB, and NG-Bank Transfer-Wiza
- **🔧 Settings Persistence Fix (2024-12-19)**: Fixed AttributeError during application shutdown by adding proper attribute checks in `_persist_settings()` method. The error occurred when the application was closed before all UI components were fully initialized. Added `hasattr()` checks for all combo boxes and wrapped the persistence call in a try-catch block to prevent crashes during shutdown.
- **🎨 APM Response Formatting Enhancement (2024-12-19)**: Updated APM tab to use the same enhanced JSON response formatting as the card views. The APM response section now uses `JSONTextEdit` with syntax highlighting and pretty formatting instead of plain text. Also improved the API response handling to match the card views with proper cURL command display, enhanced status indicators, and consistent formatting.
- **🔒 Privacy Mode Feature (2024-12-19)**: Added "Privacy Mode" checkbox below the Base URL elements in both 3DS and non-3DS views. When enabled, card numbers, CVV, and API keys are masked in the UI showing only the first 6 digits followed by asterisks for card numbers (e.g., `527460**********`), all asterisks for CVV (e.g., `***`), and first 4 + last 4 characters for API keys (e.g., `abcd****wxyz`). Card number, CVV, and API key fields become read-only when privacy mode is enabled to prevent editing of masked data. The payload preview also becomes read-only in privacy mode. **Critical Fix**: API calls now correctly use the original unmasked values even when privacy mode is enabled, ensuring proper API functionality while maintaining UI privacy. **Privacy Enhancement**: cURL commands are hidden when privacy mode is enabled to prevent exposure of sensitive data in the response display. **Data Protection**: Settings persistence now saves original unmasked values when privacy mode is enabled, preventing data loss when the application is closed in privacy mode.

## MVP Completion Status
1. ✅ Add API configuration UI (base URL, integration key)
2. ✅ Implement actual API calls to EBANX ws/direct endpoint
3. ✅ Handle API responses and display results
4. ✅ Comprehensive logging and debugging
5. ✅ **MVP FUNCTIONALLY COMPLETE** - GUI display issue on macOS
6. ✅ Implement card management (save, add, delete) features in Qt GUI
7. ✅ Editable payload with per-card saved custom payload support

## Known Issues
- Users could not previously manage test cards from the UI. ✅ **Fixed** – buttons to save existing cards, add new cards, reload from disk, and delete cards are now part of the Qt interface.
- Payload preview was read-only. ✅ **Fixed** – payload is now editable and can be saved into the selected card profile.

## Diagnostic / Helper Tools
`test_data_only.py` remains for quick logic verification without hitting the network or launching a GUI.

### Core Application Status
- **✅ Fully Functional**: All business logic, API calls, data loading
- **⚠️ Display Issue**: tkinter GUI hangs on macOS (common issue)
- **✅ Production Ready**: API integration works perfectly
- **✅ Debugging**: Comprehensive logging for troubleshooting

## Recommended Next Steps

### For Immediate Use:
1. **Run Qt GUI**: `python3 run.py`
2. **Quick data verification**: `python3 test_data_only.py`

### Future Enhancements:
- [ ] Web interface (Flask/FastAPI) for remote usage
- [ ] Enhanced reporting and export options
- [ ] Import / export test card datasets (CSV / JSON)

## Notes
- Focus on simplicity and usability for internal testing
- No need for fancy UI - functional and fast is priority
- API key changes daily - ensure easy configuration
- Corporate firewall considerations for network requests
- PTP list and postman.json moved to data/ directory for better organization
- **MVP is functionally complete** - Qt GUI resolved previous display issues 