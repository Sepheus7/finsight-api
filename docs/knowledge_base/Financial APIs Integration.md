# Financial APIs Integration

*Last Updated: May 24, 2025*  
*Documentation Type: External API Integration Guide*

## 🌐 Overview

FinSight integrates with multiple financial data providers to ensure comprehensive and accurate fact-checking capabilities. This document details the integration strategies, data sources, and implementation approaches for external financial APIs.

## 📊 Primary Data Sources

### 1. Yahoo Finance API

**Primary Use:** Real-time stock prices, market caps, basic financial data

**Integration Status:** ✅ Production Ready

**Capabilities:**
- Real-time and historical stock prices
- Market capitalization data
- Basic company information
- Trading volumes and price changes
- Dividend information

**Implementation:**
```python
class YahooFinanceProvider:
    def __init__(self):
        self.base_url = "https://query1.finance.yahoo.com/v8/finance/chart"
        self.session = requests.Session()
        
    async def get_stock_price(self, ticker: str) -> StockData:
        """Fetch current stock price and market data"""
        url = f"{self.base_url}/{ticker}"
        response = await self.session.get(url)
        data = response.json()
        
        return StockData(
            ticker=ticker,
            price=data['chart']['result'][0]['meta']['regularMarketPrice'],
            market_cap=data['chart']['result'][0]['meta']['marketCap'],
            currency=data['chart']['result'][0]['meta']['currency']
        )
```

**Rate Limits:** No official limits, but implement 1-2 requests/second
**Reliability:** 99.5% uptime
**Cost:** Free (with fair usage)

### 2. SEC EDGAR API

**Primary Use:** Official company filings, financial statements

**Integration Status:** ✅ Production Ready

**Capabilities:**
- 10-K and 10-Q filings
- 8-K current reports
- Proxy statements
- Official company names and CIK mappings

**Implementation:**
```python
class SECEdgarProvider:
    def __init__(self):
        self.base_url = "https://data.sec.gov/api/xbrl"
        self.headers = {
            'User-Agent': 'FinSight/2.1.0 (contact@finsight.com)'
        }
        
    async def get_company_facts(self, cik: str) -> CompanyFacts:
        """Fetch company financial facts from SEC"""
        url = f"{self.base_url}/companyfacts/CIK{cik.zfill(10)}.json"
        response = await self.session.get(url, headers=self.headers)
        
        return CompanyFacts.from_sec_data(response.json())
```

**Rate Limits:** 10 requests/second maximum
**Reliability:** 99.9% uptime
**Cost:** Free (government API)

### 3. Federal Reserve Economic Data (FRED)

**Primary Use:** Economic indicators, interest rates, inflation data

**Integration Status:** ✅ Production Ready

**Capabilities:**
- Federal funds rate
- Inflation rates (CPI, PCE)
- GDP data
- Employment statistics
- Treasury yields

**Implementation:**
```python
class FREDProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.stlouisfed.org/fred"
        
    async def get_economic_indicator(self, series_id: str) -> EconomicData:
        """Fetch economic indicator data"""
        url = f"{self.base_url}/series/observations"
        params = {
            'series_id': series_id,
            'api_key': self.api_key,
            'file_type': 'json',
            'limit': 1,
            'sort_order': 'desc'
        }
        
        response = await self.session.get(url, params=params)
        data = response.json()
        
        return EconomicData.from_fred_data(data)
```

**Rate Limits:** 120 requests/minute
**Reliability:** 99.8% uptime
**Cost:** Free with API key

## 🚀 Secondary Data Sources

### 4. Alpha Vantage API

**Primary Use:** Alternative market data, technical indicators

**Integration Status:** 🔄 Configured (Backup Provider)

**Capabilities:**
- Stock prices and market data
- Technical indicators
- Fundamental data
- Forex and cryptocurrency data

**Rate Limits:** 5 requests/minute (free), 75/minute (premium)
**Cost:** Free tier available, premium plans from $49.99/month

### 5. IEX Cloud API

**Primary Use:** High-quality financial data, news integration

**Integration Status:** 🔄 Configured (Premium Option)

**Capabilities:**
- Real-time and historical market data
- Financial news
- Fundamental data
- Economic indicators

