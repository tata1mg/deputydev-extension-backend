import arrow.core.*
import arrow.core.continuations.*
import kotlinx.coroutines.*
import kotlin.random.Random
import kotlin.reflect.KClass
import kotlin.reflect.full.findAnnotation
import kotlin.reflect.full.functions

// Define custom annotations (decorators)
@Target(AnnotationTarget.CLASS)
@Retention(AnnotationRetention.RUNTIME)
annotation class Service(val name: String = "")

// Sealed interface for domain errors
sealed interface DomainError {
    data class ValidationError(val reason: String) : DomainError
    data class ProcessingError(val reason: String) : DomainError
    object NotFoundError : DomainError
}

// Data class for representing user
data class User(
    val id: String,
    val name: String,
    val age: Int,
    val email: String
)

// Functional approach to user validation and processing
object UserService {
    // Validation function using Either for error handling
    fun validateUser(user: User): Either<DomainError, User> = either {
        when {
            user.name.isBlank() ->
                raise(DomainError.ValidationError("Name cannot be blank"))
            user.age < 18 ->
                raise(DomainError.ValidationError("User must be 18 or older"))
            !user.email.contains("@") ->
                raise(DomainError.ValidationError("Invalid email format"))
            else -> user
        }
    }

    // Suspend function for processing users
    suspend fun processUsers(users: List<User>): Either<DomainError, List<User>> =
        coroutineScope {
            users.map { user ->
                async { validateUser(user) }
            }.awaitAll().let { results ->
                val (errors, validUsers) = results.separate()

                if (errors.isNotEmpty()) {
                    Left(errors.first())
                } else {
                    Right(validUsers)
                }
            }
        }

    // Extension function for generating mock users
    fun generateUsers(count: Int): List<User> =
        (1..count).map { i ->
            User(
                id = "user-$i",
                name = listOf("Alice", "Bob", "Charlie", "David")[Random.nextInt(4)],
                age = Random.nextInt(16, 45),
                email = "user$i@example.com"
            )
        }
}

// High-order function demonstrating functional composition
fun <A, B, C> ((A) -> B).andThen(other: (B) -> C): (A) -> C =
    { a -> other(this(a)) }

// Main function to demonstrate functional error handling
suspend fun main() {
    val userGenerator = UserService::generateUsers
    val processUsers = UserService::processUsers

    // Function composition example
    val generateAndProcessUsers =
        userGenerator.andThen { users ->
            runBlocking { processUsers(users) }
        }

    try {
        val result = generateAndProcessUsers(50)

        result.fold(
            ifLeft = { error ->
                println("Processing failed: ${error.let {
                    when(it) {
                        is DomainError.ValidationError -> it.reason
                        is DomainError.ProcessingError -> it.reason
                        DomainError.NotFoundError -> "Not found"
                    }
                }}")
            },
            ifRight = { validUsers ->
                println("Successfully processed ${validUsers.size} users")
                validUsers.take(5).forEach(::println)
            }
        )
    } catch (e: Exception) {
        println("Unexpected error: ${e.message}")
    }
}