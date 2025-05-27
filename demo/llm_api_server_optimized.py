#!/usr/bin/env python3
"""
Optimized LLM-Enhanced API Server for FinSight
High-performance version with parallel processing and caching
Target: <8s response time (vs original ~16s)
"""

import asyncio
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import optimized components
try:
    from src.utils.performance_optimizer import get_optimizer, PerformanceOptimizer
    from src.handlers.enhance_handler_optimized import process_enhancement_async, calculate_optimized_quality_score
    from src.handlers.enhanced_fact_check_handler_optimized import OptimizedFinancialFactChecker
    from src.utils.llm_claim_extractor import LLMClaimExtractor
    from src.utils.enhanced_ticker_resolver import EnhancedTickerResolver
except ImportError as e:
    logging.error(f"Failed to import optimized components: {e}")
    # Fallback imports would go here
    raise

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="FinSight Optimized API",
    description="High-performance financial fact-checking API with LLM enhancement",
    version="2.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global optimizer instance
optimizer: PerformanceOptimizer = None

# Performance metrics
performance_stats = {
    'requests_processed': 0,
    'total_processing_time': 0,
    'cache_hits': 0,
    'cache_misses': 0,
    'parallel_tasks_executed': 0,
    'average_response_time': 0,
    'uptime_start': datetime.now()
}

class FinancialContent(BaseModel):
    content: str
    enable_fact_checking: bool = True
    enable_context_enrichment: bool = True
    enable_compliance_check: bool = True
    enrichment_level: str = "standard"  # basic, standard, comprehensive
    use_llm: bool = True

class EnhancementResponse(BaseModel):
    original_content: str
    enhanced_content: str
    fact_checks: List[Dict[str, Any]]
    context_additions: List[Dict[str, Any]]
    compliance_flags: List[str]
    quality_score: float
    processing_time_ms: float
    ai_evaluation: Optional[Dict[str, Any]]
    performance_metrics: Dict[str, Any]
    optimization_enabled: bool = True

@app.on_event("startup")
async def startup_event():
    """Initialize optimized components on startup"""
    global optimizer
    
    logger.info("🚀 Starting FinSight Optimized API Server...")
    
    # Initialize performance optimizer
    optimizer = get_optimizer()
    await optimizer.initialize_session()
    
    # Warm up components
    logger.info("🔥 Warming up components...")
    
    # Initialize LLM extractor
    try:
        llm_extractor = LLMClaimExtractor()
        logger.info("✅ LLM claim extractor initialized")
    except Exception as e:
        logger.warning(f"⚠️  LLM extractor initialization failed: {e}")
    
    # Initialize ticker resolver
    try:
        ticker_resolver = EnhancedTickerResolver()
        logger.info("✅ Enhanced ticker resolver initialized")
    except Exception as e:
        logger.warning(f"⚠️  Ticker resolver initialization failed: {e}")
    
    logger.info("✅ FinSight Optimized API Server ready!")
    logger.info("🎯 Target: <8s response time with enhanced accuracy")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    global optimizer
    
    logger.info("🛑 Shutting down FinSight Optimized API Server...")
    
    if optimizer:
        await optimizer.close_session()
        
        # Log final performance stats
        final_stats = optimizer.get_performance_metrics()
        logger.info(f"📊 Final Performance Stats: {final_stats}")
    
    logger.info("✅ Shutdown complete")

