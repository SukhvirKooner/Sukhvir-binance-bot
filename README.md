# Binance Futures Order Bot

A comprehensive CLI-based trading bot for Binance USDT-M Futures (Testnet) that supports market and limit orders, plus advanced order strategies including stop-limit, OCO, TWAP, and grid orders.

## Features

### Core Features (Mandatory)
- ✅ **Market Orders**: Buy/sell orders executed at current market price
- ✅ **Limit Orders**: Buy/sell orders with specified price and time-in-force
- ✅ **CLI Interface**: Command-line interface with comprehensive argument parsing
- ✅ **Input Validation**: Robust validation for all order parameters
- ✅ **Structured Logging**: JSON Lines logging with rotation and sanitization
- ✅ **Error Handling**: Comprehensive error handling with proper exit codes

### Advanced Features (Bonus)
- ✅ **Stop-Limit Orders**: Trigger limit orders when stop price is hit
- ✅ **OCO Orders**: One-Cancels-the-Other orders combining take-profit and stop-loss
- ✅ **TWAP Orders**: Time-Weighted Average Price execution strategy
- ✅ **Grid Orders**: Automated buy-low/sell-high within a price range

## Installation

### Prerequisites
- Python 3.10 or higher
- Binance Futures Testnet account and API credentials

### Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd binance-bot
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the project root:
   ```bash
   BINANCE_API_KEY=your_testnet_api_key
   BINANCE_API_SECRET=your_testnet_api_secret
   BINANCE_TESTNET_BASE_URL=https://testnet.binancefuture.com
   LOG_LEVEL=INFO
   ```

   **Important**: Use only testnet credentials. Never use production API keys.

## Usage

### Basic Commands

#### Place Orders
```bash
# Market buy order
python -m src.cli place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

# Limit sell order
python -m src.cli place --symbol ETHUSDT --side SELL --type LIMIT --price 1600 --quantity 0.01 --time-in-force GTC

# Stop-limit order
python -m src.cli place --symbol BTCUSDT --side BUY --type STOP_LIMIT --price 50000 --stop-price 49000 --quantity 0.001

# OCO order (take profit + stop loss)
python -m src.cli place --symbol BTCUSDT --side BUY --type OCO --price 52000 --stop-price 48000 --quantity 0.001
```

#### Query Order Status
```bash
python -m src.cli status --symbol BTCUSDT --order-id 123456
```

#### Cancel Orders
```bash
python -m src.cli cancel --symbol BTCUSDT --order-id 123456
```

### Advanced Features

#### TWAP Simulation
```bash
# Simulate TWAP order execution
python -m src.cli simulate-twap --symbol BTCUSDT --side BUY --total-quantity 1.0 --duration-minutes 10

# Simulate TWAP with limit orders
python -m src.cli simulate-twap --symbol BTCUSDT --side BUY --total-quantity 1.0 --duration-minutes 10 --order-type LIMIT --price 50000
```

#### Grid Trading Simulation
```bash
# Simulate buy grid
python -m src.cli simulate-grid --symbol BTCUSDT --side BUY --total-quantity 1.0 --min-price 40000 --max-price 50000 --num-levels 10

# Simulate sell grid
python -m src.cli simulate-grid --symbol BTCUSDT --side SELL --total-quantity 1.0 --min-price 40000 --max-price 50000 --num-levels 10
```

### Global Options

```bash
# Dry run mode (validate without placing orders)
python -m src.cli --dry-run place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

# Verbose logging
python -m src.cli --verbose place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

# Use specific profile
python -m src.cli --profile my_profile place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BINANCE_API_KEY` | Binance API key | Required |
| `BINANCE_API_SECRET` | Binance API secret | Required |
| `BINANCE_TESTNET_BASE_URL` | Testnet base URL | `https://testnet.binancefuture.com` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Order Parameters

#### Required Parameters
- `--symbol`: Trading pair (e.g., BTCUSDT, ETHUSDT)
- `--side`: Order side (BUY or SELL)
- `--type`: Order type (MARKET, LIMIT, STOP_LIMIT, OCO)
- `--quantity`: Order quantity (must be positive)

#### Optional Parameters
- `--price`: Order price (required for LIMIT, STOP_LIMIT, OCO)
- `--stop-price`: Stop price (required for STOP_LIMIT, OCO)
- `--time-in-force`: Time in force (GTC, IOC, FOK) - default: GTC
- `--client-order-id`: Client-provided order ID

## Logging

The bot uses structured JSON logging with the following features:

