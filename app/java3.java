import java.lang.annotation.*;
import javax.validation.constraints.*;
import java.util.List;
import java.util.concurrent.TimeUnit;

// Custom annotations for demonstration
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
@interface Metric {
    String name();
    String[] tags() default {};
}

@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
@interface RateLimit {
    int requests();
    TimeUnit timeUnit();
}

// Example class with annotated methods
public class AnnotatedMethodExamples {

    // Single annotation
    @Override
    public String toString() {
        return "AnnotatedMethodExamples[]";
    }

    // Multiple annotations with parameters
    @Deprecated(since = "2.0")
    @SuppressWarnings("unchecked")
    public void legacyMethod() {
        // Method implementation
    }

    // Custom annotation with parameters
    @Metric(name = "user.creation", tags = {"service=user", "type=write"})
    @RateLimit(requests = 100, timeUnit = TimeUnit.MINUTES)
    public void createUser(@NotNull String username, @Email String email) {
        // Method implementation
    }

    // Annotation with async and security
    @Async
    @Secured("ROLE_ADMIN")
    @Transactional(readOnly = true)
    public List<User> fetchUsers() {
        // Method implementation
        return null;
    }

    // Test-related annotations
    @Test
    @DisplayName("Should create user successfully")
    @Timeout(value = 5, unit = TimeUnit.SECONDS)
    public void testUserCreation() {
        // Test implementation
    }

    // Spring-style annotations
    @GetMapping("/api/users/{id}")
    @ResponseStatus(HttpStatus.OK)
    @Operation(summary = "Get user by ID")
    public ResponseEntity<User> getUser(
        @PathVariable @NotNull Long id,
        @RequestHeader(required = false) String apiKey
    ) {
        // Method implementation
        return null;
    }

    // Annotation with default interface method
    @FunctionalInterface
    interface UserProcessor {
        @Nullable
        @LogExecutionTime
        default User processUser(User user) {
            return user;
        }
    }

    // Annotation with generics and throws
    @SuppressWarnings("unchecked")
    @Retryable(
        value = {ServiceException.class},
        maxAttempts = 3,
        backoff = @Backoff(delay = 1000)
    )
    public <T extends User> T saveUser(T user) throws ServiceException {
        // Method implementation
        return null;
    }

    // Composite annotations
    @Idempotent
    @Cacheable(value = "users", key = "#id")
    @Monitored(
        metricName = "user.fetch",
        tags = {"type=read", "source=cache"}
    )
    public Optional<User> getUserById(
        @Valid @NotNull Long id
    ) {
        // Method implementation
        return Optional.empty();
    }
}