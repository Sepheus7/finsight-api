# FinSight - LLM Integration

*Last Updated: May 24, 2025*  
*Version: 2.1.0*  
*Documentation Type: LLM Provider Integration*

## 🤖 LLM Integration Overview

FinSight's **multi-provider LLM strategy** enables flexible deployment across different environments while maintaining consistent functionality. The system supports local models (Ollama), cloud providers (OpenAI/Anthropic), and intelligent fallback mechanisms.

## 🏗️ Provider Architecture

### Multi-Provider Strategy

```text
🦙 Ollama (Local)
├── Advantages: Privacy, cost-free, offline capability
├── Use Cases: Development, on-premise, sensitive data
└── Limitations: Resource intensive, slower processing

☁️ OpenAI (Cloud)
├── Advantages: High quality, fast, reliable
├── Use Cases: Production, high-volume processing
└── Limitations: Cost per token, requires internet

🔮 Anthropic (Cloud Alternative)
├── Advantages: Long context, safety-focused
├── Use Cases: Complex analysis, compliance-heavy
└── Limitations: Higher cost, rate limits

📐 Regex Fallback (Always Available)
├── Advantages: Zero dependencies, ultra-fast
├── Use Cases: Emergency fallback, basic extraction
└── Limitations: Limited accuracy, no reasoning
```

### Intelligent Provider Switching

```python
def select_provider(config: LLMConfig) -> LLMProvider:
    """Smart provider selection with fallback logic"""
    
    # Try primary provider
    if config.provider == 'ollama' and is_ollama_available():
        return OllamaProvider(config)
    
    # Cloud provider fallback
    if config.openai_api_key:
        return OpenAIProvider(config)
    
    if config.anthropic_api_key:
        return AnthropicProvider(config)
    
    # Always available fallback
    return RegexProvider()
```

## 🦙 Ollama Integration

### Local Development Setup

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull recommended models
ollama pull llama3.2:3b        # Fast, efficient
ollama pull llama3.2:8b        # Higher quality  
ollama pull codellama:7b       # Code-focused (optional)

# Start Ollama server
ollama serve
```

### Configuration

```bash
# Environment variables
FINSIGHT_LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
OLLAMA_TIMEOUT=30

# Custom model configuration
OLLAMA_TEMPERATURE=0.1         # Lower = more consistent
OLLAMA_MAX_TOKENS=1000         # Response length limit
OLLAMA_CONTEXT_LENGTH=4096     # Input context window
```

### Python Integration

```python
class OllamaProvider:
    def __init__(self, config: LLMConfig):
        self.base_url = config.ollama_base_url
        self.model = config.ollama_model
        self.timeout = config.timeout
        
    async def extract_claims(self, text: str) -> List[FinancialClaim]:
        """Extract financial claims using Ollama"""
        prompt = self._build_extraction_prompt(text)
        
        try:
            response = await self._call_ollama(prompt)
            return self._parse_claims(response)
        except Exception as e:
            logger.warning(f"Ollama failed: {e}")
            return self._fallback_to_regex(text)
            
    def _call_ollama(self, prompt: str) -> str:
        """Make API call to Ollama"""
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens
                }
            },
            timeout=self.timeout
        )
        return response.json()["response"]
```

### Ollama-Specific Optimizations

```python
# Model warming for faster responses
def warm_ollama_model():
    """Pre-load model for faster subsequent calls"""
    requests.post(f"{OLLAMA_BASE_URL}/api/generate", json={
        "model": OLLAMA_MODEL,
        "prompt": "warm up",
        "stream": False,
        "options": {"num_predict": 1}
    })

# Connection pooling
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retry_strategy = Retry(total=3, backoff_factor=1)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
```

## ☁️ OpenAI Integration

### API Configuration

```bash
# Environment variables
FINSIGHT_LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
FINSIGHT_OPENAI_MODEL=gpt-4o-mini
OPENAI_ORGANIZATION=org-...      # Optional
OPENAI_PROJECT=proj-...          # Optional
```

### Model Selection Strategy

```python
# Production-optimized model selection
MODEL_SELECTION = {
    'fast': 'gpt-4o-mini',          # Cost-efficient, fast
    'quality': 'gpt-4o',           # High quality, slower
    'balanced': 'gpt-4o-mini',     # Recommended default
}

# Dynamic model selection based on claim complexity
def select_openai_model(claim_complexity: str) -> str:
    if claim_complexity == 'simple':
        return 'gpt-4o-mini'
    elif claim_complexity == 'complex':
        return 'gpt-4o'
    else:
        return 'gpt-4o-mini'  # Default
```

### Implementation

```python
import openai
from openai import AsyncOpenAI

