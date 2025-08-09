# Architecture Documentation

Comprehensive overview of the ETF Analytics Dashboard architecture, design patterns, and technical decisions.

## System Overview

The ETF Analytics Dashboard is built with a **modular ETL architecture** that follows state-of-the-art practices for data processing, currency conversion, and web visualization.

## Architecture Principles

### 1. Separation of Concerns
- **Data Fetching**: Isolated market data retrieval
- **Currency Conversion**: Dedicated conversion pipeline
- **Data Export**: Separate export for web consumption
- **Web Interface**: Independent frontend visualization

### 2. Modular Design
- **Individual Scripts**: Each ETL step is a separate, testable component
- **Workflow Orchestration**: Central coordinator manages the pipeline
- **Configurable Steps**: Individual steps can be run in isolation

### 3. Performance Optimization
- **Batch Processing**: Efficient handling of large datasets
- **Rate Caching**: Avoids repeated API calls
- **Database Indexing**: Optimized query performance
- **Memory Management**: Chunked processing prevents overflow

## ETL Pipeline Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Database      │    │   Market Data   │    │   Currency      │
│  Initialization │───▶│    Fetching     │───▶│  Conversion     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Symbol        │    │   Historical    │    │   EUR Price     │
│   Loading       │    │   Price Data    │    │   Calculation   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ETF Metadata  │    │   OHLCV Data    │    │   Exchange      │
│   Storage       │    │   Storage       │    │   Rate Cache    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Database Design

### Schema Architecture

#### Core Tables
1. **`symbols`**: ETF metadata and configuration
2. **`etf_data`**: Historical price data with EUR conversions
3. **`currency_rates`**: Historical exchange rate cache
4. **`fifty_two_week_metrics`**: Calculated 52-week metrics
5. **`decrease_thresholds`**: Entry point calculations

#### Design Patterns
- **Normalization**: Proper foreign key relationships
- **Indexing Strategy**: Performance-optimized queries
- **Data Integrity**: Constraints and validation
- **Extensibility**: Schema supports future enhancements

### Currency Conversion Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Original      │    │   Historical    │    │   Converted     │
│   Prices        │───▶│   Exchange      │───▶│   EUR Prices    │
│   (USD/GBP)     │    │   Rates         │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Yahoo Finance │    │   Rate Cache    │    │   Batch         │
│   API Call      │    │   Database      │    │   Processing    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Component Architecture

### 1. Workflow Orchestrator (`workflow.py`)
**Responsibilities:**
- Pipeline coordination
- Step sequencing
- Error handling
- Progress tracking

**Design Patterns:**
- **Command Pattern**: Individual step execution
- **Strategy Pattern**: Configurable workflow steps
- **Observer Pattern**: Progress monitoring

### 2. Database Manager (`db_manager.py`)
**Responsibilities:**
- Database connection management
- Schema initialization
- Data operations
- Transaction handling

**Design Patterns:**
- **Singleton Pattern**: Database connection
- **Repository Pattern**: Data access abstraction
- **Unit of Work**: Transaction management

### 3. Currency Converter (`currency_converter.py`)
**Responsibilities:**
- Exchange rate fetching
- Rate caching
- Batch conversion
- Error handling

**Design Patterns:**
- **Cache Pattern**: Rate storage and retrieval
- **Batch Pattern**: Efficient processing
- **Fallback Pattern**: Error recovery

### 4. ETL Components
**Market Data Fetcher:**
- Data source abstraction
- Rate limiting
- Data validation

**Currency Converter ETL:**
- Batch processing
- Database updates
- Verification

**Data Exporter:**
- JSON generation
- File management
- Format optimization

## Performance Architecture

### 1. Batch Processing
- **Currency Conversion**: Process multiple records at once
- **Rate Fetching**: Fetch rates for date ranges, not individual dates
- **Database Operations**: Bulk inserts and updates

