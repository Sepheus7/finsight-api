// API client for FinSight
class FinSightAPI {
    constructor() {
        this.baseUrl = 'http://localhost:8000';
        this.awsRegion = 'us-east-1';
        this.awsCredentials = null;
        this.config = null;
    }

    setBaseUrl(url) {
        this.baseUrl = url;
    }

    async loadConfig() {
        try {
            const response = await fetch(`${this.baseUrl}/config`);
            this.config = await response.json();
            
            // Set AWS credentials if available
            if (this.config.aws && this.config.aws.accessKeyId && this.config.aws.secretAccessKey) {
                this.awsCredentials = {
                    accessKeyId: this.config.aws.accessKeyId,
                    secretAccessKey: this.config.aws.secretAccessKey
                };
                this.awsRegion = this.config.aws.region || 'us-east-1';
            }
            
            // Update base URL if provided in config
            if (this.config.api && this.config.api.baseUrl) {
                this.baseUrl = this.config.api.baseUrl;
            }
            
            console.log('Configuration loaded successfully');
        } catch (error) {
            console.error('Failed to load configuration:', error);
            this.config = null;
            this.awsCredentials = null;
        }
    }

    async loadAWSCredentials() {
        // Deprecated method - use loadConfig() instead
        await this.loadConfig();
    }

