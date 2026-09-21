CREATE DATABASE IF NOT EXISTS `systemface attendance`;
USE `systemface attendance`;

CREATE TABLE IF NOT EXISTS register (
 fname VARCHAR(50), lname VARCHAR(50), contact VARCHAR(20),
 email VARCHAR(100) PRIMARY KEY, securityQ VARCHAR(100),
 securityA VARCHAR(100), password VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS student (
 Dep VARCHAR(50), Course VARCHAR(50), Year VARCHAR(30), Sem VARCHAR(30),
 ID VARCHAR(50) PRIMARY KEY, Name VARCHAR(100), Div VARCHAR(20),
 `Roll No` VARCHAR(30), Gender VARCHAR(20), DOB VARCHAR(30),
 Email VARCHAR(100), `Phone No` VARCHAR(30), Address VARCHAR(255),
 Teacher VARCHAR(100), `Photo Sample` VARCHAR(10)
);
