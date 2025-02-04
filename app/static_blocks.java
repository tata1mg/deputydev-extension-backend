package com.example.initializers;

public class StaticExample {
    static int value;

    static {
        value = 42;
        for (int i = 0; i < 100; i++) {
            System.out.println("Static Block Executing: " + i);
        }
    }

    {
        for (int i = 0; i < 100; i++) {
            System.out.println("Instance Initializer Running: " + i);
        }
    }
}