class OpenAIProvider:
    def __init__(self, config: LLMConfig):
        self.client = AsyncOpenAI(
            api_key=config.openai_api_key,
            organization=config.openai_organization,
            project=config.openai_project
        )
        self.model = config.model
        
    async def extract_claims(self, text: str) -> List[FinancialClaim]:
        """Extract claims using OpenAI GPT"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text}
                ],
                temperature=0.1,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            claims_data = json.loads(response.choices[0].message.content)
            return [FinancialClaim.from_dict(claim) for claim in claims_data["claims"]]
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise LLMProviderError(f"OpenAI failed: {e}")
```

### Cost Optimization

```python
# Token usage tracking
def track_token_usage(response):
    usage = response.usage
    logger.info(f"Tokens used - Prompt: {usage.prompt_tokens}, "
               f"Completion: {usage.completion_tokens}, "
               f"Total: {usage.total_tokens}")
    
    # Cost calculation (approximate)
    cost = (usage.prompt_tokens * 0.00015 + 
            usage.completion_tokens * 0.0006) / 1000
    logger.info(f"Estimated cost: ${cost:.6f}")

# Batch processing for cost efficiency
async def batch_extract_claims(texts: List[str]) -> List[List[FinancialClaim]]:
    """Process multiple texts efficiently"""
    tasks = [extract_claims(text) for text in texts]
    return await asyncio.gather(*tasks)
```

## 🔮 Anthropic Integration

### Claude Configuration

```bash
# Environment variables
FINSIGHT_LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
FINSIGHT_ANTHROPIC_MODEL=claude-3-haiku-20240307
ANTHROPIC_VERSION=2023-06-01
```

### Model Options

```python
ANTHROPIC_MODELS = {
    'haiku': 'claude-3-haiku-20240307',     # Fast, cost-effective
    'sonnet': 'claude-3-sonnet-20240229',  # Balanced performance
    'opus': 'claude-3-opus-20240229',      # Highest quality
}

# Use case mapping
def select_claude_model(use_case: str) -> str:
    if use_case == 'compliance_analysis':
        return ANTHROPIC_MODELS['opus']     # Highest accuracy for compliance
    elif use_case == 'bulk_processing':
        return ANTHROPIC_MODELS['haiku']    # Cost-efficient for volume
    else:
        return ANTHROPIC_MODELS['haiku']    # Default
```

### Implementation of the Model

```python
import anthropic

class AnthropicProvider:
    def __init__(self, config: LLMConfig):
        self.client = anthropic.AsyncAnthropic(
            api_key=config.anthropic_api_key
        )
        self.model = config.anthropic_model
        
    async def extract_claims(self, text: str) -> List[FinancialClaim]:
        """Extract claims using Claude"""
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.1,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": text}]
            )
            
            # Parse Claude's response
            claims_text = response.content[0].text
            return self._parse_claude_response(claims_text)
            
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise LLMProviderError(f"Claude failed: {e}")
```

## 📐 Regex Fallback System

### Pattern-Based Extraction

```python
class RegexProvider:
    """Always-available fallback extraction"""
    
    FINANCIAL_PATTERNS = {
        'market_cap': [
            r'(?i)(\w+(?:\s+\w+)*)\s+market\s+cap(?:italization)?\s+(?:is|was|reached|hit)\s+\$?([0-9,.]+)\s*(billion|trillion|million)?',
            r'(?i)market\s+cap(?:italization)?\s+of\s+(\w+(?:\s+\w+)*)\s+(?:is|was|reached)\s+\$?([0-9,.]+)\s*(billion|trillion|million)?'
        ],
        'stock_price': [
            r'(?i)(\w+(?:\s+\w+)*)\s+(?:stock|shares?)\s+(?:is|are|was|were)\s+trading\s+at\s+\$?([0-9,.]+)',
            r'(?i)(\w+(?:\s+\w+)*)\s+(?:stock|share)\s+price\s+(?:is|was)\s+\$?([0-9,.]+)'
        ],
        'revenue': [
            r'(?i)(\w+(?:\s+\w+)*)\s+reported\s+\$?([0-9,.]+)\s*(billion|million)?\s+in\s+revenue',
            r'(?i)(\w+(?:\s+\w+)*)\s+revenue\s+(?:was|is|reached)\s+\$?([0-9,.]+)\s*(billion|million)?'
        ]
    }
    
    def extract_claims(self, text: str) -> List[FinancialClaim]:
        """Extract claims using regex patterns"""
        claims = []
        
        for claim_type, patterns in self.FINANCIAL_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    claim = self._create_claim_from_match(claim_type, match)
                    if claim:
                        claims.append(claim)
                        
        return claims
```

### Pattern Optimization

```python
# Advanced regex patterns with improved accuracy
ENHANCED_PATTERNS = {
    'market_cap_with_context': [
        # Matches: "Apple's market cap is $3 trillion"
        r'(?i)(?P<company>\w+(?:\'s|\s+(?:inc|corp|ltd))*)\s+market\s+cap(?:italization)?\s+(?:is|was|reached|hit)\s+\$?(?P<value>[0-9,.]+)\s*(?P<unit>billion|trillion|million)?',
        
        # Matches: "The market capitalization of Microsoft reached $2.8 trillion"
        r'(?i)(?:the\s+)?market\s+cap(?:italization)?\s+of\s+(?P<company>\w+(?:\s+\w+)*)\s+(?:is|was|reached|hit)\s+\$?(?P<value>[0-9,.]+)\s*(?P<unit>billion|trillion|million)?'
    ]
}

# Context-aware extraction
def extract_with_context(text: str) -> List[FinancialClaim]:
    """Enhanced extraction with context analysis"""
    claims = []
    sentences = text.split('.')
    
    for sentence in sentences:
        # Extract potential claims
        raw_claims = extract_raw_claims(sentence)
        
        # Add context from surrounding sentences
        for claim in raw_claims:
            claim.context = get_surrounding_context(sentence, text)
            claims.append(claim)
            
    return claims
```

## 🔄 Provider Switching Logic

### Automatic Failover

```python
class LLMManager:
    def __init__(self, config: LLMConfig):
        self.providers = self._initialize_providers(config)
        self.current_provider_index = 0
        
    async def extract_claims(self, text: str) -> List[FinancialClaim]:
        """Extract claims with automatic provider failover"""
        
        for i, provider in enumerate(self.providers):
            try:
                start_time = time.time()
                claims = await provider.extract_claims(text)
                
                # Track performance
                duration = time.time() - start_time
                self._record_success(provider.__class__.__name__, duration)
                
                return claims
                
            except Exception as e:
                logger.warning(f"Provider {provider.__class__.__name__} failed: {e}")
                self._record_failure(provider.__class__.__name__, str(e))
                
                # Try next provider
                continue
                
        # All providers failed
        raise AllProvidersFailedError("All LLM providers exhausted")
        
    def _initialize_providers(self, config: LLMConfig) -> List[LLMProvider]:
        """Initialize providers in priority order"""
        providers = []
        
        # Primary provider based on configuration
        if config.provider == 'ollama' and self._is_ollama_available():
            providers.append(OllamaProvider(config))
            
        # Cloud provider fallbacks
        if config.openai_api_key:
            providers.append(OpenAIProvider(config))
            
        if config.anthropic_api_key:
            providers.append(AnthropicProvider(config))
            
        # Always include regex fallback
        providers.append(RegexProvider())
        
        return providers
```

### Health Monitoring

```python
class ProviderHealthMonitor:
    def __init__(self):
        self.health_scores = {}
        self.response_times = {}
        self.error_rates = {}
        
    def update_health(self, provider: str, success: bool, response_time: float):
        """Update provider health metrics"""
        if provider not in self.health_scores:
            self.health_scores[provider] = 1.0
            self.response_times[provider] = []
            self.error_rates[provider] = 0.0
            
        # Update response time
        self.response_times[provider].append(response_time)
        if len(self.response_times[provider]) > 100:
            self.response_times[provider].pop(0)
            
        # Update success rate
        if success:
            self.health_scores[provider] = min(1.0, self.health_scores[provider] + 0.01)
        else:
            self.health_scores[provider] = max(0.0, self.health_scores[provider] - 0.1)
            
    def get_best_provider(self) -> str:
        """Return the provider with best health score"""
        if not self.health_scores:
            return "regex"  # Default fallback
            
        return max(self.health_scores.items(), key=lambda x: x[1])[0]
```

## 🎯 Prompt Engineering

### System Prompts

```python
FINANCIAL_CLAIM_EXTRACTION_PROMPT = """
You are a financial data extraction expert. Your task is to identify and extract financial claims from text.

