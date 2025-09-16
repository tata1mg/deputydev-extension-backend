"""Fixture data for base thinking parser tests."""
from typing import List


class BaseThinkingParserFixtures:
    """Fixture data for base thinking parser tests."""

    @staticmethod
    def get_simple_thinking_examples() -> List[str]:
        """Get simple thinking examples for basic testing."""
        return [
            "This is a simple thought process.",
            "Let me analyze this step by step.",
            "I need to consider the user requirements carefully.",
            "The solution should be efficient and maintainable."
        ]

    @staticmethod
    def get_complex_thinking_examples() -> List[str]:
        """Get complex thinking examples with detailed reasoning."""
        return [
            """The user is asking for a comprehensive solution to implement authentication in their web application. I need to consider several aspects:

1. Security best practices
2. User experience considerations
3. Database design implications
4. API endpoint structure
5. Maintenance and future updates

Let me start with the security aspects first, then move to implementation details.""",

            """This is a complex architectural decision. I need to weigh the pros and cons of different approaches:

Microservices approach:
- Pros: Better scalability, technology diversity, fault isolation
- Cons: Increased complexity, network overhead, distributed system challenges

Monolithic approach:
- Pros: Simpler deployment, easier debugging, better performance for small scale
- Cons: Scaling challenges, technology lock-in, deployment coupling

Given the requirements, I think a hybrid approach might be best.""",

            """The user's code has several potential issues that I need to address:

1. Memory leaks in the event listeners
2. Race conditions in asynchronous operations
3. Inefficient database queries
4. Missing error handling for edge cases
5. Security vulnerabilities in user input handling

I'll provide solutions for each of these issues with code examples and explanations."""
        ]

    @staticmethod
    def get_structured_thinking_examples() -> List[str]:
        """Get thinking examples with structured formatting."""
        return [
            """My approach to this problem:

1. First, I'll analyze the requirements
   - What does the user want to achieve?
   - What are the constraints?
   - What are the performance requirements?

2. Then I'll design the solution
   - Architecture overview
   - Component breakdown
   - Data flow design

3. Finally, I'll implement it
   - Core logic
   - Error handling
   - Testing strategy""",

            """Breaking down this algorithm:

Step 1: Input validation
  • Check for null/undefined values
  • Validate data types
  • Ensure ranges are correct

Step 2: Data processing
  • Transform input data
  • Apply business logic
  • Handle edge cases

Step 3: Output formatting
  • Format results according to specification
  • Add metadata if needed
  • Prepare for serialization""",

            """Analysis framework:

A) Problem Definition
   -> What exactly needs to be solved?
   -> What are the success criteria?
   -> What are the limitations?

B) Solution Design
   -> What approach should we take?
   -> What tools and technologies to use?
   -> How to break down the work?
   -> What are the dependencies?
   -> How to validate the solution?"""
        ]

    @staticmethod
    def get_thinking_with_code_examples() -> List[str]:
        """Get thinking examples that include code snippets."""
        return [
            """I need to implement a retry mechanism. Here's my thinking:

The basic structure should be:
```python
def retry_operation(func, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
```

But I also need to consider:
- Which exceptions should trigger a retry
- How to make the delay configurable
- Whether to add jitter to prevent thundering herd
- Logging for debugging purposes""",

            """The user's current code has an issue:

```javascript
function processData(data) {
    return data.map(item => {
        // This will throw if item is null/undefined
        return item.value * 2;
    });
}
```

The problem is that it doesn't handle null/undefined items. Here's a better approach:

```javascript
function processData(data) {
    if (!Array.isArray(data)) {
        throw new Error('Data must be an array');
    }
    
    return data
        .filter(item => item && typeof item.value === 'number')
        .map(item => item.value * 2);
}
```"""
        ]

    @staticmethod
    def get_multilingual_examples() -> List[str]:
        """Get thinking examples with multilingual content."""
        return [
            """Le utilisateur demande une solution pour gerer l'authentification. Je dois considerer les aspects suivants:

1. Securite - utiliser des tokens JWT
2. Experience utilisateur - login simple
3. Conformite RGPD - protection des donnees

I'll implement this with a focus on security and user experience.""",

            """El usuario esta pidiendo ayuda con un sistema de autenticacion. Necesito pensar en:

- Seguridad: usar HTTPS, tokens seguros
- Usabilidad: interfaz intuitiva
- Mantenimiento: codigo limpio y documentado

I'll provide a solution that covers all these aspects."""
        ]

    @staticmethod
    def get_special_characters_examples() -> List[str]:
        """Get thinking examples with special characters and symbols."""
        return [
            """Mathematical thinking: Let me calculate the complexity.

For algorithm A: O(n²) where n is input size
For algorithm B: O(n log n)

Let's define:
- Input processing = O(n)
- Core algorithm = varies
- Output formatting = O(1)

So: final result = process(core(input)) where process has O(n log n) complexity.""",

            """Code symbols and operators:

&& (logical AND)
|| (logical OR)
! (negation)
== vs === (equality comparison)

Important considerations:
- Triple equals (===) vs double equals (==)
- Truthiness: 0, "", null, undefined are falsy
- Type coercion issues""",

            """Special formatting characters:

Tabs: \\t
Newlines: \\n
Quotes: \\" and \\'
Backslashes: \\\\
HTML entities: &lt; &gt; &amp; &quot; &#39;

All these need proper handling in the parser.""",

            """Database query with special characters:

SELECT * FROM users
WHERE name LIKE '%O\\'Connor%'
AND email NOT LIKE '%@temp.com'

Need to handle:
- SQL injection prevention
- Proper escaping of quotes
- International characters (UTF-8)
- Special regex metacharacters: . * + ? ^ $ { } [ ] | ( ) \\"""
        ]

    @staticmethod
    def get_large_thinking_content() -> str:
        """Get large thinking content for performance testing."""
        return """This is a comprehensive analysis of the software architecture problem presented. I need to consider multiple dimensions and provide a thorough solution.

First, let me analyze the current system architecture. The existing monolithic application has served well for the initial product development phase, but as the user base grows and feature requirements become more complex, we are encountering several limitations:

1. Scalability Issues:
   - The entire application must be scaled as a unit, even if only specific components experience high load
   - Database bottlenecks occur when multiple features compete for the same resources
   - Memory usage grows linearly with user sessions, creating resource constraints

2. Development Complexity:
   - Large codebase becomes difficult to navigate and understand for new team members
   - Feature development cycles are slowed by the need to understand the entire system
   - Testing becomes more complex as changes in one area can affect seemingly unrelated features
   - Deployment risks increase as any change requires deploying the entire application

3. Technology Limitations:
   - Stuck with initial technology choices, making it difficult to adopt new tools or frameworks
   - Performance optimizations are global rather than component-specific
   - Different components have different performance characteristics and optimization needs

Now, considering the migration to a microservices architecture, I need to evaluate the benefits and challenges:

Benefits of Microservices:
- Independent scaling of individual services based on their specific load patterns
- Technology diversity allowing teams to choose the best tools for each service
- Fault isolation where failure in one service does not bring down the entire system
- Independent deployment cycles enabling faster feature delivery
- Team autonomy with clear service boundaries and ownership
- Better alignment with business capabilities and domain-driven design principles

Challenges and Considerations:
- Increased operational complexity with multiple services to deploy, monitor, and maintain
- Network latency and reliability concerns when services communicate over HTTP/gRPC
- Data consistency challenges when transactions span multiple services
- Service discovery and load balancing requirements
- Distributed debugging and monitoring complexity
- Initial development overhead for setting up the microservices infrastructure

Technical Implementation Strategy:

Service Decomposition:
- Start with identifying clear bounded contexts within the current monolith
- Extract services that have well-defined interfaces and minimal cross-dependencies
- Begin with read-heavy services that are easier to extract and scale independently
- Gradually move towards more complex services that involve write operations

Communication Patterns:
- Use asynchronous messaging for event-driven communication where possible
- Implement synchronous APIs only when immediate consistency is required
- Consider saga patterns for distributed transactions
- Implement circuit breaker patterns to handle service failures gracefully

Data Management:
- Follow the database-per-service pattern to maintain data independence
- Implement event sourcing for audit trails and complex business processes
- Use eventual consistency patterns where strict consistency is not required
- Consider CQRS (Command Query Responsibility Segregation) for complex read/write scenarios

Infrastructure and DevOps:
- Containerization with Docker for consistent deployment environments
- Kubernetes for orchestration, scaling, and service discovery
- Implement comprehensive monitoring and logging across all services
- Set up automated testing pipelines for each service
- Use Infrastructure as Code for reproducible environments
- Consider service mesh technologies like Istio for traffic management

This migration will require significant investment in tooling, monitoring, and team training. However, the long-term benefits in terms of scalability, maintainability, and development velocity make it a worthwhile investment for a growing application."""

    @staticmethod
    def get_edge_case_examples() -> List[str]:
        """Get edge case examples for robust testing."""
        return [
            "",  # Empty string
            " ",  # Single space
            "\\n",  # Single newline
            "Multiple\\n\\nNewlines\\n\\n\\n",  # Multiple newlines
            "Very long thinking content that exceeds normal limits and tests the parser's ability to handle large inputs without crashing or causing performance issues in the system",
            "Mixed content with <tags> and special characters !@#$%^&*()_+{}|:<>?[]\\;'\".,/~`",
        ]

    @staticmethod
    def get_realistic_thinking_scenarios() -> List[str]:
        """Get realistic thinking scenarios that might occur in actual usage."""
        return [
            """The user is asking about implementing caching in their application. Let me think through the different caching strategies:

1. Client-side caching (browser cache, localStorage)
   - Pros: Reduces server load, improves perceived performance
   - Cons: Limited control, can become stale

2. CDN caching (CloudFlare, AWS CloudFront)
   - Pros: Global distribution, handles static assets well
   - Cons: Cost, complexity for dynamic content

For their specific use case with frequently changing data, I think a combination of Redis for session data and application-level caching would work best.""",

            """Looking at this React performance issue, I need to identify the root cause:

The component is re-rendering unnecessarily on every state change in the parent. This could be due to:
1. Props being recreated on each render (objects, arrays, functions)
2. Missing memoization with React.memo
3. Inefficient use of useEffect dependencies
4. Context value changes triggering all consumers

I should suggest using React DevTools profiler to identify the exact cause, then provide specific optimizations like useMemo, useCallback, and proper memoization strategies.""",

            """This SQL query performance problem requires careful analysis:

The query is doing a full table scan because:
1. Missing indexes on the WHERE clause columns
2. Using functions in WHERE conditions that prevent index usage
3. LIKE patterns starting with wildcards
4. OR conditions that prevent efficient index usage

Solutions would include:
- Adding appropriate indexes
- Rewriting the query to avoid functions in WHERE clause
- Using full-text search for LIKE patterns
- Considering query restructuring with UNION for OR conditions"""
        ]