**Rate Limits:** Based on subscription plan
**Cost:** Pay-per-use model, starts at $9/month

### 6. Polygon.io API

**Primary Use:** Professional-grade market data

**Integration Status:** 📋 Planned (Enterprise Feature)

**Capabilities:**
- Real-time market data
- Options and futures data
- Alternative data sources
- News and social sentiment

**Rate Limits:** Based on subscription
**Cost:** Professional plans from $99/month

## 🔄 Data Integration Patterns

### 1. Fallback Strategy

```python
class DataSourceManager:
    def __init__(self):
        self.providers = [
            YahooFinanceProvider(),    # Primary
            AlphaVantageProvider(),    # Secondary
            IEXCloudProvider()         # Tertiary
        ]
        
    async def get_stock_data(self, ticker: str) -> StockData:
        """Get stock data with automatic fallback"""
        
        for provider in self.providers:
            try:
                data = await provider.get_stock_data(ticker)
                if self._validate_data(data):
                    return data
            except Exception as e:
                logger.warning(f"Provider {provider.name} failed: {e}")
                continue
                
        raise NoDataAvailableError(f"All providers failed for {ticker}")
```

### 2. Data Validation & Cross-verification

```python
class DataValidator:
    def __init__(self):
        self.tolerance_percent = 5.0  # 5% tolerance for discrepancies
        
    def cross_validate(self, data_sources: List[StockData]) -> ValidationResult:
        """Cross-validate data from multiple sources"""
        
        if len(data_sources) < 2:
            return ValidationResult(confidence=0.5, status="single_source")
            
        # Compare prices across sources
        prices = [source.price for source in data_sources]
        price_variance = self._calculate_variance(prices)
        
        if price_variance < self.tolerance_percent:
            return ValidationResult(
                confidence=0.95,
                status="validated",
                consensus_value=statistics.mean(prices)
            )
        else:
            return ValidationResult(
                confidence=0.6,
                status="discrepancy_detected",
                variance=price_variance
            )
```

### 3. Caching Strategy

```python
class DataCache:
    def __init__(self):
        self.cache_durations = {
            'stock_price': timedelta(minutes=1),     # Very short for prices
            'market_cap': timedelta(minutes=5),      # Medium for market cap
            'company_info': timedelta(hours=24),     # Long for static data
            'economic_data': timedelta(hours=1)      # Medium for economic data
        }
        
    async def get_cached_data(self, key: str, data_type: str) -> Optional[Any]:
        """Retrieve cached data if still valid"""
        
        cache_entry = await self.redis.get(key)
        if not cache_entry:
            return None
            
        data = json.loads(cache_entry)
        cached_time = datetime.fromisoformat(data['timestamp'])
        max_age = self.cache_durations.get(data_type, timedelta(minutes=5))
        
        if datetime.now() - cached_time < max_age:
            return data['value']
        else:
            await self.redis.delete(key)  # Remove expired data
            return None
```

## 📋 Data Standardization

### Unified Data Models

```python
@dataclass
class StandardizedStockData:
    """Standardized stock data across all providers"""
    ticker: str
    price: Decimal
    currency: str
    market_cap: Optional[Decimal]
    volume: Optional[int]
    timestamp: datetime
    source: str
    confidence: float = 1.0
    
    def __post_init__(self):
        """Validate and normalize data"""
        self.ticker = self.ticker.upper().strip()
        self.price = Decimal(str(self.price)).quantize(Decimal('0.01'))
        if self.market_cap:
            self.market_cap = Decimal(str(self.market_cap))

@dataclass
class StandardizedEconomicData:
    """Standardized economic indicator data"""
    indicator_id: str
    value: Decimal
    unit: str
    period: str  # "2025-Q1", "2025-05", etc.
    timestamp: datetime
    source: str
    seasonally_adjusted: bool = False
```

### Data Transformation Pipeline