    async makeRequest(method, endpoint, data = null) {
        try {
            const url = `${this.baseUrl}${endpoint}`;
            const options = {
                method,
                headers: {
                    'Content-Type': 'application/json'
                }
            };

            if (data) {
                options.body = JSON.stringify(data);
            }

            // Add AWS SigV4 signing for production requests
            if (this.baseUrl.includes('execute-api') && this.awsCredentials) {
                const signedRequest = await this.signRequest(url, method, data);
                Object.assign(options, signedRequest);
            }

            const response = await fetch(url, options);
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    async signRequest(url, method, data) {
        if (!this.awsCredentials) {
            await this.loadConfig();
        }

        if (!this.awsCredentials) {
            throw new Error('AWS credentials not available');
        }

        const { accessKeyId, secretAccessKey } = this.awsCredentials;
        const service = 'execute-api';
        const host = new URL(url).host;
        const path = new URL(url).pathname;
        const query = new URL(url).search;

        // Create canonical request
        const timestamp = new Date().toISOString().replace(/[:-]|\.\d{3}/g, '');
        const date = timestamp.substr(0, 8);
        const canonicalHeaders = [
            `host:${host}`,
            `x-amz-date:${timestamp}`,
            'content-type:application/json'
        ].join('\n') + '\n';

        const signedHeaders = 'host;x-amz-date;content-type';
        const payloadHash = data ? await this.sha256(JSON.stringify(data)) : 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855';

        const canonicalRequest = [
            method,
            path,
            query,
            canonicalHeaders,
            signedHeaders,
            payloadHash
        ].join('\n');

        // Create string to sign
        const algorithm = 'AWS4-HMAC-SHA256';
        const credentialScope = `${date}/${this.awsRegion}/${service}/aws4_request`;
        const stringToSign = [
            algorithm,
            timestamp,
            credentialScope,
            await this.sha256(canonicalRequest)
        ].join('\n');

        // Calculate signature
        const signature = await this.getSignatureKey(secretAccessKey, date, this.awsRegion, service, stringToSign);

        // Create authorization header
        const authorization = [
            `${algorithm} Credential=${accessKeyId}/${credentialScope}`,
            `SignedHeaders=${signedHeaders}`,
            `Signature=${signature}`
        ].join(', ');

        return {
            headers: {
                'Authorization': authorization,
                'X-Amz-Date': timestamp
            }
        };
    }

    async sha256(message) {
        const msgBuffer = new TextEncoder().encode(message);
        const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    }

    async getSignatureKey(key, dateStamp, regionName, serviceName, stringToSign) {
        const kDate = await this.hmac(`AWS4${key}`, dateStamp);
        const kRegion = await this.hmac(kDate, regionName);
        const kService = await this.hmac(kRegion, serviceName);
        const kSigning = await this.hmac(kService, 'aws4_request');
        return await this.hmac(kSigning, stringToSign);
    }

    async hmac(key, message) {
        const keyBuffer = new TextEncoder().encode(key);
        const messageBuffer = new TextEncoder().encode(message);
        const cryptoKey = await crypto.subtle.importKey(
            'raw',
            keyBuffer,
            { name: 'HMAC', hash: 'SHA-256' },
            false,
            ['sign']
        );
        const signature = await crypto.subtle.sign('HMAC', cryptoKey, messageBuffer);
        return Array.from(new Uint8Array(signature))
            .map(b => b.toString(16).padStart(2, '0'))
            .join('');
    }

    // Health and Info endpoints
    async getHealth() {
        return this.makeRequest('GET', '/health');
    }

    async getApiInfo() {
        return this.makeRequest('GET', '/');
    }

    async getStatus() {
        return this.makeRequest('GET', '/status');
    }

    // Financial Enrichment endpoint
    async enrich(content, options = {}) {
        const payload = {
            content: content,
            enrichment_types: options.enrichment_types || ['stock_data'],
            format_style: options.format_style || 'enhanced',
            include_compliance: options.include_compliance !== false,
            enable_cache: options.enable_cache !== false,
            ...options
        };
        
        return this.makeRequest('POST', '/enrich', payload);
    }

    // Enhanced Fact Check endpoint
    async factCheck(content, options = {}) {
        const payload = {
            content: content,
            use_llm: options.use_llm !== false,
            include_context: options.include_context !== false,
            confidence_threshold: options.confidence_threshold || 0.8,
            ...options
        };
        
        return this.makeRequest('POST', '/fact-check', payload);
    }

    // Compliance Analysis endpoint
    async checkCompliance(content, options = {}) {
        const payload = {
            content: content,
            check_types: options.check_types || ['investment_advice', 'guarantees', 'disclaimers'],
            ...options
        };
        
        return this.makeRequest('POST', '/compliance', payload);
    }

    // Enhancement endpoint
    async enhance(aiResponse, options = {}) {
        const payload = {
            ai_response: aiResponse,
            enhancement_types: options.enhancement_types || ['financial_data', 'compliance'],
            format_style: options.format_style || 'enhanced',
            ...options
        };
        
        return this.makeRequest('POST', '/enhance', payload);
    }

    // RAG Query endpoint
    async rag(query, options = {}) {
        const payload = {
            query: query,
            max_results: options.max_results || 10,
            include_sources: options.include_sources !== false,
            use_reranking: options.use_reranking !== false,
            ...options
        };
        
        return this.makeRequest('POST', '/rag', payload);
    }

    // Chat endpoint - Updated to use Bedrock Router Agent
    async chat(message, options = {}) {
        const payload = {
            query: message,
            conversation_id: options.conversation_id || null,
            use_function_calling: options.use_function_calling !== false,
            ...options
        };
        
        return this.makeRequest('POST', '/chat', payload);
    }

    // Bedrock Router Agent endpoint (new)
    async routeQuery(query, options = {}) {
        const payload = {
            query: query,
            ...options
        };
        
        return this.makeRequest('POST', '/route-query', payload);
    }

    // Lambda Handler Testing (for local development)
    async testLambdaHandler(handlerName, payload) {
        return this.makeRequest('POST', `/lambda/${handlerName}`, payload);
    }

    // Batch operations
    async batchEnrich(contents, options = {}) {
        const payload = {
            contents: contents,
            ...options
        };
        
        return this.makeRequest('POST', '/batch/enrich', payload);
    }

    async batchFactCheck(contents, options = {}) {
        const payload = {
            contents: contents,
            ...options
        };
        
        return this.makeRequest('POST', '/batch/fact-check', payload);
    }

    async batchCompliance(contents, options = {}) {
        const payload = {
            contents: contents,
            ...options
        };
        
        return this.makeRequest('POST', '/batch/compliance', payload);
    }

    // Utility methods for testing
    async ping() {
        const start = performance.now();
        await this.getHealth();
        const end = performance.now();
        return {
            latency: end - start,
            timestamp: new Date().toISOString()
        };
    }

    async runDiagnostics() {
        const results = {
            timestamp: new Date().toISOString(),
            baseUrl: this.baseUrl,
            tests: {}
        };

        try {
            // Health check
            const healthStart = performance.now();
            const health = await this.getHealth();
            results.tests.health = {
                status: 'pass',
                latency: performance.now() - healthStart,
                result: health
            };
        } catch (error) {
            results.tests.health = {
                status: 'fail',
                error: error.message
            };
        }

        try {
            // API info
            const infoStart = performance.now();
            const info = await this.getApiInfo();
            results.tests.info = {
                status: 'pass',
                latency: performance.now() - infoStart,
                result: info
            };
        } catch (error) {
            results.tests.info = {
                status: 'fail',
                error: error.message
            };
        }

        try {
            // Simple enrichment test
            const enrichStart = performance.now();
            const enrichResult = await this.enrich('Apple (AAPL) stock test', {
                format_style: 'basic'
            });
            results.tests.enrichment = {
                status: 'pass',
                latency: performance.now() - enrichStart,
                claims: enrichResult.claims?.length || 0
            };
        } catch (error) {
            results.tests.enrichment = {
                status: 'fail',
                error: error.message
            };
        }

        return results;
    }
}

// Export the API client
window.FinSightAPI = FinSightAPI; 