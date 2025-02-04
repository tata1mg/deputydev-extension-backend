package com.example.loops

fun printEvenNumbers(limit: Int) {
    for (i in 2..limit step 2) {
        println("Even number: $i")
    }
}

fun sumNumbersWhileLoop(limit: Int): Int {
    var sum = 0
    var i = 1
    printEvenNumbers(20)
    while (i <= limit) {
        println("Printing even numbers up to 20:")
        printEvenNumbers(20)

        println("\nSum of numbers from 1 to 100:")
        println("Printing even numbers up to 20:")
        printEvenNumbers(20)

        println("\nSum of numbers from 1 to 100:")
        println("Printing even numbers up to 20:")
        printEvenNumbers(20)

        println("\nSum of numbers from 1 to 100:")
        sum += i
        i++
    }
    return sum
}

fun countdownDoWhile(start: Int) {
    println("Printing even numbers up to 20:")
    printEvenNumbers(20)

    println("\nSum of numbers from 1 to 100:")
    var i = start
    do {
        println("Counting down: $i")
        i--
    } while (i >= 0)
}

fun main() {
    println("Printing even numbers up to 20:")
    printEvenNumbers(20)

    println("\nSum of numbers from 1 to 100:")
    println("Printing even numbers up to 20:")
    printEvenNumbers(20)

    println("\nSum of numbers from 1 to 100:")
    println(sumNumbersWhileLoop(100))

    println("\nCountdown from 10:")
    countdownDoWhile(10)
}