```python
class DataTransformer:
    """Transform provider-specific data to standard format"""
    
    def transform_yahoo_data(self, raw_data: dict) -> StandardizedStockData:
        """Transform Yahoo Finance data"""
        chart_data = raw_data['chart']['result'][0]
        meta = chart_data['meta']
        
        return StandardizedStockData(
            ticker=meta['symbol'],
            price=Decimal(str(meta['regularMarketPrice'])),
            currency=meta['currency'],
            market_cap=Decimal(str(meta.get('marketCap', 0))),
            volume=meta.get('regularMarketVolume'),
            timestamp=datetime.fromtimestamp(meta['regularMarketTime']),
            source='yahoo_finance'
        )
        
    def transform_sec_data(self, raw_data: dict) -> CompanyFinancials:
        """Transform SEC EDGAR data"""
        facts = raw_data['facts']['us-gaap']
        
        # Extract revenue data
        revenue_data = facts.get('Revenues', {}).get('units', {}).get('USD', [])
        latest_revenue = max(revenue_data, key=lambda x: x['end']) if revenue_data else None
        
        return CompanyFinancials(
            cik=raw_data['cik'],
            company_name=raw_data['entityName'],
            revenue=Decimal(str(latest_revenue['val'])) if latest_revenue else None,
            revenue_period=latest_revenue['end'] if latest_revenue else None,
            source='sec_edgar'
        )
```

## ⚡ Performance Optimization

### Async Request Batching

```python
class BatchRequestManager:
    def __init__(self, max_concurrent: int = 10):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.session = aiohttp.ClientSession()
        
    async def batch_fetch(self, requests: List[APIRequest]) -> List[APIResponse]:
        """Execute multiple API requests concurrently"""
        
        async def fetch_with_semaphore(request: APIRequest) -> APIResponse:
            async with self.semaphore:
                return await self._execute_request(request)
                
        tasks = [fetch_with_semaphore(req) for req in requests]
        return await asyncio.gather(*tasks, return_exceptions=True)
```

### Connection Pooling

```python
class OptimizedHTTPSession:
    def __init__(self):
        connector = aiohttp.TCPConnector(
            limit=100,              # Total connection pool size
            limit_per_host=20,      # Per-host connection limit
            ttl_dns_cache=300,      # DNS cache TTL
            use_dns_cache=True,
            keepalive_timeout=30
        )
        
        timeout = aiohttp.ClientTimeout(
            total=30,               # Total timeout
            connect=10,             # Connection timeout
            sock_read=20            # Socket read timeout
        )
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': 'FinSight/2.1.0'}
        )
```

## 🔒 Security & Compliance

### API Key Management

```python
class SecureAPIKeyManager:
    def __init__(self):
        self.aws_ssm = boto3.client('ssm')
        self.key_cache = {}
        self.cache_ttl = timedelta(hours=1)
        
    async def get_api_key(self, provider: str) -> str:
        """Securely retrieve API key from AWS Parameter Store"""
        
        cache_key = f"api_key_{provider}"
        if cache_key in self.key_cache:
            cached_data = self.key_cache[cache_key]
            if datetime.now() - cached_data['timestamp'] < self.cache_ttl:
                return cached_data['key']
                
        # Fetch from AWS Parameter Store
        parameter_name = f"/finsight/api_keys/{provider}"
        response = self.aws_ssm.get_parameter(
            Name=parameter_name,
            WithDecryption=True
        )
        
        api_key = response['Parameter']['Value']
        self.key_cache[cache_key] = {
            'key': api_key,
            'timestamp': datetime.now()
        }
        
        return api_key
```

### Rate Limit Management

```python
class RateLimitManager:
    def __init__(self):
        self.rate_limits = {
            'yahoo_finance': RateLimit(requests_per_second=2),
            'sec_edgar': RateLimit(requests_per_second=10),
            'fred': RateLimit(requests_per_minute=120),
            'alpha_vantage': RateLimit(requests_per_minute=5)
        }
        
    async def wait_for_rate_limit(self, provider: str):
        """Wait if necessary to respect rate limits"""
        rate_limit = self.rate_limits.get(provider)
        if rate_limit:
            await rate_limit.wait_if_needed()
```

## 📊 Monitoring & Observability

### API Health Monitoring

