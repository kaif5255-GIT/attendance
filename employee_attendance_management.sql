-- ========================================================
-- Employee Attendance Management System Database Schema
-- Ready for Live Demonstration (Zero Hardcoded Dummy Records)
-- ========================================================

SET FOREIGN_KEY_CHECKS = 0;

CREATE DATABASE IF NOT EXISTS `employee_attendance_db`;
USE `employee_attendance_db`;

-- Roles table
CREATE TABLE IF NOT EXISTS `Roles` (
    `Role_Id` INT AUTO_INCREMENT PRIMARY KEY,
    `Role_Name` VARCHAR(50) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- User authentication accounts
CREATE TABLE IF NOT EXISTS `Users` (
    `User_Id` INT AUTO_INCREMENT PRIMARY KEY,
    `Full_Name` VARCHAR(100) NOT NULL,
    `Email` VARCHAR(100) UNIQUE,
    `Phone` VARCHAR(15),
    `Password_hash` VARCHAR(200) NOT NULL,
    `Role_Id` INT NOT NULL,
    `Is_Active` BOOLEAN NOT NULL DEFAULT TRUE,
    `Must_Change_Password` BOOLEAN NOT NULL DEFAULT FALSE,
    `Created_At` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_users_role` FOREIGN KEY (`Role_Id`) REFERENCES `Roles`(`Role_Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Employee organizational profiles
CREATE TABLE IF NOT EXISTS `Employees` (
    `Employee_Id` INT PRIMARY KEY,
    `User_Id` INT NULL UNIQUE,
    `Manager_Id` INT NULL,
    `Employee_Name` VARCHAR(100),
    `Email` VARCHAR(100),
    `Phone` VARCHAR(15),
    `Department` VARCHAR(100),
    `Designation` VARCHAR(100),
    CONSTRAINT `fk_employee_user` FOREIGN KEY (`User_Id`) REFERENCES `Users`(`User_Id`),
    CONSTRAINT `fk_employee_manager` FOREIGN KEY (`Manager_Id`) REFERENCES `Users`(`User_Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Daily attendance records
CREATE TABLE IF NOT EXISTS `Attendance` (
    `Attendance_Id` INT AUTO_INCREMENT PRIMARY KEY,
    `Employee_Id` INT,
    `Attendance_Date` DATE DEFAULT (CURRENT_DATE),
    `Status` VARCHAR(50),
    CONSTRAINT `fk_attendance_employee` FOREIGN KEY (`Employee_Id`) REFERENCES `Employees`(`Employee_Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Leave requests and approvals
CREATE TABLE IF NOT EXISTS `Leave_Requests` (
    `Leave_Id` INT AUTO_INCREMENT PRIMARY KEY,
    `Employee_Id` INT,
    `From_Date` DATE,
    `To_Date` DATE,
    `Leave_Type` VARCHAR(50),
    `Reason` VARCHAR(500),
    `Status` VARCHAR(20) NOT NULL DEFAULT 'Pending',
    `Reviewed_By` INT NULL,
    `Reviewed_At` DATETIME NULL,
    CONSTRAINT `fk_leave_employee` FOREIGN KEY (`Employee_Id`) REFERENCES `Employees`(`Employee_Id`),
    CONSTRAINT `fk_leave_reviewed_by` FOREIGN KEY (`Reviewed_By`) REFERENCES `Users`(`User_Id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Session-level token blacklisting for logout
CREATE TABLE IF NOT EXISTS `Revoked_Tokens` (
    `RevokedToken_Id` INT AUTO_INCREMENT PRIMARY KEY,
    `Token_JTI` VARCHAR(100) NULL,
    `Session_Id` VARCHAR(100) NULL,
    `Expires_At` DATETIME NOT NULL,
    INDEX `idx_session_id` (`Session_Id`),
    INDEX `idx_token_jti` (`Token_JTI`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Standard roles seed
INSERT IGNORE INTO `Roles` (`Role_Id`, `Role_Name`) VALUES
(1, 'Admin'),
(2, 'manager'),
(3, 'employee');

-- Initial Administrator Account (admin@gmail.com / Admin@12345)
INSERT IGNORE INTO `Users` (`User_Id`, `Full_Name`, `Email`, `Phone`, `Password_hash`, `Role_Id`, `Is_Active`, `Must_Change_Password`, `Created_At`) VALUES
(1, 'System Administrator', 'admin@gmail.com', '9999999999', 'dc7f46fe12b70ed7$daba5455e7aa17ee0122d88ac91c3abc2ea23c7c38fe3b25257e189c709a50e4', 1, TRUE, FALSE, CURRENT_TIMESTAMP);

SET FOREIGN_KEY_CHECKS = 1;
