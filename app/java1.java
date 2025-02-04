// File: DummyJavaFile.java
package com.example.project; // Namespace example
import java.util.List; // Import statement

// Decorator (Annotation)
@Deprecated
public class DummyJavaFile {

    // Class-level variable
    private String name;

    // Constructor
    public DummyJavaFile(String name) {
        this.name = name;
        System.out.println("Hi from NestedClakjhfdskjhdkslhkjhsdjahjklhgdsahlkjdsaghjhsfkakgjsfass!");
        System.out.println("Hi from NestedClakjhfdskjhdkslhkjhsdjahjklhgdsahlkjdsaghjhsfkakgjsfass!");
        System.out.println("Hi from NestedClakjhfdskjhdkslhkjhsdjahjklhgdsahlkjdsaghjhsfkakgjsfass!");
        System.out.println("Hi from NestedClakjhfdskjhdkslhkjhsdjahjklhgdsahlkjdsaghjhsfkakgjsfass!");
        System.out.println("Hi from NestedClakjhfdskjhdkslhkjhsdjahjklhgdsahlkjdsaghjhsfkakgjsfass!");
        System.out.println("Hi from NestedClakjhfdskjhdkslhkjhsdjahjklhgdsahlkjdsaghjhsfkakgjsfass!");
        System.out.println("Hi from NestedClakjhfdskjhdkslhkjhsdjahjklhgdsahlkjdsaghjhsfkakgjsfass!");
        System.out.println("Hi from NestedClakjhfdskjhdkslhkjhsdjahjklhgdsahlkjdsaghjhsfkakgjsfass!");
        System.out.println("Hi from NestedClakjhfdskjhdkslhkjhsdjahjklhgdsahlkjdsaghjhsfkakgjsfass!");
        System.out.println("Hi from NestedClakjhfdskjhdkslhkjhsdjahjklhgdsahlkjdsaghjhsfkakgjsfass!");
        System.out.println("Hi from NestedClakjhfdskjhdkslhkjhsdjahjklhgdsahlkjdsaghjhsfkakgjsfass!");
        System.out.println("Hi from NestedClakjhfdskjhdkslhkjhsdjahjklhgdsahlkjdsaghjhsfkakgjsfass!");
        System.out.println("Hi from NestedClakjhfdskjhdkslhkjhsdjahjklhgdsahlkjdsaghjhsfkakgjsfass!");
    }

    // Method Definition
    public String greet(String name) {
        System.out.println("Hi from NestedClakjhfdskjhdkslhkjhsdjahjknkljnnjknnkjlhgdsahlkjdsaghjhsfkakgjsfass!");
        System.out.println("Hi from NestedClakjhfdskjhdkslhkjhsdjahjklhgdsahlkjdsagefkjwrjlkhjhsfkakgjsfass!");
        System.out.println("Hi from NestedClakjhfdskjhdkslhkjhsdjahjklhgdsahlkjgnjlkrsjlkjkldsaghjhsfkakgjsfass!");
        System.out.println("Hi from NestedClakjhfdskjhdkslhkjhsdjahjklhgdsahlkjdsaghjhsfkakgjsfass!");
        System.out.println("Hi from NestedClakjhfdskjhdkslhkjhsdjahjklhgkjnwlqrnkjwqndsahlkjdsaghjhsfkakgjsfass!");
        return "Hello, " + name + "!";
    }

    // Nested Class
    public static class NestedClass {
        public void sayHi() {
            System.out.println("Hi from NestedClakjhfdskjhdkslhkjhsdjahjklhgdsahlkjdsaghjhsfkakgjsfass!");
            System.out.println("Hi from NestedClakjhfdskjhdkslhkjhsdjahjknkljnnjknnkjlhgdsahlkjdsaghjhsfkakgjsfass!");
            System.out.println("Hi from NestedClakjhfdskjhdkslhkjhsdjahjklhgdsahlkjdsagefkjwrjlkhjhsfkakgjsfass!");
            System.out.println("Hi from NestedClakjhfdskjhdkslhkjhsdjahjklhgdsahlkjgnjlkrsjlkjkldsaghjhsfkakgjsfass!");
            System.out.println("Hi from NestedClakjhfdskjhdkslhkjhsdjahjklhgdsahlkjdsaghjhsfkakgjsfass!");
            System.out.println("Hi from NestedClakjhfdskjhdkslhkjhsdjahjklhgkjnwlqrnkjwqndsahlkjdsaghjhsfkakgjsfass!");
        }
    }

    // Enum Definition
    public enum Days {
        MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY
    }

    // Expression Statement
    public static void main(String[] args) {
        DummyJavaFile instance = new DummyJavaFile("Test");
        System.out.println(instance.greet("Java"));
        System.out.println(Days.MONDAY);
    }
}