@app.post("/enhance", response_model=EnhancementResponse)
async def enhance_content_optimized(content: FinancialContent, background_tasks: BackgroundTasks):
    """
    Enhanced financial content processing with optimizations
    """
    request_start = time.time()
    request_id = f"req_{int(time.time() * 1000)}"
    
    logger.info(f"🔄 Processing optimized request {request_id}")
    logger.info(f"📝 Content length: {len(content.content)} chars")
    logger.info(f"⚙️  Settings: LLM={content.use_llm}, Facts={content.enable_fact_checking}, Context={content.enable_context_enrichment}")
    
    try:
        # Process enhancement using optimized pipeline
        result = await process_enhancement_async(
            content=content.content,
            request_id=request_id,
            fact_check=content.enable_fact_checking,
            add_context=content.enable_context_enrichment,
            enrichment_level=content.enrichment_level
        )
        
        processing_time = (time.time() - request_start) * 1000
        
        # Update performance stats
        performance_stats['requests_processed'] += 1
        performance_stats['total_processing_time'] += processing_time
        performance_stats['average_response_time'] = (
            performance_stats['total_processing_time'] / performance_stats['requests_processed']
        )
        
        # Get optimizer metrics
        optimizer_metrics = optimizer.get_performance_metrics()
        
        # Combine performance metrics
        combined_metrics = {
            **optimizer_metrics,
            'request_id': request_id,
            'server_processing_time_ms': processing_time,
            'requests_processed': performance_stats['requests_processed'],
            'average_response_time_ms': performance_stats['average_response_time']
        }
        
        # Create response
        response = EnhancementResponse(
            original_content=result['original_content'],
            enhanced_content=result['enhanced_content'],
            fact_checks=result['fact_checks'],
            context_additions=result['context_additions'],
            compliance_flags=result['compliance_flags'],
            quality_score=result['quality_score'],
            processing_time_ms=processing_time,
            ai_evaluation=result.get('ai_evaluation'),
            performance_metrics=combined_metrics,
            optimization_enabled=True
        )
        
        # Log success with performance metrics
        logger.info(f"✅ Request {request_id} completed in {processing_time:.1f}ms")
        logger.info(f"📊 Cache hit rate: {optimizer_metrics.get('cache_hit_rate', 0):.1%}")
        logger.info(f"🎯 Quality score: {result['quality_score']:.1%}")
        
        # Schedule background analytics
        background_tasks.add_task(log_analytics, request_id, processing_time, result)
        
        return response
        
    except Exception as e:
        processing_time = (time.time() - request_start) * 1000
        logger.error(f"❌ Request {request_id} failed after {processing_time:.1f}ms: {str(e)}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Enhancement processing failed: {str(e)}"
        )

@app.post("/fact-check-only")
async def fact_check_only_optimized(content: FinancialContent):
    """
    Optimized fact-checking only endpoint for faster processing
    """
    request_start = time.time()
    request_id = f"fact_{int(time.time() * 1000)}"
    
    logger.info(f"🔍 Processing fact-check-only request {request_id}")
    
    try:
        # Initialize optimized fact checker
        fact_checker = OptimizedFinancialFactChecker(use_llm=content.use_llm)
        
        # Process claims asynchronously
        result = await fact_checker.process_claims_async(content.content, request_id)
        
        processing_time = (time.time() - request_start) * 1000
        
        result.update({
            'processing_time_ms': processing_time,
            'optimization_enabled': True
        })
        
        logger.info(f"✅ Fact-check {request_id} completed in {processing_time:.1f}ms")
        logger.info(f"📋 Claims processed: {result.get('claims_processed', 0)}")
        
        return result
        
    except Exception as e:
        processing_time = (time.time() - request_start) * 1000
        logger.error(f"❌ Fact-check {request_id} failed after {processing_time:.1f}ms: {str(e)}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Fact-checking failed: {str(e)}"
        )

@app.get("/performance-stats")
async def get_performance_stats():
    """
    Get current performance statistics
    """
    optimizer_metrics = optimizer.get_performance_metrics() if optimizer else {}
    
    uptime = datetime.now() - performance_stats['uptime_start']
    
    stats = {
        **performance_stats,
        **optimizer_metrics,
        'uptime_seconds': uptime.total_seconds(),
        'uptime_human': str(uptime),
        'target_achievement': {
            'target_response_time_ms': 8000,
            'current_avg_response_time_ms': performance_stats['average_response_time'],
            'target_achieved': performance_stats['average_response_time'] < 8000,
            'improvement_needed_ms': max(0, performance_stats['average_response_time'] - 8000)
        }
    }
    
    return stats

