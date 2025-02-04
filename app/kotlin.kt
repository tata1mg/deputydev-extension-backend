// File: DummyKotlinFile.kt
package com.example.project // Namespace example
import kotlin.math.PI // Import statement

@Deprecated("Use newFunction() instead") // Decorator (Annotation)
fun oldFunction() {
    println("This function is deprecated.")
}

// Class Definition
class MyClass {
    // Constructor
    constructor(name: String) {
        println("Constructor: $name")
    }

    // Function Definition
    fun greet(name: String): String {
        return "Hello, $name!"
    }

    // Nested Class
    class NestedClass {
        fun sayHi() {
            println("Hi from NestedClass!")
        }
    }
}

// Enum Class
enum class Days {
    MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY
}

// Expression Statement
fun main() {
    val instance = MyClass("Test")
    println(instance.greet("Kotlin"))
    println(Days.MONDAY)
}
