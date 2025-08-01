# EBANX Production Tester

A Python-based GUI application for testing payment methods across multiple Payment Type Profiles (PTPs) using the EBANX API. This is an internal testing tool designed for corporate use behind firewall with daily-changing API keys.

## Features

- **Multi-PTP Testing**: Test payment methods across different Payment Type Profiles
- **Tab-Based Interface**: Three dedicated tabs for different payment scenarios
  - **Non-3DS (Unauthenticated)**: Standard card payment testing
  - **3DS (Authenticated)**: 3DS authentication testing with browser integration
  - **APMs (Alternative Payment Methods)**: Bank transfers, mobile money, and other payment methods
- **Card Management**: Save, add, delete, and manage test cards with custom payloads
- **APM Profile Management**: Complete CRUD operations for Alternative Payment Methods
- **Real-time API Testing**: Live JSON payload generation and API response display
- **Privacy Mode**: Mask sensitive data (card numbers, CVV, API keys) in the UI
- **Comprehensive Logging**: Daily rotating log files for debugging and audit trails
- **Cross-platform GUI**: Built with PySide6 Qt for consistent experience across platforms
- **Non-blocking Operations**: Background API calls keep the UI responsive
- **Smart Form Fields**: Dynamic form that adapts to payment method type
- **Persistent Settings**: Remembers last selected cards and PTPs across sessions

## Quick Start

### Prerequisites

- Python 3.8+
- Git

### Installation

1. Clone the repository:
```bash
git clone git@github.com:wizaj/eb-tester.git
cd eb-tester
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python3 run.py
```

## Usage

### Tab-Based Interface

The application provides a tabbed interface with three main testing modes:

#### Non-3DS Tab (Unauthenticated)
- Standard card payment testing
- Automatic capture enabled
- Full card management and payload editing
- Real-time API response analysis

#### 3DS Tab (Authenticated)
- 3DS authentication testing
- Manual capture (auto_capture: false)
- Force 3DS authentication (threeds_force: true)
- Browser integration for 3DS redirects
- Independent card management and settings

#### APMs Tab (Alternative Payment Methods)
- Bank transfers, mobile money, and other payment methods
- Dynamic form fields based on payment type
- Support for both payment-nested and direct payload structures
- Complete APM profile management

### Testing a Payment

1. **Select a Tab**: Choose the appropriate testing mode (Non-3DS, 3DS, or APMs)
2. **Select a Test Card/Profile**: Choose from the dropdown or use the search filter
3. **Choose PTP**: Select the Payment Type Profile to test (with filtering support)
4. **Configure API**: Enter your EBANX base URL and integration key
5. **Optional Settings**: Enable privacy mode or soft descriptor as needed
6. **Run Test**: Click "Run Test" to execute the API call
7. **View Results**: Check the response display for payment status and details

### Card Management

- **Save Card**: Save current form data as a new test card
- **Add Card**: Create a new test card from scratch
- **Delete Card**: Remove selected test card from the list
- **Reload**: Refresh card data from disk

### APM Profile Management

- **Save Profile**: Save current APM configuration as a new profile
- **Add Profile**: Create a new APM profile from scratch
- **Delete Profile**: Remove selected APM profile from the list
- **Reload**: Refresh APM data from disk

### Custom Payloads

Each test card can have custom JSON payloads that override the default payment structure:
- **Non-3DS**: Uses `custom_payload` field
- **3DS**: Uses `custom_payload_3ds` field
- **APMs**: Uses `custom_payload` field with dynamic structure

Edit the payload directly in the JSON editor and save it with the card/profile.

### Privacy Mode

Enable privacy mode to mask sensitive data in the UI:
- Card numbers show as `527460**********`
- CVV shows as `***`
- API keys show as `abcd****wxyz`
- cURL commands are hidden to prevent data exposure
- Original values are preserved for API calls

## Project Structure