Extract the following types of financial claims:
1. Market capitalization values
2. Stock prices  
3. Revenue figures
4. Financial ratios
5. Economic indicators

For each claim, provide:
- Entity name (company, stock ticker, or economic indicator)
- Claim type (market_cap, stock_price, revenue, etc.)
- Numerical value
- Unit (billion, million, percentage, etc.)
- Confidence level (0.0-1.0)

Return results as JSON array with this structure:
{
  "claims": [
    {
      "entity": "Apple",
      "claim_type": "market_cap", 
      "value": 3000000000000,
      "unit": "USD",
      "confidence": 0.95,
      "original_text": "Apple's market cap is $3 trillion"
    }
  ]
}

Only extract factual financial claims with specific numerical values. Ignore opinions, predictions, or vague statements.
"""

# Model-specific prompt variations
OLLAMA_PROMPT = """
Extract financial claims from this text. Be precise and include only factual numerical claims.

Text: {text}

Return JSON format with claims array containing entity, type, value, unit, confidence.
"""

OPENAI_PROMPT = """
Analyze the following text and extract specific financial claims with numerical values.

Focus on:
- Market capitalization figures
- Stock prices and trading values  
- Revenue and earnings data
- Financial ratios and percentages
- Economic indicators

Text to analyze:
{text}