```python
class APIHealthMonitor:
    def __init__(self):
        self.health_checks = {}
        self.check_interval = timedelta(minutes=5)
        
    async def monitor_api_health(self):
        """Continuously monitor API provider health"""
        
        while True:
            for provider_name, provider in self.providers.items():
                try:
                    start_time = time.time()
                    test_result = await provider.health_check()
                    response_time = time.time() - start_time
                    
                    self.health_checks[provider_name] = {
                        'status': 'healthy',
                        'response_time': response_time,
                        'last_check': datetime.now(),
                        'consecutive_failures': 0
                    }
                    
                except Exception as e:
                    self._record_failure(provider_name, str(e))
                    
            await asyncio.sleep(self.check_interval.total_seconds())
            
    def _record_failure(self, provider: str, error: str):
        """Record API failure for monitoring"""
        if provider not in self.health_checks:
            self.health_checks[provider] = {'consecutive_failures': 0}
            
        self.health_checks[provider].update({
            'status': 'unhealthy',
            'last_error': error,
            'last_check': datetime.now(),
            'consecutive_failures': self.health_checks[provider]['consecutive_failures'] + 1
        })
        
        # Alert if multiple consecutive failures
        if self.health_checks[provider]['consecutive_failures'] >= 3:
            self._send_alert(provider, error)
```

### Usage Analytics

```python
class APIUsageTracker:
    def __init__(self):
        self.usage_stats = defaultdict(lambda: {
            'requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_response_time': 0.0,
            'data_points_retrieved': 0
        })
        
    def record_api_call(self, provider: str, success: bool, response_time: float, data_points: int = 1):
        """Record API usage statistics"""
        stats = self.usage_stats[provider]
        stats['requests'] += 1
        stats['total_response_time'] += response_time
        stats['data_points_retrieved'] += data_points
        
        if success:
            stats['successful_requests'] += 1
        else:
            stats['failed_requests'] += 1
            
    def get_usage_report(self, time_period: str = 'daily') -> dict:
        """Generate usage report"""
        report = {}
        for provider, stats in self.usage_stats.items():
            if stats['requests'] > 0:
                report[provider] = {
                    'total_requests': stats['requests'],
                    'success_rate': stats['successful_requests'] / stats['requests'],
                    'avg_response_time': stats['total_response_time'] / stats['requests'],
                    'data_points': stats['data_points_retrieved']
                }
        return report
```

## 🔗 Integration Testing

### API Integration Tests

```python
class APIIntegrationTests:
    @pytest.mark.asyncio
    async def test_yahoo_finance_integration(self):
        """Test Yahoo Finance API integration"""
        provider = YahooFinanceProvider()
        
        # Test known ticker
        result = await provider.get_stock_data('AAPL')
        assert result is not None
        assert result.ticker == 'AAPL'
        assert result.price > 0
        assert result.currency == 'USD'
        
    @pytest.mark.asyncio
    async def test_sec_edgar_integration(self):
        """Test SEC EDGAR API integration"""
        provider = SECEdgarProvider()
        
        # Test known CIK (Apple Inc.)
        result = await provider.get_company_facts('0000320193')
        assert result is not None
        assert 'Apple' in result.company_name
        
    @pytest.mark.asyncio
    async def test_data_fallback_mechanism(self):
        """Test fallback between providers"""
        manager = DataSourceManager()
        
        # This should work even if primary provider fails
        result = await manager.get_stock_data('MSFT')
        assert result is not None
        assert result.ticker == 'MSFT'
```

### Load Testing

```python
async def load_test_apis():
    """Load test API integrations"""
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'] * 20
    
    start_time = time.time()
    tasks = [get_stock_data(ticker) for ticker in tickers]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    duration = time.time() - start_time
    successful_requests = sum(1 for r in results if not isinstance(r, Exception))
    
    print(f"Processed {len(tickers)} requests in {duration:.2f}s")
    print(f"Success rate: {successful_requests/len(tickers)*100:.1f}%")
    print(f"Requests per second: {len(tickers)/duration:.1f}")
```

## 🔗 Related Documentation

- [[FinSight - Application Overview]] - System overview
- [[FinSight - Technical Architecture]] - System architecture
- [[FinSight - API Reference]] - FinSight API documentation
- [[AWS Cost Optimization]] - Cost management for external APIs
- [[Performance Benchmarks]] - API performance analysis

---

*This document provides comprehensive coverage of FinSight's external API integrations. For specific implementation details or troubleshooting, consult the individual provider documentation or contact the development team.*
