package com.example.functions

fun factorial(n: Int): Long {  // function_declaration
    if (n == 0) return 1
    var result = 1L
    for (i in 1..n) {
        result *= i
    }
    return result
}

fun fibonacci(n: Int): Long {
    if (n == 0) return 0
    if (n == 1) return 1
    var a = 0L
    var b = 1L
    var sum: Long
    for (i in 2..n) {
        sum = a + b
        a = b
        b = sum
    }
    return b
}

val multiply: (Int, Int) -> Int = { x, y -> x * y } // lambda_expression

fun sumOfSquares(n: Int): Long {
    var sum = 0L
    for (i in 1..n) {
        sum += i * i
    }
    return sum
}

fun main() {
    println("Factorial of 10: ${factorial(10)}")
    println("Fibonacci of 15: ${fibonacci(15)}")
    println("Multiplication using lambda: ${multiply(5, 6)}")
    println("Sum of squares up to 10: ${sumOfSquares(10)}")
}
