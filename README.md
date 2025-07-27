# EBANX Production Tester

A Python-based GUI application for testing payment methods across multiple Payment Type Profiles (PTPs) using the EBANX API. This is an internal testing tool designed for corporate use behind firewall with daily-changing API keys.

## Features

- **Multi-PTP Testing**: Test payment methods across different Payment Type Profiles
- **Card Management**: Save, add, delete, and manage test cards with custom payloads
- **Real-time API Testing**: Live JSON payload generation and API response display
- **Comprehensive Logging**: Daily rotating log files for debugging and audit trails
- **Cross-platform GUI**: Built with PySide6 Qt for consistent experience across platforms
- **Non-blocking Operations**: Background API calls keep the UI responsive

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

### Main Interface

The application provides a two-panel layout:

- **Left Panel**: Card selection and payment form
- **Right Panel**: API configuration and response display

### Testing a Payment

1. **Select a Test Card**: Choose from the dropdown or use the search filter
2. **Choose PTP**: Select the Payment Type Profile to test
3. **Configure API**: Enter your EBANX base URL and integration key
4. **Run Test**: Click "Run Test" to execute the API call
5. **View Results**: Check the response display for payment status and details

### Card Management

- **Save Card**: Save current form data as a new test card
- **Add Card**: Create a new test card from scratch
- **Delete Card**: Remove selected test card from the list
- **Reload**: Refresh card data from disk

### Custom Payloads

Each test card can have custom JSON payloads that override the default payment structure. Edit the payload directly in the JSON editor and save it with the card.

## Project Structure

```
eb-tester/
├── data/
│   ├── ptp-list.txt          # Payment Type Profile definitions
│   └── test_cards.json       # Test card data (gitignored)
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

## Configuration

### API Configuration

- **Base URL**: Your EBANX API endpoint
- **Integration Key**: Your daily-changing API key
- **PTP Header**: Automatically added as `X-EBANX-Custom-Payment-Type-Profile`

### Test Data

Test cards are stored in `data/test_cards.json` (excluded from version control for security). The file contains:
- Customer data (name, email, phone, currency) per country
- Test cards organized by country and card type
- Mobile money test data (MPESA for Kenya)

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

- Test card data is excluded from version control
- API keys should be configured securely
- Designed for internal corporate use behind firewall
- Daily API key rotation supported

## Troubleshooting

### Common Issues

1. **GUI Display Issues**: If the interface appears broken, try restarting the application
2. **API Connection Errors**: Verify your base URL and integration key
3. **Card Loading Issues**: Check that `data/test_cards.json` exists and is valid JSON

### Debug Mode

Check the daily log files in the `logs/` directory for detailed debugging information.

## Contributing

This is an internal testing tool. For issues or enhancements, please contact the development team.

## License

Internal corporate tool - not for public distribution. 