- **Format**: JSON Lines (one JSON object per line)
- **Rotation**: Daily rotation or 10MB file size
- **Retention**: Last 30 files
- **Sanitization**: API secrets are automatically redacted
- **Log File**: `bot.log` in the project root

### Log Entry Example
```json
{
  "timestamp": "2025-01-23T12:00:00Z",
  "level": "INFO",
  "component": "binance_client",
  "event": "order_placed",
  "request": {
    "symbol": "BTCUSDT",
    "side": "BUY",
    "quantity": 0.001
  },
  "response": {
    "orderId": 12345,
    "status": "FILLED",
    "avgPrice": "50000.0"
  }
}
```

## Error Handling

The bot implements comprehensive error handling with proper exit codes:

| Exit Code | Description |
|-----------|-------------|
| 0 | Success |
| 2 | Invalid input/validation error |
| 3 | API error (authentication, network) |
| 4 | Runtime error |

## Testing

### Run Unit Tests
```bash
pytest tests/ -v
```

### Run Integration Tests
```bash
pytest tests/test_integration.py -v
```

### Run with Coverage
```bash
pytest tests/ --cov=src --cov-report=html
```

## Project Structure

```
binance-bot/
├── src/
│   ├── __init__.py
│   ├── cli.py                 # CLI interface
│   ├── config.py              # Configuration management
│   ├── binance_client.py      # Binance API client wrapper
│   ├── validators.py          # Input validation
│   ├── models.py              # Pydantic models
│   ├── orders/
│   │   ├── __init__.py
│   │   ├── market_orders.py   # Market order implementation
│   │   ├── limit_orders.py    # Limit order implementation
│   │   └── advanced/
│   │       ├── __init__.py
│   │       ├── stop_limit.py  # Stop-limit orders
│   │       ├── oco.py         # OCO orders
│   │       ├── twap.py        # TWAP strategy
│   │       └── grid.py        # Grid trading
│   └── utils/
│       ├── __init__.py
│       ├── logger.py          # Structured logging
│       └── retry.py           # Retry decorator
├── tests/
│   ├── __init__.py
│   ├── test_validators.py     # Validator tests
│   ├── test_models.py         # Model tests
│   ├── test_binance_client.py # Client tests
│   ├── test_orders.py         # Order tests
│   └── test_integration.py    # Integration tests
├── requirements.txt           # Dependencies
├── README.md                  # This file
└── bot.log                    # Log file (created at runtime)
```

## Security Notes

- **Never use production API keys** - This bot is designed for testnet only
- **API secrets are automatically sanitized** in logs
- **Environment variables** are used for sensitive configuration
- **Input validation** prevents malicious input
- **Rate limiting** is handled by the Binance client

## Examples

### Example 1: Basic Market Order
```bash
# Place a market buy order for 0.001 BTC
python -m src.cli place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

### Example 2: Limit Order with Custom Time-in-Force
```bash
# Place a limit sell order that expires if not filled immediately
python -m src.cli place --symbol ETHUSDT --side SELL --type LIMIT --price 3700 --quantity 0.01 --time-in-force IOC
```

### Example 3: Stop-Loss Order
```bash
# Place a stop-limit order to limit losses
python -m src.cli place --symbol BTCUSDT --side SELL --type STOP_LIMIT --price 45000 --stop-price 46000 --quantity 0.003
```

### Example 4: TWAP Strategy Simulation
```bash
# Simulate buying 1 BTC over 30 minutes using market orders
python -m src.cli simulate-twap --symbol BTCUSDT --side BUY --total-quantity 1.0 --duration-minutes 30
```

### Example 5: Grid Trading Simulation
```bash
# Simulate a buy grid from $40k to $50k with 20 levels
python -m src.cli simulate-grid --symbol BTCUSDT --side BUY --total-quantity 1.0 --min-price 40000 --max-price 50000 --num-levels 20
```

## Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure you're using testnet credentials
2. **Validation Errors**: Check symbol format and quantity precision
3. **Network Errors**: The bot includes automatic retry logic
4. **Logging Issues**: Check file permissions for `bot.log`

### Getting Help

1. Check the logs in `bot.log` for detailed error information
2. Use `--verbose` flag for debug-level logging
3. Use `--dry-run` flag to validate orders without placing them
4. Review the test cases for usage examples

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is for educational purposes only. Use at your own risk.

## Disclaimer

This software is for educational and testing purposes only. Trading cryptocurrencies involves substantial risk of loss. The authors are not responsible for any financial losses incurred through the use of this software.
