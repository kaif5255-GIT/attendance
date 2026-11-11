-- ========================================================
-- Employee Attendance Management System Database Schema
-- Ready for Live Demonstration (Zero Hardcoded Dummy Records)
-- ========================================================

SET FOREIGN_KEY_CHECKS = 0;

CREATE DATABASE IF NOT EXISTS `employee_attendance_db`;
USE `employee_attendance_db`;

-- --------------------------------------------------------
-- Roles Table
-- --------------------------------------------------------
DROP TABLE IF EXISTS `roles`;
CREATE TABLE `roles` (
  `Role_Id` int NOT NULL AUTO_INCREMENT,
  `Role_Name` varchar(50) NOT NULL,
  PRIMARY KEY (`Role_Id`),
  UNIQUE KEY `Role_Name` (`Role_Name`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

INSERT INTO `roles` (`Role_Id`, `Role_Name`) VALUES 
(1, 'Admin'),
(2, 'manager'),
(3, 'employee');

-- --------------------------------------------------------
-- Users Table (Default Administrator Account Only)
-- --------------------------------------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `User_Id` int NOT NULL AUTO_INCREMENT,
  `Full_Name` varchar(100) NOT NULL,
  `Email` varchar(100) DEFAULT NULL,
  `Phone` varchar(15) DEFAULT NULL,
  `Password_hash` varchar(200) NOT NULL,
  `Role_Id` int NOT NULL,
  `Created_At` datetime NOT NULL DEFAULT (now()),
  `Is_Active` tinyint(1) NOT NULL DEFAULT '1',
  `Must_Change_Password` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`User_Id`),
  UNIQUE KEY `Email` (`Email`),
  KEY `Role_Id` (`Role_Id`),
  CONSTRAINT `users_ibfk_1` FOREIGN KEY (`Role_Id`) REFERENCES `roles` (`Role_Id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Initial Admin: admin@gmail.com | Password: Admin@12345
INSERT INTO `users` (`User_Id`, `Full_Name`, `Email`, `Phone`, `Password_hash`, `Role_Id`, `Created_At`, `Is_Active`, `Must_Change_Password`) VALUES 
(1, 'System Administrator', 'admin@gmail.com', '9999999999', 'dc7f46fe12b70ed7$daba5455e7aa17ee0122d88ac91c3abc2ea23c7c38fe3b25257e189c709a50e4', 1, (now()), 1, 0);

-- --------------------------------------------------------
-- Employees Table (Inputted Live via Web Application)
-- --------------------------------------------------------
DROP TABLE IF EXISTS `employees`;
CREATE TABLE `employees` (
  `Employee_Id` int NOT NULL,
  `Employee_Name` varchar(100) DEFAULT NULL,
  `Email` varchar(100) DEFAULT NULL,
  `Phone` varchar(15) DEFAULT NULL,
  `Department` varchar(100) DEFAULT NULL,
  `Designation` varchar(100) DEFAULT NULL,
  `User_Id` int DEFAULT NULL,
  `Manager_Id` int DEFAULT NULL,
  PRIMARY KEY (`Employee_Id`),
  UNIQUE KEY `User_Id` (`User_Id`),
  KEY `fk_employee_manager` (`Manager_Id`),
  CONSTRAINT `fk_employee_manager` FOREIGN KEY (`Manager_Id`) REFERENCES `users` (`User_Id`),
  CONSTRAINT `fk_employee_user` FOREIGN KEY (`User_Id`) REFERENCES `users` (`User_Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------
-- Attendance Table (Marked Live via Web Application)
-- --------------------------------------------------------
DROP TABLE IF EXISTS `attendance`;
CREATE TABLE `attendance` (
  `Attendance_Id` int NOT NULL AUTO_INCREMENT,
  `Employee_Id` int DEFAULT NULL,
  `Attendance_Date` date DEFAULT NULL,
  `Status` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`Attendance_Id`),
  KEY `Employee_Id` (`Employee_Id`),
  CONSTRAINT `attendance_ibfk_1` FOREIGN KEY (`Employee_Id`) REFERENCES `employees` (`Employee_Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------
-- Leave Requests Table (Applied & Reviewed Live via Web Application)
-- --------------------------------------------------------
DROP TABLE IF EXISTS `leave_requests`;
CREATE TABLE `leave_requests` (
  `Leave_Id` int NOT NULL AUTO_INCREMENT,
  `Employee_Id` int DEFAULT NULL,
  `From_Date` date DEFAULT NULL,
  `To_Date` date DEFAULT NULL,
  `Leave_Type` varchar(50) DEFAULT NULL,
  `Reason` varchar(500) DEFAULT NULL,
  `Status` varchar(50) DEFAULT 'Pending',
  `Reviewed_By` int DEFAULT NULL,
  `Reviewed_At` datetime DEFAULT NULL,
  PRIMARY KEY (`Leave_Id`),
  KEY `Employee_Id` (`Employee_Id`),
  CONSTRAINT `leave_requests_ibfk_1` FOREIGN KEY (`Employee_Id`) REFERENCES `employees` (`Employee_Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------
-- Revoked Tokens Table (Session Invalidation)
-- --------------------------------------------------------
DROP TABLE IF EXISTS `revoked_tokens`;
CREATE TABLE `revoked_tokens` (
  `RevokedToken_Id` int NOT NULL AUTO_INCREMENT,
  `Token_JTI` varchar(100) DEFAULT NULL,
  `Expires_At` datetime NOT NULL,
  `Session_Id` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`RevokedToken_Id`),
  UNIQUE KEY `ix_Revoked_Tokens_Token_JTI` (`Token_JTI`),
  KEY `ix_Revoked_Tokens_RevokedToken_Id` (`RevokedToken_Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

SET FOREIGN_KEY_CHECKS = 1;