### 2. Caching Strategy
- **Exchange Rates**: Store in database to avoid API calls
- **Database Connections**: Connection pooling
- **Query Results**: Optimized queries with proper indexing

### 3. Memory Management
- **Chunked Processing**: Process data in manageable chunks
- **Resource Cleanup**: Proper connection and file handling
- **Garbage Collection**: Automatic memory management

## Scalability Considerations

### 1. Horizontal Scaling
- **Modular Components**: Each step can run independently
- **Database Sharding**: Can be extended for multiple databases
- **Load Balancing**: Multiple instances possible

### 2. Vertical Scaling
- **Database Optimization**: Proper indexing and query optimization
- **Memory Management**: Efficient data structures
- **CPU Utilization**: Parallel processing capabilities

### 3. Data Volume Handling
- **Incremental Updates**: Only fetch new data
- **Data Archiving**: Historical data management
- **Compression**: Efficient storage strategies

## Security Architecture

### 1. Data Protection
- **Local Storage**: No external data transmission
- **Input Validation**: Data sanitization
- **Error Handling**: Secure error messages

### 2. API Security
- **Rate Limiting**: Respect API limits
- **Error Recovery**: Graceful failure handling
- **Data Validation**: Verify data integrity

## Error Handling Architecture

### 1. Graceful Degradation
- **Step Isolation**: Individual step failures don't break pipeline
- **Fallback Mechanisms**: Alternative data sources
- **Partial Success**: Continue with available data

### 2. Comprehensive Logging
- **Structured Logging**: Consistent log format
- **Error Tracking**: Detailed error information
- **Progress Monitoring**: Step-by-step progress

### 3. Recovery Mechanisms
- **Retry Logic**: Automatic retry for transient failures
- **Data Validation**: Ensure data integrity
- **Rollback Capability**: Revert failed operations

## Testing Architecture

### 1. Unit Testing
- **Component Isolation**: Test individual components
- **Mock Dependencies**: Isolate external dependencies
- **Edge Cases**: Comprehensive test coverage

### 2. Integration Testing
- **Pipeline Testing**: End-to-end workflow testing
- **Database Testing**: Data integrity verification
- **API Testing**: External service integration

### 3. Performance Testing
- **Load Testing**: Handle large datasets
- **Memory Testing**: Memory usage optimization
- **Scalability Testing**: Performance under load

## Deployment Architecture

### 1. Development Environment
- **Local Database**: SQLite for development
- **Virtual Environment**: Isolated dependencies
- **Debug Tools**: Comprehensive debugging support

### 2. Production Environment
- **Database Backup**: Regular backup procedures
- **Monitoring**: Performance and error monitoring
- **Scheduling**: Automated data updates

### 3. Configuration Management
- **Environment Variables**: Flexible configuration
- **Database Configuration**: Optimized for production
- **Logging Configuration**: Production-appropriate logging

## Future Enhancements

### 1. Additional Data Sources
- **Multiple APIs**: Support for additional data providers
- **Real-time Data**: Live data streaming capabilities
- **Alternative Currencies**: Support for more currencies

### 2. Advanced Analytics
- **Machine Learning**: Predictive analytics
- **Technical Indicators**: Advanced charting capabilities
- **Portfolio Management**: Multi-asset portfolio tracking

### 3. Performance Improvements
- **Parallel Processing**: Multi-threaded data processing
- **Distributed Computing**: Cloud-based processing
- **Real-time Updates**: Live data synchronization

## Technology Stack

### Backend
- **Python 3.8+**: Core programming language
- **SQLite**: Local database storage
- **pandas**: Data manipulation and analysis
- **yfinance**: Market data API integration

### Frontend
- **HTML5/CSS3**: Modern web standards
- **JavaScript (ES6+)**: Interactive functionality
- **Chart.js**: Data visualization
- **Responsive Design**: Mobile-friendly interface

### Infrastructure
- **Git**: Version control
- **Virtual Environment**: Dependency isolation
- **Requirements.txt**: Dependency management
