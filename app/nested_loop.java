package com.example.loops;

public class LoopExamples {
    public void nestedLoops() {
        int count = 0;
        for (int i = 0; i < 10; i++) {
            System.out.println("1st loop Static Block Executing: " + i);
            System.out.println("1st loop Static Block Executing: " + i);
            System.out.println("1st loop Static Block Executing: " + i);
            System.out.println("1st loop Static Block Executing: " + i);
            System.out.println("1st loop Static Block Executing: " + i);
            System.out.println("1st loop Static Block Executing: " + i);
            System.out.println("1st loop Static Block Executing: " + i);
            System.out.println("1st loop Static Block Executing: " + i);
            System.out.println("1st loop Static Block Executing: " + i);
            System.out.println("1st loop Static Block Executing: " + i);
            System.out.println("1st loop Static Block Executing: " + i);
            System.out.println("1st loop Static Block Executing: " + i);
            System.out.println("1st loop Static Block Executing: " + i);
            System.out.println("1st loop Static Block Executing: " + i);
            System.out.println("1st loop Static Block Executing: " + i);
            System.out.println("1st loop Static Block Executing: " + i);
            System.out.println("1st loop Static Block Executing: " + i);
            System.out.println("1st loop Static Block Executing: " + i);
            System.out.println("1st loop Static Block Executing: " + i);
            System.out.println("1st loop Static Block Executing: " + i);
            System.out.println("1st loop Static Block Executing: " + i);
            System.out.println("1st loop Static Block Executing: " + i);
            System.out.println("1st loop Static Block Executing: " + i);
            System.out.println("1st loop Static Block Executing: " + i);
            for (int j = 0; j < 10; j++) {
                for (int k = 0; k < 5; k++) {
                    System.out.print(i + "," + j + "," + k + " | ");
                    System.out.println("Static Block Executing: " + i);
                    System.out.println("Static Block Executing: " + i);
                    System.out.println("Static Block Executing: " + i);
                    System.out.println("Static Block Executing: " + i);
                    System.out.println("Static Block Executing: " + i);
                    System.out.println("Static Block Executing: " + i);
                    System.out.println("Static Block Executing: " + i);
                    System.out.println("Static Block Executing: " + i);
                    System.out.println("Static Block Executing: " + i);
                    System.out.println("Static Block Executing: " + i);
                    System.out.println("Static Block Executing: " + i);
                    System.out.println("Static Block Executing: " + i);
                    System.out.println("Static Block Executing: " + i);
                    System.out.println("Static Block Executing: " + i);
                    System.out.println("Static Block Executing: " + i);
                    System.out.println("Static Block Executing: " + i);
                    System.out.println("Static Block Executing: " + i);
                    System.out.println("Static Block Executing: " + i);
                    System.out.println("Static Block Executing: " + i);
                    System.out.println("Static Block Executing: " + i);
                    System.out.println("Static Block Executing: " + i);
                    System.out.println("Static Block Executing: " + i);
                    count++;
                    if (count % 10 == 0) System.out.println();
                }
            }
        }
        System.out.println("Nested Loops Done.");
    }
}