@app.post("/benchmark")
async def run_performance_benchmark():
    """
    Run a performance benchmark test
    """
    logger.info("🧪 Running performance benchmark...")
    
    test_claims = [
        "Apple stock is trading at $175.50 per share",
        "Microsoft reported quarterly revenue of $62.9 billion",
        "Tesla has a market capitalization of $780 billion"
    ]
    
    results = []
    total_start = time.time()
    
    for i, claim in enumerate(test_claims):
        start_time = time.time()
        
        try:
            content = FinancialContent(content=claim)
            response = await enhance_content_optimized(content, BackgroundTasks())
            
            processing_time = (time.time() - start_time) * 1000
            
            results.append({
                'test_id': i + 1,
                'claim': claim,
                'processing_time_ms': processing_time,
                'quality_score': response.quality_score,
                'fact_checks_count': len(response.fact_checks),
                'success': True
            })
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            results.append({
                'test_id': i + 1,
                'claim': claim,
                'processing_time_ms': processing_time,
                'error': str(e),
                'success': False
            })
    
    total_time = (time.time() - total_start) * 1000
    
    # Calculate benchmark stats
    successful_tests = [r for r in results if r['success']]
    processing_times = [r['processing_time_ms'] for r in successful_tests]
    
    benchmark_results = {
        'total_tests': len(test_claims),
        'successful_tests': len(successful_tests),
        'total_benchmark_time_ms': total_time,
        'individual_results': results,
        'performance_summary': {
            'avg_processing_time_ms': sum(processing_times) / len(processing_times) if processing_times else 0,
            'min_processing_time_ms': min(processing_times) if processing_times else 0,
            'max_processing_time_ms': max(processing_times) if processing_times else 0,
            'target_achieved': all(t < 8000 for t in processing_times),
            'success_rate': len(successful_tests) / len(test_claims)
        }
    }
    
    logger.info(f"🏁 Benchmark completed: {benchmark_results['performance_summary']}")
    
    return benchmark_results

@app.get("/cache-stats")
async def get_cache_stats():
    """
    Get detailed cache performance statistics
    """
    if not optimizer:
        return {"error": "Optimizer not initialized"}
    
    metrics = optimizer.get_performance_metrics()
    
    cache_stats = {
        'cache_hit_rate': metrics.get('cache_hit_rate', 0),
        'cache_hits': metrics.get('cache_hits', 0),
        'cache_misses': metrics.get('cache_misses', 0),
        'total_cache_requests': metrics.get('cache_hits', 0) + metrics.get('cache_misses', 0),
        'cache_effectiveness': 'High' if metrics.get('cache_hit_rate', 0) > 0.7 else 'Medium' if metrics.get('cache_hit_rate', 0) > 0.4 else 'Low'
    }
    
    return cache_stats

@app.post("/clear-cache")
async def clear_cache():
    """
    Clear performance cache (admin endpoint)
    """
    if optimizer:
        optimizer.clear_cache()
        logger.info("🧹 Performance cache cleared")
        return {"message": "Cache cleared successfully"}
    else:
        raise HTTPException(status_code=500, detail="Optimizer not available")

async def log_analytics(request_id: str, processing_time: float, result: Dict[str, Any]):
    """
    Background task for logging analytics
    """
    try:
        analytics = {
            'request_id': request_id,
            'timestamp': datetime.now().isoformat(),
            'processing_time_ms': processing_time,
            'content_length': len(result.get('original_content', '')),
            'fact_checks_count': len(result.get('fact_checks', [])),
            'context_additions_count': len(result.get('context_additions', [])),
            'compliance_flags_count': len(result.get('compliance_flags', [])),
            'quality_score': result.get('quality_score', 0),
            'optimization_enabled': True
        }
        
        logger.debug(f"📈 Analytics logged for {request_id}")
        
    except Exception as e:
        logger.error(f"❌ Analytics logging failed for {request_id}: {str(e)}")

@app.get("/")
async def root():
    """
    API root endpoint with status information
    """
    uptime = datetime.now() - performance_stats['uptime_start']
    
    return {
        "service": "FinSight Optimized API",
        "version": "2.1.0",
        "status": "operational",
        "optimization_enabled": True,
        "target_performance": "<8s response time",
        "uptime": str(uptime),
        "requests_processed": performance_stats['requests_processed'],
        "average_response_time_ms": performance_stats['average_response_time'],
        "endpoints": {
            "enhance": "POST /enhance - Full content enhancement",
            "fact_check": "POST /fact-check-only - Fast fact-checking",
            "benchmark": "POST /benchmark - Performance testing",
            "stats": "GET /performance-stats - Performance metrics",
            "cache": "GET /cache-stats - Cache statistics"
        }
    }

def main():
    """
    Run the optimized API server
    """
    logger.info("🚀 Starting FinSight Optimized API Server...")
    logger.info("🎯 Performance Target: <8s response time")
    logger.info("⚡ Features: Parallel Processing, Caching, Connection Pooling")
    
    uvicorn.run(
        "llm_api_server_optimized:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable reload for production performance
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()
