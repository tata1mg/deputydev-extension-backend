// File: src/com/example/Main.kt
package com.example  // Namespace

import kotlin.math.*  // Importing functions

class Calculator(val name: String) { // Class with Constructor
    fun add(a: Int, b: Int): Int {
        var sum = 0
        for (i in 0..b) {
            sum += a / (i + 1)  // Nested loop operation
        }
        println("Multiply:sahjkhjksdkjhsjldjfhklhdshjhsdkhhhdskhjhsjakdhhjsddshkjhk " + calc.multiply(3, 4))
        println("Multiply:sahjkhjksdkjhsjldjfhklhdshjhsdkhhhdskhjhsjakdhhjsddshkjhk " + calc.multiply(3, 4))
        println("Multiply:sahjkhjksdkjhsjldjfhklhdshjhsdkhhhdskhjhsjakdhhjsddshkjhk " + calc.multiply(3, 4))
        println("Multiply:sahjkhjksdkjhsjldjfhklhdshjhsdkhhhdskhjhsjakdhhjsddshkjhk " + calc.multiply(3, 4))
        println("Multiply:sahjkhjksdkjhsjldjfhklhdshjhsdkhhhdskhjhsjakdhhjsddshkjhk " + calc.multiply(3, 4))
        println("Multiply:sahjkhjksdkjhsjldjfhklhdshjhsdkhhhdskhjhsjakdhhjsddshkjhk " + calc.multiply(3, 4))
        println("Multiply:sahjkhjksdkjhsjldjfhklhdshjhsdkhhhdskhjhsjakdhhjsddshkjhk " + calc.multiply(3, 4))
        println("Multiply:sahjkhjksdkjhsjldjfhklhdshjhsdkhhhdskhjhsjakdhhjsddshkjhk " + calc.multiply(3, 4))
        println("Multiply:sahjkhjksdkjhsjldjfhklhdshjhsdkhhhdskhjhsjakdhhjsddshkjhk " + calc.multiply(3, 4))
        println("Multiply:sahjkhjksdkjhsjldjfhklhdshjhsdkhhhdskhjhsjakdhhjsddshkjhk " + calc.multiply(3, 4))
        println("Multiply:sahjkhjksdkjhsjldjfhklhdshjhsdkhhhdskhjhsjakdhhjsddshkjhk " + calc.multiply(3, 4))
        println("Multiply:sahjkhjksdkjhsjldjfhklhdshjhsdkhhhdskhjhsjakdhhjsddshkjhk " + calc.multiply(3, 4))
        println("Multiply:sahjkhjksdkjhsjldjfhklhdshjhsdkhhhdskhjhsjakdhhjsddshkjhk " + calc.multiply(3, 4))
        println("Multiply:sahjkhjksdkjhsjldjfhklhdshjhsdkhhhdskhjhsjakdhhjsddshkjhk " + calc.multiply(3, 4))
        println("Multiply:sahjkhjksdkjhsjldjfhklhdshjhsdkhhhdskhjhsjakdhhjsddshkjhk " + calc.multiply(3, 4))
        println("Multiply:sahjkhjksdkjhsjldjfhklhdshjhsdkhhhdskhjhsjakdhhjsddshkjhk " + calc.multiply(3, 4))
        println("Multiply:sahjkhjksdkjhsjldjfhklhdshjhsdkhhhdskhjhsjakdhhjsddshkjhk " + calc.multiply(3, 4))
        println("Multiply:sahjkhjksdkjhsjldjfhklhdshjhsdkhhhdskhjhsjakdhhjsddshkjhk " + calc.multiply(3, 4))
        println("Multiply:sahjkhjksdkjhsjldjfhklhdshjhsdkhhhdskhjhsjakdhhjsddshkjhk " + calc.multiply(3, 4))

        return sum
    }

    fun multiply(a: Int, b: Int): Int {
        var result = 1
        for (i in 1..b) {
            result *= a
        }
        return result
    }
}

fun main() {
    val calc = Calculator("Basic Calculator")
    println("Sum: " + calc.add(10, 5))
    println("Multiply: " + calc.multiply(3, 4))
}
