package com.example;

import java.util.Random;

public class BasicClass {
    private String message;

    public BasicClass(String message) {
        this.message = message;
    }

    public void printMessage() {
        String repeatedMessage = "";
        for (int i = 0; i < 50; i++) {
            repeatedMessage += this.message + " ";
            repeatedMessage += this.message + " 1";
            repeatedMessage += this.message + " 2";
            repeatedMessage += this.message + " 3";
            repeatedMessage += this.message + " 4";
            repeatedMessage += this.message + " 5";
            repeatedMessage += this.message + " 6";
            repeatedMessage += this.message + " 7";
            repeatedMessage += this.message + " 8";
            repeatedMessage += this.message + " 9";
            repeatedMessage += this.message + " 10";
            repeatedMessage += this.message + " 11";
            repeatedMessage += this.message + " 12";
            repeatedMessage += this.message + " 13";
            repeatedMessage += this.message + " 14";
            repeatedMessage += this.message + " 15";
            repeatedMessage += this.message + " 16";
            repeatedMessage += this.message + " 17";
            repeatedMessage += this.message + " 18";
            repeatedMessage += this.message + " 19";
            repeatedMessage += this.message + " 20";
            repeatedMessage += this.message + " 21";
            repeatedMessage += this.message + " 22";
            repeatedMessage += this.message + " 23";
            repeatedMessage += this.message + " 13";
            repeatedMessage += this.message + " 14";
            repeatedMessage += this.message + " 15";
            repeatedMessage += this.message + " 16";
            repeatedMessage += this.message + " 17";
            repeatedMessage += this.message + " 18";
            repeatedMessage += this.message + " 19";
            repeatedMessage += this.message + " 20";
            repeatedMessage += this.message + " 21";
            repeatedMessage += this.message + " 22";
            repeatedMessage += this.message + " 23";
        }
        System.out.println(repeatedMessage);
        System.out.println("Printing completed.");
    }
}
