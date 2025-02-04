package com.example.nested;

public class OuterClass {
    private String outerMessage = "Hello from Outer";

    static class StaticNestedClass {
        void display() {
            StringBuilder sb = new StringBuilder();
            for (int i = 0; i < 100; i++) {
                sb.append("Static Nested Loop Iteration: ").append(i).append("\n");
            }
            System.out.println(sb.toString());
        }
    }

    class InnerClass {
        void display() {
            StringBuilder sb = new StringBuilder();
            for (int i = 0; i < 100; i++) {
                sb.append("Inner Loop Iteration: ").append(i).append("\n");
            }
            System.out.println(sb.toString());
        }
    }
}
