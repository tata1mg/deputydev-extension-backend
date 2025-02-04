package com.example.interfaces;

interface Vehicle {
    void drive();
}

class Car implements Vehicle {
    @Override
    public void drive() {
        StringBuilder driveLog = new StringBuilder();
        for (int i = 0; i < 50; i++) {
            driveLog.append("Driving iteration: ").append(i).append("\n");
        }
        System.out.println(driveLog.toString());
    }
}

public class InterfaceTest {
    public static void main(String[] args) {
        Vehicle myCar = new Car();
        myCar.drive();
    }
}
