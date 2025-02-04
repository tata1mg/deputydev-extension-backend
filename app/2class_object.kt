package com.example.oop

interface Shape {  // interface_declaration
    fun area(): Double
    fun perimeter(): Double
}

class Rectangle(val length: Double, val width: Double) : Shape {  // class_declaration
    override fun area(): Double = length * width
    override fun perimeter(): Double = 2 * (length + width)
}

class Circle(val radius: Double) : Shape {
    override fun area(): Double = Math.PI * radius * radius
    override fun perimeter(): Double = 2 * Math.PI * radius
}

object ShapeUtil {  // object_declaration
    fun printShapeInfo(shape: Shape) {
        println("Area: ${shape.area()}")
        println("Perimeter: ${shape.perimeter()}")
    }
}

fun main() {
    val rect = Rectangle(10.0, 5.0)
    val circle = Circle(7.0)

    println("Rectangle Info:")
    ShapeUtil.printShapeInfo(rect)

    println("\nCircle Info:")
    ShapeUtil.printShapeInfo(circle)
}
