# ETF Analytics Documentation

Welcome to the ETF Analytics documentation. This tool helps you track and visualize ETF performance with a focus on price movements and key metrics.

## Features

- **ETF Price Tracking**: Daily price updates for your ETFs
- **52-Week Metrics**: Track high/low points and important thresholds
- **Decrease Thresholds**: Monitor various decrease levels from 52-week high
- **Interactive Visualization**: Web interface for data exploration

## Quick Start

1. Installation:
   ```bash
   pip install -e .
   ```

2. Configure your environment:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. Initialize the database:
   ```bash
   python -m analytics.database.db_manager
   ```

4. Run the web interface:
   ```bash
   python -m website.app
   ```

## Project Structure

- `analytics/`: Core analytics functionality
  - `database/`: Database management
  - `etl/`: Data pipeline processes
  - `models/`: Analytics calculations
  - `utils/`: Helper utilities
- `website/`: Web interface
- `tests/`: Test suite
- `docs/`: Documentation

## Contributing

See our [Contributing Guide](development/contributing.md) for details on how to:
- Set up your development environment
- Run tests
- Submit pull requests