Return structured JSON with extracted claims including confidence scores.
"""
```

### Response Parsing

```python
def parse_llm_response(response: str, provider: str) -> List[FinancialClaim]:
    """Parse LLM response into structured claims"""
    try:
        # Handle different response formats
        if provider == 'openai':
            data = json.loads(response)
        elif provider == 'anthropic':
            # Claude might return text that needs extraction
            data = extract_json_from_text(response)
        elif provider == 'ollama':
            # Ollama responses might be less structured
            data = parse_ollama_response(response)
            
        claims = []
        for claim_data in data.get('claims', []):
            claim = FinancialClaim(
                text=claim_data.get('original_text', ''),
                claim_type=ClaimType(claim_data.get('claim_type')),
                entity=claim_data.get('entity'),
                metric=claim_data.get('metric', ''),
                value=float(claim_data.get('value', 0)),
                unit=claim_data.get('unit'),
                confidence=float(claim_data.get('confidence', 0.5))
            )
            claims.append(claim)
            
        return claims
        
    except Exception as e:
        logger.error(f"Failed to parse {provider} response: {e}")
        logger.debug(f"Raw response: {response}")
        return []
```

## 📊 Performance Optimization

### Caching Strategy

```python
class LLMCache:
    def __init__(self, cache_duration_hours: int = 24):
        self.cache = {}
        self.cache_duration = timedelta(hours=cache_duration_hours)
        
    def get_cached_result(self, text: str, provider: str) -> Optional[List[FinancialClaim]]:
        """Get cached LLM result if available"""
        cache_key = self._generate_cache_key(text, provider)
        
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if datetime.now() - cached_data['timestamp'] < self.cache_duration:
                return cached_data['claims']
            else:
                # Cache expired
                del self.cache[cache_key]
                
        return None
        
    def cache_result(self, text: str, provider: str, claims: List[FinancialClaim]):
        """Cache LLM result for future use"""
        cache_key = self._generate_cache_key(text, provider)
        self.cache[cache_key] = {
            'claims': claims,
            'timestamp': datetime.now()
        }
        
    def _generate_cache_key(self, text: str, provider: str) -> str:
        """Generate unique cache key"""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return f"{provider}:{text_hash}"
```

### Async Processing

```python
async def parallel_claim_extraction(texts: List[str]) -> List[List[FinancialClaim]]:
    """Process multiple texts concurrently"""
    
    # Create semaphore to limit concurrent requests
    semaphore = asyncio.Semaphore(5)  # Max 5 concurrent requests
    
    async def extract_with_semaphore(text: str) -> List[FinancialClaim]:
        async with semaphore:
            return await llm_manager.extract_claims(text)
    
    # Process all texts concurrently
    tasks = [extract_with_semaphore(text) for text in texts]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle exceptions and return results
    final_results = []
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Extraction failed: {result}")
            final_results.append([])  # Empty result for failed extraction
        else:
            final_results.append(result)
            
    return final_results
```

## 🔗 Related Documentation

- [[FinSight - Application Overview]] - System overview and capabilities
- [[FinSight - Technical Architecture]] - Overall system architecture
- [[FinSight - Deployment Guide]] - Deployment and configuration
- [[LLM Model Comparison]] - Detailed provider performance analysis
- [[Performance Benchmarks]] - LLM integration performance metrics

## 📋 LLM Integration Checklist

### Provider Setup

- [ ] API keys configured and tested
- [ ] Model selection optimized for use case  
- [ ] Rate limits and quotas understood
- [ ] Fallback providers configured
- [ ] Health monitoring enabled

### Performance Optimization  

- [ ] Caching implemented
- [ ] Async processing enabled
- [ ] Token usage tracking active
- [ ] Response time monitoring
- [ ] Error handling robust

### Security & Compliance

- [ ] API keys securely stored
- [ ] Data privacy requirements met
- [ ] Rate limiting implemented
- [ ] Input sanitization active
- [ ] Audit logging enabled

---

*This LLM integration guide provides comprehensive coverage of FinSight's multi-provider strategy. For specific deployment scenarios, see [[FinSight - Deployment Guide]].*