```
eb-tester/
├── data/
│   ├── ptp-list.txt          # Payment Type Profile definitions
│   ├── test-cards.json       # Test card data (gitignored)
│   └── test-apms.json       # APM profile data (gitignored)
├── logs/                     # Daily rotating log files
├── src/
│   └── gui/                  # GUI components
├── qt_gui.py                 # Main Qt GUI implementation
├── run.py                    # Application entry point
├── test_data_only.py         # Headless testing utility
├── config_util.py            # Configuration utilities
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## API Endpoints Supported

- `ws/direct` - Direct payment processing
- `ws/capture` - Payment capture
- `ws/query` - Payment status query
- `ws/refund` - Payment refund
- `ws/verifycard` - Card verification

## PTP Categories

The tool supports various Payment Type Profiles across multiple countries:

- **Payment Types**: banktransfer, debitcard
- **Acquirers**: flutterwave, paystack, cellulant, peach, payu
- **Countries**: ng (Nigeria), ke (Kenya), za (South Africa), eg (Egypt)
- **Features**: 3ds, otp, cof, hosted-url, recurrent, sandbox

## APM Support

The APMs tab supports various alternative payment methods:

- **Mobile Money**: MPESA (Kenya)
- **Bank Transfers**: Direct bank transfers
- **Digital Wallets**: Ozow (South Africa)
- **Dynamic Structure**: Supports both payment-nested and direct payload structures

## Configuration

### API Configuration

- **Base URL**: Your EBANX API endpoint
- **Integration Key**: Your daily-changing API key
- **PTP Header**: Automatically added as `X-EBANX-Custom-Payment-Type-Profile`
- **Soft Descriptor**: Optional merchant descriptor for card payments

### Test Data

Test data is stored in separate files (excluded from version control for security):

- **test-cards.json**: Contains customer data and test cards organized by country
- **test-apms.json**: Contains APM profiles organized by country → payment method → profile name

## Logging

The application provides comprehensive logging:

- **Daily Log Files**: `logs/ebanx_tester_YYYYMMDD.log`
- **Application Lifecycle**: Startup, initialization, shutdown events
- **API Calls**: Complete request/response logging with timing
- **Error Tracking**: Full exception tracebacks and error handling
- **User Interactions**: GUI events and data loading progress

## Development

### Dependencies

- `PySide6>=6.7.0` - Qt GUI framework
- `requests>=2.31.0` - HTTP client for API calls
- `json5>=0.9.0` - Enhanced JSON parsing

### Testing

For quick logic verification without GUI:
```bash
python3 test_data_only.py
```

## Security Notes

- Test card and APM data is excluded from version control
- API keys should be configured securely
- Privacy mode available for sensitive data protection
- Designed for internal corporate use behind firewall
- Daily API key rotation supported

## Troubleshooting

### Common Issues

1. **GUI Display Issues**: If the interface appears broken, try restarting the application
2. **API Connection Errors**: Verify your base URL and integration key
3. **Card Loading Issues**: Check that `data/test-cards.json` exists and is valid JSON
4. **APM Loading Issues**: Check that `data/test-apms.json` exists and is valid JSON

### Debug Mode

Check the daily log files in the `logs/` directory for detailed debugging information.

## Recent Updates

- **Tab-Based UI**: Refactored to use tabs for Non-3DS, 3DS, and APMs testing
- **3DS Authentication**: Full 3DS testing with browser integration for redirects
- **APMs Implementation**: Complete Alternative Payment Methods support with dynamic forms
- **Privacy Mode**: Mask sensitive data in the UI while preserving functionality
- **Persistent Settings**: Remember last selected cards and PTPs across sessions
- **Enhanced Response Formatting**: Improved JSON display with syntax highlighting
- **Non-blocking API Calls**: Background thread execution for responsive UI

## Contributing

This is an internal testing tool. For issues or enhancements, please contact the development team.

## License

Internal corporate tool - not for public distribution. 