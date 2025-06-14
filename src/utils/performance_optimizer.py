"""
Performance Optimization Module for FinSight
Implements parallel processing, caching, and connection pooling for improved performance
Target: Reduce processing time from ~16s to <8s
"""

import asyncio
import aiohttp
import time
import json
import logging
from typing import Dict, List, Any, Optional, Callable, Tuple
from datetime import datetime, timedelta
from functools import wraps
import hashlib
import os
import boto3
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

class PerformanceOptimizer:
    """
    Central performance optimization manager
    Handles parallel processing, caching, and connection pooling
    """
    
    def __init__(self, max_concurrent: int = 10, cache_ttl: int = 300):
        self.max_concurrent = max_concurrent
        self.cache_ttl = cache_ttl
        self.cache = {}
        self.session = None
        self.lambda_client = boto3.client('lambda')
        self.s3_client = boto3.client('s3')
        self.s3_bucket = os.environ.get('S3_BUCKET', 'finsight-cache')
        
        # Performance metrics
        self.metrics = {
            'cache_hits': 0,
            'cache_misses': 0,
            'api_calls': 0,
            'parallel_tasks': 0,
            'processing_times': []
        }
    
    async def initialize_session(self):
        """Initialize optimized HTTP session with connection pooling"""
        if self.session is None:
            connector = aiohttp.TCPConnector(
                limit=100,              # Total connection pool size
                limit_per_host=20,      # Per-host connection limit
                ttl_dns_cache=300,      # DNS cache TTL (5 minutes)
                use_dns_cache=True,
                keepalive_timeout=30,   # Keep connections alive
                enable_cleanup_closed=True
            )
            
            timeout = aiohttp.ClientTimeout(
                total=30,               # Total timeout
                connect=10,             # Connection timeout
                sock_read=20            # Socket read timeout
            )
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'FinSight/2.1.0',
                    'Accept': 'application/json',
                    'Accept-Encoding': 'gzip, deflate'
                }
            )
            logger.info("Optimized HTTP session initialized")
    
    async def close_session(self):
        """Clean up HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    def cache_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get_from_cache(self, key: str) -> Optional[Any]:
        """Get item from cache if not expired"""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.cache_ttl:
                self.metrics['cache_hits'] += 1
                logger.debug(f"Cache hit for key: {key[:10]}...")
                return value
            else:
                # Remove expired item
                del self.cache[key]
        
        self.metrics['cache_misses'] += 1
        return None
    
    def set_cache(self, key: str, value: Any):
        """Set item in cache with timestamp"""
        self.cache[key] = (value, time.time())
        logger.debug(f"Cached result for key: {key[:10]}...")
    
    async def get_from_s3_cache(self, key: str) -> Optional[Dict]:
        """Get cached result from S3 for longer-term storage"""
        try:
            response = self.s3_client.get_object(
                Bucket=self.s3_bucket,
                Key=f"cache/{key}"
            )
            
            data = json.loads(response['Body'].read())
            
            # Check if cache is still valid
            cache_time = datetime.fromisoformat(data['timestamp'])
            if datetime.now() - cache_time < timedelta(seconds=self.cache_ttl):
                return data['value']
            
        except Exception as e:
            logger.debug(f"S3 cache miss for {key}: {str(e)}")
        
        return None
    
    async def set_s3_cache(self, key: str, value: Any):
        """Store result in S3 cache"""
        try:
            cache_data = {
                'value': value,
                'timestamp': datetime.now().isoformat()
            }
            
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=f"cache/{key}",
                Body=json.dumps(cache_data, default=str),
                ContentType='application/json'
            )
            logger.debug(f"Stored in S3 cache: {key[:10]}...")
            
        except Exception as e:
            logger.warning(f"Failed to store in S3 cache: {str(e)}")

    async def parallel_lambda_invoke(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute multiple Lambda functions in parallel
        Replaces sequential invocation with concurrent processing
        """
        start_time = time.time()
        self.metrics['parallel_tasks'] += len(tasks)
        
        async def invoke_single_lambda(task: Dict[str, Any]) -> Tuple[str, Any]:
            """Invoke a single Lambda function"""
            try:
                task_type = task['type']
                function_name = task['function_name']
                payload = task['payload']
                
                # Check cache first
                cache_key = self.cache_key(function_name, payload)
                cached_result = self.get_from_cache(cache_key)
                
                if cached_result:
                    return task_type, cached_result
                
                # Check S3 cache for longer-term results
                s3_cached = await self.get_from_s3_cache(cache_key)
                if s3_cached:
                    self.set_cache(cache_key, s3_cached)
                    return task_type, s3_cached
                
                # Invoke Lambda function
                response = self.lambda_client.invoke(
                    FunctionName=function_name,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(payload)
                )
                
                if response['StatusCode'] == 200:
                    result = json.loads(response['Payload'].read())
                    
                    # Cache the result
                    self.set_cache(cache_key, result)
                    await self.set_s3_cache(cache_key, result)
                    
                    return task_type, result
                else:
                    logger.error(f"Lambda {function_name} failed with status {response['StatusCode']}")
                    return task_type, {'error': f"Service unavailable"}
                    
            except Exception as e:
                logger.error(f"Error invoking {task.get('function_name', 'unknown')}: {str(e)}")
                return task['type'], {'error': str(e)}
        
        # Execute all tasks concurrently with semaphore for rate limiting
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def invoke_with_semaphore(task):
            async with semaphore:
                return await invoke_single_lambda(task)
        
        # Run tasks in parallel
        results = await asyncio.gather(
            *[invoke_with_semaphore(task) for task in tasks],
            return_exceptions=True
        )
        
        # Process results
        processed_results = {}
        for result in results:
            if isinstance(result, tuple):
                task_type, task_result = result
                processed_results[task_type] = task_result
            else:
                logger.error(f"Unexpected result type: {type(result)}")
        
        processing_time = time.time() - start_time
        self.metrics['processing_times'].append(processing_time)
        
        logger.info(f"Parallel Lambda execution completed in {processing_time:.2f}s for {len(tasks)} tasks")
        
        return processed_results

    async def parallel_api_calls(self, api_requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute multiple API calls in parallel
        Optimized for external financial data APIs
        """
        if not self.session:
            await self.initialize_session()
        
        start_time = time.time()
        self.metrics['api_calls'] += len(api_requests)
        
        async def make_api_call(request: Dict[str, Any]) -> Dict[str, Any]:
            """Make a single API call with caching"""
            try:
                url = request['url']
                method = request.get('method', 'GET')
                headers = request.get('headers', {})
                params = request.get('params', {})
                
                # Check cache
                cache_key = self.cache_key(url, method, params)
                cached_result = self.get_from_cache(cache_key)
                
                if cached_result:
                    return cached_result
                
                # Make API call
                async with self.session.request(method, url, headers=headers, params=params) as response:
                    if response.status == 200:
                        result = {
                            'success': True,
                            'data': await response.json(),
                            'url': url,
                            'status': response.status
                        }
                    else:
                        result = {
                            'success': False,
                            'error': f"HTTP {response.status}",
                            'url': url,
                            'status': response.status
                        }
                    
                    # Cache successful results
                    if result['success']:
                        self.set_cache(cache_key, result)
                    
                    return result
                    
            except Exception as e:
                logger.error(f"API call failed for {request.get('url', 'unknown')}: {str(e)}")
                return {
                    'success': False,
                    'error': str(e),
                    'url': request.get('url', 'unknown')
                }
        
        # Execute API calls with rate limiting
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def call_with_semaphore(request):
            async with semaphore:
                return await make_api_call(request)
        
        results = await asyncio.gather(
            *[call_with_semaphore(req) for req in api_requests],
            return_exceptions=True
        )
        
        processing_time = time.time() - start_time
        logger.info(f"Parallel API calls completed in {processing_time:.2f}s for {len(api_requests)} requests")
        
        return [r for r in results if not isinstance(r, Exception)]

    def parallel_cpu_tasks(self, tasks: List[Callable], max_workers: int = 4) -> List[Any]:
        """
        Execute CPU-intensive tasks in parallel using ThreadPoolExecutor
        Useful for data processing and calculations
        """
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(task) for task in tasks]
            results = []
            
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=30)  # 30 second timeout
                    results.append(result)
                except Exception as e:
                    logger.error(f"CPU task failed: {str(e)}")
                    results.append({'error': str(e)})
        
        processing_time = time.time() - start_time
        logger.info(f"Parallel CPU tasks completed in {processing_time:.2f}s for {len(tasks)} tasks")
        
        return results

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        cache_hit_rate = 0
        if (self.metrics['cache_hits'] + self.metrics['cache_misses']) > 0:
            cache_hit_rate = self.metrics['cache_hits'] / (self.metrics['cache_hits'] + self.metrics['cache_misses'])
        
        avg_processing_time = 0
        if self.metrics['processing_times']:
            avg_processing_time = sum(self.metrics['processing_times']) / len(self.metrics['processing_times'])
        
        return {
            'cache_hit_rate': cache_hit_rate,
            'cache_hits': self.metrics['cache_hits'],
            'cache_misses': self.metrics['cache_misses'],
            'api_calls_made': self.metrics['api_calls'],
            'parallel_tasks_executed': self.metrics['parallel_tasks'],
            'average_processing_time': avg_processing_time,
            'total_requests': len(self.metrics['processing_times'])
        }

    def clear_cache(self):
        """Clear in-memory cache"""
        self.cache.clear()
        logger.info("Performance cache cleared")


# Global optimizer instance
_optimizer = None

def get_optimizer() -> PerformanceOptimizer:
    """Get global optimizer instance"""
    global _optimizer
    if _optimizer is None:
        _optimizer = PerformanceOptimizer()
    return _optimizer


def async_cached(ttl: int = 300):
    """Decorator for caching async function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            optimizer = get_optimizer()
            cache_key = optimizer.cache_key(func.__name__, *args, **kwargs)
            
            # Check cache
            cached_result = optimizer.get_from_cache(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            optimizer.set_cache(cache_key, result)
            
            return result
        return wrapper
    return decorator


def sync_cached(ttl: int = 300):
    """Decorator for caching synchronous function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            optimizer = get_optimizer()
            cache_key = optimizer.cache_key(func.__name__, *args, **kwargs)
            
            # Check cache
            cached_result = optimizer.get_from_cache(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            optimizer.set_cache(cache_key, result)
            
            return result
        return wrapper
    return decorator
