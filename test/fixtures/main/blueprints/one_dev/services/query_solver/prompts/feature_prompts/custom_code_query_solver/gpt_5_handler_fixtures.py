from typing import Any, Dict, List

from app.backend_common.models.dto.message_thread_dto import (
    ContentBlockCategory,
    MessageData,
    TextBlockContent,
    TextBlockData,
)


class Gpt5CustomHandlerFixtures:
    """Fixture data for GPT-5 Custom Code Query Solver Handler tests."""

    @staticmethod
    def get_sample_params() -> Dict[str, Any]:
        """Get sample parameters for custom handler initialization."""
        return {
            "query": "Create a custom REST API with advanced features",
            "files": [
                {
                    "path": "src/api/base.py",
                    "content": "# Base API configuration\nfrom fastapi import FastAPI\n\napp = FastAPI()",
                },
            ],
            "custom_requirements": {
                "authentication": "JWT with refresh tokens",
                "authorization": "RBAC (Role-Based Access Control)",
                "caching": "Redis with intelligent cache invalidation",
                "monitoring": "Prometheus metrics + structured logging",
                "testing": "100% code coverage with integration tests",
            },
            "technical_constraints": {
                "framework": "FastAPI",
                "database": "PostgreSQL with async SQLAlchemy",
                "deployment": "Docker + Kubernetes",
                "performance": "< 100ms response time",
                "security": "OWASP compliance",
            },
            "custom_instructions": [
                "Follow clean architecture principles",
                "Implement comprehensive error handling",
                "Use dependency injection pattern",
                "Include API versioning strategy",
                "Add comprehensive documentation",
            ],
        }

    @staticmethod
    def get_sample_message_data() -> List[MessageData]:
        """Get sample message data for testing custom response parsing."""
        return [
            TextBlockData(
                type=ContentBlockCategory.TEXT_BLOCK,
                content=TextBlockContent(
                    text="I'll help you create a custom REST API with advanced features. Let me design a comprehensive solution."
                ),
            ),
            TextBlockData(
                type=ContentBlockCategory.TEXT_BLOCK,
                content=TextBlockContent(
                    text="""<thinking>
The user wants a custom REST API with advanced features. I need to consider:

1. **Architecture Design**:
   - Clean Architecture with proper layer separation
   - Domain-driven design principles
   - SOLID principles implementation

2. **Security Implementation**:
   - JWT authentication with refresh token mechanism
   - RBAC for fine-grained authorization
   - Input validation and sanitization
   - Rate limiting and DDoS protection

3. **Performance Optimization**:
   - Redis caching with intelligent invalidation
   - Database query optimization
   - Connection pooling
   - Async/await patterns for I/O operations

4. **Monitoring and Observability**:
   - Prometheus metrics for monitoring
   - Structured logging with correlation IDs
   - Health check endpoints
   - Distributed tracing

5. **Testing Strategy**:
   - Unit tests with high code coverage
   - Integration tests for API endpoints
   - Load testing for performance validation
   - Security testing for vulnerability assessment

I'll create a modular, scalable solution that follows best practices.
</thinking>

<code_block>
<programming_language>python</programming_language>
<file_path>src/main.py</file_path>
<is_diff>false</is_diff>
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import uvicorn
from prometheus_fastapi_instrumentator import Instrumentator

from src.core.config import settings
from src.core.logging import setup_logging
from src.core.database import database
from src.core.cache import redis_client
from src.api.v1 import api_router
from src.core.middleware import (
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware
)


@asynccontextmanager
    async def lifespan(app: FastAPI):
        \\\"\\\"\\\"Application lifespan events.\\\"\\\"\\\"
    # Startup
    setup_logging()
    await database.connect()
    await redis_client.connect()
    
    yield
    
    # Shutdown
    await database.disconnect()
    await redis_client.disconnect()


    def create_application() -> FastAPI:
        \\\"\\\"\\\"Create and configure FastAPI application.\\\"\\\"\\\"
    app = FastAPI(
        title="Custom REST API",
        description="Advanced REST API with comprehensive features",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    )

    # Security middleware
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Custom middleware
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)
    
    # Prometheus metrics
    if settings.ENABLE_METRICS:
        Instrumentator().instrument(app).expose(app)
    
    # Include API routes
    app.include_router(api_router, prefix="/api/v1")
    
    return app


app = create_application()


@app.get("/health")
    async def health_check():
        \\\"\\\"\\\"Health check endpoint.\\\"\\\"\\\"
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }


@app.get("/metrics")
    async def custom_metrics():
        \\\"\\\"\\\"Custom application metrics.\\\"\\\"\\\"
    return {
        "database_connections": await database.get_connection_count(),
        "cache_connections": await redis_client.get_connection_count(),
        "active_sessions": await redis_client.get_session_count()
    }


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=settings.WORKERS if not settings.DEBUG else 1
    )
</code_block>

<code_block>
<programming_language>python</programming_language>
<file_path>src/core/auth.py</file_path>
<is_diff>false</is_diff>
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.core.config import settings
from src.core.cache import redis_client
from src.models.user import User, UserRole
from src.schemas.auth import TokenResponse, RefreshTokenRequest


class AuthService:
    \\\"\\\"\\\"Advanced authentication service with JWT and refresh tokens.\\\"\\\"\\\"
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.security = HTTPBearer()
        self.algorithm = "HS256"
        self.access_token_expire = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        self.refresh_token_expire = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
        def hash_password(self, password: str) -> str:
            \\\"\\\"\\\"Hash password using bcrypt.\\\"\\\"\\\"
            return self.pwd_context.hash(password)
    
        def verify_password(self, plain_password: str, hashed_password: str) -> bool:
            \\\"\\\"\\\"Verify password against hash.\\\"\\\"\\\"
            return self.pwd_context.verify(plain_password, hashed_password)
    
        def create_access_token(self, user_id: int, roles: List[str], permissions: List[str]) -> str:
            \\\"\\\"\\\"Create JWT access token with user information and permissions.\\\"\\\"\\\"
        now = datetime.utcnow()
        expire = now + self.access_token_expire
        
        payload = {
            "sub": str(user_id),
            "type": "access",
            "iat": now,
            "exp": expire,
            "roles": roles,
            "permissions": permissions,
            "jti": f"access_{user_id}_{int(now.timestamp())}"
        }
        
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=self.algorithm)
    
        def create_refresh_token(self, user_id: int) -> str:
            \\\"\\\"\\\"Create JWT refresh token.\\\"\\\"\\\"
        now = datetime.utcnow()
        expire = now + self.refresh_token_expire
        
        payload = {
            "sub": str(user_id),
            "type": "refresh",
            "iat": now,
            "exp": expire,
            "jti": f"refresh_{user_id}_{int(now.timestamp())}"
        }
        
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=self.algorithm)
    
        async def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
            \\\"\\\"\\\"Verify JWT token and return payload.\\\"\\\"\\\"
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[self.algorithm])
            
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type. Expected: {token_type}"
                )
            
            # Check if token is blacklisted
            jti = payload.get("jti")
            if await redis_client.is_token_blacklisted(jti):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been invalidated"
                )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
        async def blacklist_token(self, token: str) -> None:
            \\\"\\\"\\\"Add token to blacklist.\\\"\\\"\\\"
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[self.algorithm],
                options={"verify_exp": False}
            )
            jti = payload.get("jti")
            exp = payload.get("exp")
            
            if jti and exp:
                ttl = exp - int(datetime.utcnow().timestamp())
                if ttl > 0:
                    await redis_client.blacklist_token(jti, ttl)
        except jwt.JWTError:
            pass  # Invalid tokens don't need to be blacklisted
    
    async def get_current_user(
        self, 
        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
        ) -> User:
            \\\"\\\"\\\"Get current authenticated user.\\\"\\\"\\\"
        payload = await self.verify_token(credentials.credentials)
        user_id = int(payload["sub"])
        
        # Get user from database with caching
        user = await User.get_by_id_cached(user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        return user
    
        def require_permissions(self, required_permissions: List[str]):
            \\\"\\\"\\\"Dependency to require specific permissions.\\\"\\\"\\\"
        async def permission_checker(current_user: User = Depends(self.get_current_user)):
            user_permissions = await current_user.get_permissions()
            
            if not all(perm in user_permissions for perm in required_permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            return current_user
        
        return permission_checker
    
        def require_roles(self, required_roles: List[str]):
            \\\"\\\"\\\"Dependency to require specific roles.\\\"\\\"\\\"
        async def role_checker(current_user: User = Depends(self.get_current_user)):
            user_roles = [role.name for role in current_user.roles]
            
            if not any(role in user_roles for role in required_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient role privileges"
                )
            
            return current_user
        
        return role_checker


# Global auth service instance
auth_service = AuthService()


# Convenience dependencies
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
    ) -> User:
        \\\"\\\"\\\"Get current authenticated user - convenience function.\\\"\\\"\\\"
        return await auth_service.get_current_user(credentials)
    
    
    def require_admin():
        \\\"\\\"\\\"Require admin role.\\\"\\\"\\\"
        return auth_service.require_roles(["admin"])
    
    
    def require_permissions(*permissions: str):
        \\\"\\\"\\\"Require specific permissions.\\\"\\\"\\\"
        return auth_service.require_permissions(list(permissions))
</code_block>

<summary>
I've created a comprehensive custom REST API with advanced features including:

**Core Architecture:**
- Clean FastAPI application structure with proper lifespan management
- Modular design with separation of concerns
- Configuration management with environment-specific settings

**Advanced Authentication & Authorization:**
- JWT tokens with access and refresh token mechanism
- Role-Based Access Control (RBAC) with fine-grained permissions
- Token blacklisting for secure logout
- Password hashing with bcrypt
- Comprehensive security middleware

**Security Features:**
- Security headers middleware
- CORS configuration
- Trusted host middleware
- Rate limiting middleware
- Input validation and sanitization

**Performance & Monitoring:**
- Redis caching for user data and sessions
- Prometheus metrics integration
- Custom application metrics endpoint
- Request logging with correlation IDs
- Database connection pooling

**Key Features:**
1. **Scalable Architecture**: Clean separation with dependency injection
2. **Security First**: Multiple layers of security controls
3. **Observability**: Comprehensive logging and metrics
4. **Performance**: Caching and async operations
5. **Flexibility**: Role and permission-based access control

The implementation follows OWASP security guidelines and includes proper error handling, health checks, and monitoring capabilities for production deployment.
</summary>"""
                ),
            ),
        ]

    @staticmethod
    def get_query_type_examples() -> List[Dict[str, Any]]:
        """Get different types of custom query examples."""
        return [
            # Algorithm implementation query
            {
                "query": "Implement a custom sorting algorithm optimized for nearly sorted data",
                "algorithm_type": "hybrid_sort",
                "performance_requirements": {
                    "time_complexity": "O(n) best case, O(n log n) worst case",
                    "space_complexity": "O(1) auxiliary space",
                    "optimize_for": "nearly_sorted_data",
                },
                "custom_features": [
                    "Adaptive behavior based on input characteristics",
                    "Fallback to quicksort for random data",
                    "Insertion sort for small subarrays",
                ],
            },
            # Data structure design query
            {
                "query": "Design a custom cache with intelligent eviction policies",
                "data_structure": "hybrid_cache",
                "features": {
                    "eviction_policies": ["LRU", "LFU", "TTL-based"],
                    "adaptive_policy_selection": True,
                    "memory_efficiency": "high",
                    "thread_safety": True,
                },
                "performance_goals": {"hit_ratio": "> 85%", "latency": "< 1ms average", "memory_overhead": "< 20%"},
            },
            # System architecture query
            {
                "query": "Create a custom event-driven microservices architecture",
                "architecture_style": "event_sourcing + CQRS",
                "components": ["Event Store", "Command Handlers", "Query Handlers", "Event Bus", "Projection Handlers"],
                "quality_attributes": {
                    "scalability": "horizontal",
                    "consistency": "eventual",
                    "availability": "99.9%",
                    "fault_tolerance": "high",
                },
            },
            # Machine learning pipeline query
            {
                "query": "Build a custom ML pipeline for real-time recommendation system",
                "ml_components": {
                    "feature_engineering": "real_time_streaming",
                    "model_serving": "ensemble_approach",
                    "feedback_loop": "online_learning",
                    "personalization": "context_aware",
                },
                "technical_requirements": {
                    "latency": "< 50ms",
                    "throughput": "> 10000 RPS",
                    "model_update_frequency": "hourly",
                    "a_b_testing": "integrated",
                },
            },
            # Security framework query
            {
                "query": "Implement a custom security framework with advanced threat detection",
                "security_features": {
                    "authentication": "multi_factor",
                    "authorization": "attribute_based",
                    "threat_detection": "ml_powered",
                    "incident_response": "automated",
                },
                "compliance": ["SOC2", "GDPR", "HIPAA"],
                "threat_models": ["OWASP Top 10", "STRIDE methodology", "Custom threat intelligence"],
            },
        ]

    @staticmethod
    def get_complex_scenarios() -> List[Dict[str, Any]]:
        """Get complex custom query scenarios."""
        return [
            # Multi-tenant SaaS platform
            {
                "query": "Build a multi-tenant SaaS platform with custom domain support",
                "tenant_isolation": "schema_per_tenant",
                "custom_domains": {
                    "ssl_management": "automated",
                    "dns_configuration": "api_driven",
                    "subdomain_routing": "dynamic",
                },
                "billing_integration": {
                    "usage_metering": "real_time",
                    "pricing_models": ["freemium", "usage_based", "tiered"],
                    "payment_processing": "stripe_integration",
                },
                "customization": {
                    "white_labeling": True,
                    "custom_themes": True,
                    "api_extensions": "plugin_architecture",
                },
            },
            # IoT data processing platform
            {
                "query": "Create an IoT data processing platform with edge computing support",
                "data_ingestion": {
                    "protocols": ["MQTT", "CoAP", "HTTP", "WebSocket"],
                    "throughput": "1M messages/second",
                    "edge_processing": "intelligent_filtering",
                },
                "stream_processing": {
                    "engine": "Apache Kafka + Flink",
                    "windowing": "custom_time_windows",
                    "anomaly_detection": "ml_based",
                },
                "device_management": {
                    "provisioning": "zero_touch",
                    "ota_updates": "delta_updates",
                    "fleet_management": "hierarchical",
                },
            },
            # Distributed game engine
            {
                "query": "Develop a distributed game engine for massively multiplayer games",
                "networking": {
                    "architecture": "hybrid_p2p_server",
                    "latency_compensation": "client_side_prediction",
                    "anti_cheat": "server_authoritative",
                },
                "scalability": {
                    "world_partitioning": "spatial_hashing",
                    "load_balancing": "interest_management",
                    "horizontal_scaling": "microservices",
                },
                "performance": {"target_fps": 60, "network_latency": "< 100ms", "concurrent_players": "10000+"},
            },
        ]

    @staticmethod
    def get_custom_block_examples() -> List[str]:
        """Get custom block examples for testing parsing."""
        return [
            """<thinking>
This is a custom implementation request that requires careful planning:

1. **Requirements Analysis**:
   - Custom sorting algorithm for nearly sorted data
   - Need adaptive behavior based on input characteristics
   - Performance optimization for specific use cases

2. **Algorithm Design**:
   - Hybrid approach combining multiple sorting techniques
   - Adaptive selection based on data characteristics
   - Fallback mechanisms for edge cases

3. **Implementation Strategy**:
   - Start with insertion sort for small arrays
   - Use merge sort for partially sorted data
   - Fallback to quicksort for random data
   - Implement adaptive threshold selection
</thinking>

<code_block>
<programming_language>python</programming_language>
<file_path>src/algorithms/adaptive_sort.py</file_path>
<is_diff>false</is_diff>
def adaptive_sort(arr, threshold_small=10, threshold_sorted=0.8):
    \"\"\"
    Adaptive sorting algorithm optimized for nearly sorted data.
    \"\"\"
    if len(arr) <= threshold_small:
        return insertion_sort(arr)
    
    sorted_ratio = calculate_sorted_ratio(arr)
    
    if sorted_ratio >= threshold_sorted:
        return merge_sort_optimized(arr)
    else:
        return quicksort(arr)
</code_block>

<summary>
I've implemented an adaptive sorting algorithm that:
- Analyzes input characteristics to choose optimal strategy
- Uses insertion sort for small arrays (< 10 elements)
- Uses optimized merge sort for nearly sorted data (> 80% sorted)
- Falls back to quicksort for random data
- Achieves O(n) performance for nearly sorted inputs
</summary>""",
            """<custom_instruction>
Focus on creating a production-ready implementation with:
- Comprehensive error handling
- Detailed logging and monitoring
- Security best practices
- Performance optimization
- Extensive test coverage
</custom_instruction>

<architecture_diagram>
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   API Gateway   │    │   Auth Service  │
│                 │────▶│                 │────▶│                 │
│   (Nginx/HAProxy)│    │   (Kong/Zuul)   │    │   (JWT + RBAC)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Microservice 1│    │   Microservice 2│    │   Microservice N│
│                 │    │                 │    │                 │
│   (User Mgmt)   │    │   (Orders)      │    │   (Notifications)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
</architecture_diagram>

<performance_requirements>
- Response time: < 100ms for 95% of requests
- Throughput: > 1000 RPS per service instance
- Availability: 99.9% uptime
- Scalability: Horizontal auto-scaling
- Security: Zero-trust architecture
</performance_requirements>""",
            """<implementation_phases>
Phase 1: Core Infrastructure
- Set up containerized services
- Implement basic authentication
- Create database schemas
- Set up monitoring and logging

Phase 2: Business Logic
- Implement domain services
- Add API endpoints
- Create data validation layers
- Implement caching strategies

Phase 3: Advanced Features
- Add real-time notifications
- Implement advanced security
- Add performance optimizations
- Create comprehensive test suites

Phase 4: Production Readiness
- Load testing and optimization
- Security penetration testing
- Documentation and runbooks
- Deployment automation
</implementation_phases>

<technology_stack>
Backend: FastAPI, SQLAlchemy, PostgreSQL
Cache: Redis with intelligent invalidation
Queue: Celery with Redis broker
Monitoring: Prometheus + Grafana
Logging: ELK Stack (Elasticsearch, Logstash, Kibana)
Deployment: Docker + Kubernetes
CI/CD: GitHub Actions + ArgoCD
</technology_stack>""",
        ]

    @staticmethod
    def get_code_block_examples() -> List[str]:
        """Get code block examples for testing extraction."""
        return [
            """<code_block>
<programming_language>python</programming_language>
<file_path>src/custom/algorithm.py</file_path>
<is_diff>false</is_diff>
class CustomHashTable:
    \"\"\"
    Custom hash table implementation with dynamic resizing
    and collision handling using open addressing with quadratic probing.
    \"\"\"
    
    def __init__(self, initial_capacity=16, load_factor_threshold=0.75):
        self.capacity = initial_capacity
        self.size = 0
        self.load_factor_threshold = load_factor_threshold
        self.buckets = [None] * self.capacity
        self.deleted_marker = object()
    
    def _hash(self, key):
        \"\"\"Custom hash function using FNV-1a algorithm.\"\"\"
        hash_value = 2166136261  # FNV offset basis
        for byte in str(key).encode('utf-8'):
            hash_value ^= byte
            hash_value *= 16777619  # FNV prime
        return hash_value % self.capacity
    
    def _find_slot(self, key):
        \"\"\"Find slot for key using quadratic probing.\"\"\"
        index = self._hash(key)
        original_index = index
        i = 0
        
        while self.buckets[index] is not None:
            if (self.buckets[index] != self.deleted_marker and 
                self.buckets[index][0] == key):
                return index, True  # Found existing key
            
            i += 1
            index = (original_index + i * i) % self.capacity
            
            if index == original_index:  # Full cycle
                break
        
        return index, False  # Found empty slot
    
    def put(self, key, value):
        \"\"\"Insert or update key-value pair.\"\"\"
        if self.size >= self.capacity * self.load_factor_threshold:
            self._resize()
        
        index, found = self._find_slot(key)
        
        if not found:
            self.size += 1
        
        self.buckets[index] = (key, value)
    
    def get(self, key):
        \"\"\"Retrieve value by key.\"\"\"
        index, found = self._find_slot(key)
        
        if found:
            return self.buckets[index][1]
        
        raise KeyError(f"Key '{key}' not found")
    
    def delete(self, key):
        \"\"\"Delete key-value pair.\"\"\"
        index, found = self._find_slot(key)
        
        if found:
            self.buckets[index] = self.deleted_marker
            self.size -= 1
        else:
            raise KeyError(f"Key '{key}' not found")
    
    def _resize(self):
        \"\"\"Resize hash table when load factor exceeds threshold.\"\"\"
        old_buckets = self.buckets
        self.capacity *= 2
        self.size = 0
        self.buckets = [None] * self.capacity
        
        for item in old_buckets:
            if item is not None and item != self.deleted_marker:
                key, value = item
                self.put(key, value)
</code_block>""",
            """<code_block>
<programming_language>rust</programming_language>
<file_path>src/custom_allocator.rs</file_path>
<is_diff>false</is_diff>
use std::alloc::{GlobalAlloc, Layout};
use std::ptr;
use std::sync::atomic::{AtomicUsize, Ordering};

/// Custom memory allocator with tracking and optimization for specific patterns
pub struct CustomAllocator {
    allocated_bytes: AtomicUsize,
    allocation_count: AtomicUsize,
    peak_memory: AtomicUsize,
}

impl CustomAllocator {
    pub const fn new() -> Self {
        Self {
            allocated_bytes: AtomicUsize::new(0),
            allocation_count: AtomicUsize::new(0),
            peak_memory: AtomicUsize::new(0),
        }
    }
    
    pub fn get_stats(&self) -> AllocatorStats {
        AllocatorStats {
            current_allocated: self.allocated_bytes.load(Ordering::Relaxed),
            total_allocations: self.allocation_count.load(Ordering::Relaxed),
            peak_memory: self.peak_memory.load(Ordering::Relaxed),
        }
    }
    
    fn update_peak_memory(&self, current: usize) {
        let mut peak = self.peak_memory.load(Ordering::Relaxed);
        while current > peak {
            match self.peak_memory.compare_exchange_weak(
                peak, 
                current, 
                Ordering::Relaxed, 
                Ordering::Relaxed
            ) {
                Ok(_) => break,
                Err(x) => peak = x,
            }
        }
    }
}

unsafe impl GlobalAlloc for CustomAllocator {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        let ptr = std::alloc::System.alloc(layout);
        
        if !ptr.is_null() {
            let size = layout.size();
            self.allocated_bytes.fetch_add(size, Ordering::Relaxed);
            self.allocation_count.fetch_add(1, Ordering::Relaxed);
            
            let current = self.allocated_bytes.load(Ordering::Relaxed);
            self.update_peak_memory(current);
        }
        
        ptr
    }
    
    unsafe fn dealloc(&self, ptr: *mut u8, layout: Layout) {
        std::alloc::System.dealloc(ptr, layout);
        self.allocated_bytes.fetch_sub(layout.size(), Ordering::Relaxed);
    }
}

#[derive(Debug, Clone, Copy)]
pub struct AllocatorStats {
    pub current_allocated: usize,
    pub total_allocations: usize,
    pub peak_memory: usize,
}

#[global_allocator]
static ALLOCATOR: CustomAllocator = CustomAllocator::new();
</code_block>""",
            """<code_block>
<programming_language>go</programming_language>
<file_path>pkg/custom/ratelimiter.go</file_path>
<is_diff>false</is_diff>
package custom

import (
    "context"
    "sync"
    "time"
)

// CustomRateLimiter implements a token bucket algorithm with burst capacity
// and adaptive rate adjustment based on system load
type CustomRateLimiter struct {
    mu           sync.RWMutex
    tokens       float64
    capacity     float64
    refillRate   float64
    lastRefill   time.Time
    burstTokens  float64
    adaptiveMode bool
    systemLoad   *SystemLoadMonitor
}

// NewCustomRateLimiter creates a new adaptive rate limiter
func NewCustomRateLimiter(rate float64, capacity float64, burstCapacity float64) *CustomRateLimiter {
    return &CustomRateLimiter{
        tokens:       capacity,
        capacity:     capacity,
        refillRate:   rate,
        lastRefill:   time.Now(),
        burstTokens:  burstCapacity,
        adaptiveMode: true,
        systemLoad:   NewSystemLoadMonitor(),
    }
}

// Allow checks if a request should be allowed based on current token availability
func (rl *CustomRateLimiter) Allow() bool {
    return rl.AllowN(1)
}

// AllowN checks if N requests should be allowed
func (rl *CustomRateLimiter) AllowN(n int) bool {
    rl.mu.Lock()
    defer rl.mu.Unlock()
    
    rl.refillTokens()
    
    if rl.adaptiveMode {
        rl.adjustRateBasedOnLoad()
    }
    
    tokensNeeded := float64(n)
    
    // Check if we have enough regular tokens
    if rl.tokens >= tokensNeeded {
        rl.tokens -= tokensNeeded
        return true
    }
    
    // Check if we can use burst tokens
    totalAvailable := rl.tokens + rl.burstTokens
    if totalAvailable >= tokensNeeded {
        burstUsed := tokensNeeded - rl.tokens
        rl.tokens = 0
        rl.burstTokens -= burstUsed
        return true
    }
    
    return false
}

// Wait blocks until the request can be processed or context is cancelled
func (rl *CustomRateLimiter) Wait(ctx context.Context) error {
    return rl.WaitN(ctx, 1)
}

// WaitN blocks until N requests can be processed
func (rl *CustomRateLimiter) WaitN(ctx context.Context, n int) error {
    for {
        if rl.AllowN(n) {
            return nil
        }
        
        select {
        case <-ctx.Done():
            return ctx.Err()
        case <-time.After(time.Millisecond * 10):
            continue
        }
    }
}

// refillTokens adds tokens based on elapsed time
func (rl *CustomRateLimiter) refillTokens() {
    now := time.Now()
    elapsed := now.Sub(rl.lastRefill).Seconds()
    rl.lastRefill = now
    
    tokensToAdd := elapsed * rl.refillRate
    rl.tokens = min(rl.capacity, rl.tokens+tokensToAdd)
    
    // Refill burst tokens gradually
    if rl.burstTokens < rl.capacity*0.5 {
        burstRefill := elapsed * rl.refillRate * 0.1
        rl.burstTokens = min(rl.capacity*0.5, rl.burstTokens+burstRefill)
    }
}

// adjustRateBasedOnLoad adapts the rate based on system load
func (rl *CustomRateLimiter) adjustRateBasedOnLoad() {
    load := rl.systemLoad.GetCurrentLoad()
    
    switch {
    case load < 0.3:
        // Low load - increase rate by 10%
        rl.refillRate = min(rl.refillRate*1.1, rl.capacity*2)
    case load > 0.8:
        // High load - decrease rate by 20%
        rl.refillRate = max(rl.refillRate*0.8, rl.capacity*0.1)
    }
}

func min(a, b float64) float64 {
    if a < b {
        return a
    }
    return b
}

func max(a, b float64) float64 {
    if a > b {
        return a
    }
    return b
}
</code_block>""",
        ]

    @staticmethod
    def get_malformed_examples() -> List[str]:
        """Get malformed examples for error handling tests."""
        return [
            "",  # Empty string
            "<thinking>Incomplete thinking block without closing",
            "<code_block>\n<programming_language>python</programming_language>\n# Missing closing tags and metadata",
            "Plain text without any structured blocks",
            "<custom_block>Unknown block type</custom_block>",
            "<thinking></thinking>",  # Empty thinking
            "<code_block></code_block>",  # Empty code block
            """<code_block>
<programming_language></programming_language>
<file_path></file_path>
<is_diff>invalid</is_diff>
print("malformed metadata")
</code_block>""",  # Invalid metadata
            "<thinking>Nested <thinking>blocks</thinking> are invalid</thinking>",
            "< >Malformed XML syntax< >",
        ]

    @staticmethod
    def get_large_input_example() -> Dict[str, Any]:
        """Get large input example for performance testing."""
        return {
            "query": "Create a comprehensive enterprise application with microservices architecture",
            "description": "Build a complete enterprise solution with all modern features and best practices. " * 50,
            "requirements": {
                "functional": [f"Requirement {i}: " + "Detailed requirement description. " * 20 for i in range(50)],
                "non_functional": [
                    f"Performance requirement {i}: " + "Detailed performance specification. " * 15 for i in range(30)
                ],
                "security": [
                    f"Security requirement {i}: " + "Detailed security specification. " * 10 for i in range(20)
                ],
            },
            "technical_constraints": {
                "frameworks": ["FastAPI", "React", "PostgreSQL", "Redis", "Kubernetes"],
                "languages": ["Python", "TypeScript", "SQL", "YAML"],
                "patterns": ["CQRS", "Event Sourcing", "Microservices", "Clean Architecture"],
                "deployment": "Cloud-native with auto-scaling and disaster recovery",
            },
            "files": [
                {
                    "path": f"src/services/service_{i}/main.py",
                    "content": f"# Service {i} implementation\n" + "# Detailed implementation code\n" * 100,
                }
                for i in range(20)
            ],
            "documentation": {
                "api_specs": "Comprehensive API documentation with examples. " * 100,
                "architecture_docs": "Detailed architecture documentation with diagrams. " * 100,
                "deployment_guide": "Step-by-step deployment instructions. " * 100,
            },
        }
