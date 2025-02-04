package com.example.annotations;


@interface CustomAnnotation {
    String value();
}

public class AnnotationExample {
    @Deprecated
    public void oldMethod() {
        for (int i = 0; i < 100; i++) {
            System.out.println("Deprecated method call #" + i);
        }
    }

    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < 50; i++) {
            sb.append("Overridden toString message. ");
        }
        return sb.toString();
    }

    @CustomAnnotation(value = "Test")
    public void annotatedMethod() {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < 75; i++) {
            sb.append("Annotated method processing... ");
        }
        System.out.println(sb.toString());
    }
}
