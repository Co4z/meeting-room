-- phpMyAdmin SQL Dump
-- version 4.9.1
-- https://www.phpmyadmin.net/
--
-- Host: localhost
-- Generation Time: May 07, 2026 at 03:57 AM
-- Server version: 8.0.17
-- PHP Version: 7.3.10

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `meeting_room_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `booking`
--

CREATE TABLE `booking` (
  `booking_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `room_id` int(11) NOT NULL,
  `title` varchar(200) NOT NULL,
  `start_datetime` datetime NOT NULL,
  `end_datetime` datetime NOT NULL,
  `status` enum('confirmed','pending','cancelled') NOT NULL DEFAULT 'confirmed',
  `require_break` tinyint(1) NOT NULL DEFAULT '0',
  `break_note` text,
  `note` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `agenda_file` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `booking`
--

INSERT INTO `booking` (`booking_id`, `user_id`, `room_id`, `title`, `start_datetime`, `end_datetime`, `status`, `require_break`, `break_note`, `note`, `created_at`, `agenda_file`) VALUES
(5, 3, 5, 'ห้องทดลอง', '2026-05-06 15:00:00', '2026-05-06 16:00:00', 'confirmed', 1, 'เบรกช่วงเช้า', '', '2026-05-06 07:20:28', NULL),
(6, 3, 4, 'ห้องทดลอง2', '2026-05-06 15:00:00', '2026-05-06 16:00:00', 'confirmed', 1, 'เบรกช่วงบ่าย', '', '2026-05-06 07:25:53', NULL),
(7, 3, 1, 'ห้องทอลอง', '2026-05-06 15:00:00', '2026-05-06 17:00:00', 'confirmed', 1, 'เบรกช่วงบ่าย', '', '2026-05-06 07:35:57', NULL),
(8, 3, 3, 'ห้องทอลอง', '2026-05-07 15:00:00', '2026-05-07 17:00:00', 'confirmed', 1, 'เบรกช่วงบ่าย', '', '2026-05-06 07:36:23', NULL),
(9, 3, 1, 'ห้องทดลอง', '2026-05-08 09:00:00', '2026-05-08 10:30:00', 'confirmed', 0, '', '', '2026-05-06 07:41:54', NULL),
(10, 3, 3, 'ห้องลอง', '2026-05-21 09:00:00', '2026-05-21 10:30:00', 'confirmed', 0, '', '', '2026-05-06 07:42:46', NULL),
(11, 3, 5, 'ห้องทดลอง', '2026-05-29 08:00:00', '2026-05-29 10:00:00', 'confirmed', 1, 'เบรกช่วงเช้า', '', '2026-05-06 07:53:04', NULL);

-- --------------------------------------------------------

--
-- Table structure for table `booking_attendee`
--

CREATE TABLE `booking_attendee` (
  `attendee_id` int(11) NOT NULL,
  `booking_id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `email` varchar(100) NOT NULL,
  `notify_status` enum('pending','sent','failed') NOT NULL DEFAULT 'pending',
  `response` enum('pending','accepted','declined') NOT NULL DEFAULT 'pending'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `booking_attendee`
--

INSERT INTO `booking_attendee` (`attendee_id`, `booking_id`, `user_id`, `email`, `notify_status`, `response`) VALUES
(11, 5, NULL, 'ice@gmail.com', 'pending', 'pending'),
(12, 5, NULL, 'kong@gmail.com', 'pending', 'pending'),
(13, 6, NULL, 'ice@gmail.com', 'pending', 'pending'),
(14, 6, NULL, 'kong@gmail.com', 'pending', 'pending'),
(15, 11, NULL, 'ice@gmail.com', 'pending', 'pending'),
(16, 11, NULL, 'kong@gmail.com', 'pending', 'pending'),
(17, 11, NULL, 'Vee@gmail.com', 'pending', 'pending');

-- --------------------------------------------------------

--
-- Table structure for table `booking_equipment`
--

CREATE TABLE `booking_equipment` (
  `booking_eq_id` int(11) NOT NULL,
  `booking_id` int(11) NOT NULL,
  `equipment_id` int(11) NOT NULL,
  `quantity` int(11) NOT NULL DEFAULT '1',
  `return_status` enum('pending','returned','lost') NOT NULL DEFAULT 'pending'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `booking_equipment`
--

INSERT INTO `booking_equipment` (`booking_eq_id`, `booking_id`, `equipment_id`, `quantity`, `return_status`) VALUES
(13, 5, 26, 1, 'pending'),
(14, 6, 26, 1, 'pending'),
(15, 6, 27, 1, 'pending'),
(16, 7, 26, 1, 'pending'),
(17, 7, 27, 1, 'pending'),
(18, 8, 26, 1, 'pending'),
(19, 8, 27, 1, 'pending'),
(20, 9, 26, 1, 'pending'),
(21, 9, 27, 1, 'pending'),
(22, 10, 26, 1, 'pending'),
(23, 10, 27, 1, 'pending'),
(24, 11, 26, 1, 'pending'),
(25, 11, 27, 1, 'pending');

-- --------------------------------------------------------

--
-- Table structure for table `equipment`
--

CREATE TABLE `equipment` (
  `equipment_id` int(11) NOT NULL,
  `room_id` int(11) DEFAULT NULL,
  `name` varchar(100) NOT NULL,
  `type` varchar(50) DEFAULT NULL,
  `is_room_fixed` tinyint(1) NOT NULL DEFAULT '0',
  `status` enum('available','in_use','maintenance') NOT NULL DEFAULT 'available',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `description` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `equipment`
--

INSERT INTO `equipment` (`equipment_id`, `room_id`, `name`, `type`, `is_room_fixed`, `status`, `created_at`, `description`) VALUES
(1, 1, 'Projector', 'Visual', 1, 'available', '2026-05-06 04:30:07', ''),
(2, 1, 'เครื่องขยายเสียง', 'Audio', 1, 'available', '2026-05-06 04:30:14', ''),
(3, 1, 'เครื่องบันทึกเสียง', 'Audio', 1, 'available', '2026-05-06 04:30:21', ''),
(4, 1, 'กระดานบันทึกข้อความ', 'Whiteboard', 1, 'available', '2026-05-06 04:30:31', ''),
(5, 1, 'เครื่องคอมพิวเตอร์ Laptop', 'Computing', 1, 'available', '2026-05-06 04:30:39', ''),
(6, 2, 'Projector', 'Visual', 1, 'available', '2026-05-06 04:31:07', ''),
(7, 2, 'เครื่องขยายเสียง', 'Audio', 1, 'available', '2026-05-06 06:09:43', ''),
(8, 2, 'เครื่องบันทึกเสียง', 'Audio', 1, 'available', '2026-05-06 06:09:54', ''),
(9, 2, 'กระดานบันทึกข้อความ', 'Whiteboard', 1, 'available', '2026-05-06 06:10:05', ''),
(10, 2, 'เครื่องคอมพิวเตอร์ Laptop', 'Computing', 1, 'available', '2026-05-06 06:10:38', ''),
(11, 3, 'Projector', 'Visual', 1, 'available', '2026-05-06 06:10:56', ''),
(12, 3, 'เครื่องขยายเสียง', 'Audio', 1, 'available', '2026-05-06 06:11:14', ''),
(13, 3, 'เครื่องบันทึกเสียง', 'Audio', 1, 'available', '2026-05-06 06:11:33', ''),
(14, 3, 'กระดานบันทึกข้อความ', 'Whiteboard', 1, 'available', '2026-05-06 06:11:42', ''),
(15, 3, 'เครื่องคอมพิวเตอร์ Laptop', 'Computing', 1, 'available', '2026-05-06 06:11:54', ''),
(16, 4, 'Projector', 'Visual', 1, 'available', '2026-05-06 06:12:12', ''),
(17, 4, 'เครื่องขยายเสียง', 'Audio', 1, 'available', '2026-05-06 06:13:17', ''),
(18, 4, 'เครื่องบันทึกเสียง', 'Audio', 1, 'available', '2026-05-06 06:13:44', ''),
(19, 4, 'กระดานบันทึกข้อความ', 'Whiteboard', 1, 'available', '2026-05-06 06:13:51', ''),
(20, 4, 'เครื่องคอมพิวเตอร์ Laptop', 'Computing', 1, 'available', '2026-05-06 06:14:06', ''),
(21, 5, 'Projector', 'Visual', 1, 'available', '2026-05-06 06:14:18', ''),
(22, 5, 'เครื่องขยายเสียง', 'Audio', 1, 'available', '2026-05-06 06:14:26', ''),
(23, 5, 'เครื่องบันทึกเสียง', 'Audio', 1, 'available', '2026-05-06 06:14:36', ''),
(24, 5, 'กระดานบันทึกข้อความ', 'Whiteboard', 1, 'available', '2026-05-06 06:14:54', ''),
(25, 5, 'เครื่องคอมพิวเตอร์ Laptop', 'Computing', 1, 'available', '2026-05-06 06:15:10', ''),
(26, NULL, 'ไมโครโฟนไร้สาย', 'Audio', 0, 'available', '2026-05-06 06:20:23', ''),
(27, NULL, 'ปลั๊กเสริม', 'Other', 0, 'available', '2026-05-06 06:21:56', '');

-- --------------------------------------------------------

--
-- Table structure for table `room`
--

CREATE TABLE `room` (
  `room_id` int(11) NOT NULL,
  `room_name` varchar(100) NOT NULL,
  `capacity` int(11) NOT NULL,
  `location_floor` varchar(50) DEFAULT NULL,
  `description` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `room`
--

INSERT INTO `room` (`room_id`, `room_name`, `capacity`, `location_floor`, `description`, `created_at`) VALUES
(1, 'ห้องประชุม L', 50, 'ชั้น 1', 'ห้องประชุมขนาดใหญ่สำหรับงานสัมมนาและอบรม', '2026-05-05 07:02:18'),
(2, 'ห้อง M-1', 15, 'ชั้น 2', 'ห้องประชุมขนาดกลาง สำหรับประชุมทีม', '2026-05-05 07:02:18'),
(3, 'ห้อง M-2', 15, 'ชั้น 2', 'ห้องประชุมขนาดกลาง พร้อมระบบขยายเสียง', '2026-05-05 07:02:18'),
(4, 'ห้อง S-1', 7, 'ชั้น 2', 'ห้องประชุมเล็ก เหมาะสำหรับสัมภาษณ์หรือประชุมย่อย', '2026-05-05 07:02:18'),
(5, 'ห้อง S-2', 7, 'ชั้น 2', 'ห้องประชุมเล็ก พร้อม TV สำหรับการนำเสนอ', '2026-05-05 07:02:18');

-- --------------------------------------------------------

--
-- Table structure for table `user`
--

CREATE TABLE `user` (
  `user_id` int(11) NOT NULL,
  `username` varchar(50) NOT NULL,
  `full_name` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `department` varchar(100) DEFAULT NULL,
  `role` enum('admin','maid','user') NOT NULL DEFAULT 'user',
  `status` enum('active','inactive') NOT NULL DEFAULT 'active',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `user`
--

INSERT INTO `user` (`user_id`, `username`, `full_name`, `email`, `phone`, `department`, `role`, `status`, `created_at`) VALUES
(1, 'admin', 'ผู้ดูแลระบบ', 'admin@somapha.co.th', '021110001', 'IT', 'admin', 'active', '2026-05-05 07:02:18'),
(2, 'maid1', 'สมฤดี วงศ์ทอง', 'maid1@somapha.co.th', '021110002', 'Facility', 'maid', 'active', '2026-05-05 07:02:18'),
(3, 'user1', 'นภา ศรีสวัสดิ์', 'napa@somapha.co.th', '021110003', 'Finance', 'user', 'active', '2026-05-05 07:02:18'),
(4, 'user2', 'ธนพล เจริญสุข', 'thanaphon@somapha.co.th', '021110004', 'HR', 'user', 'active', '2026-05-05 07:02:18'),
(5, 'user3', 'ปิยะ มีชัย', 'piya@somapha.co.th', '021110005', 'Engineering', 'user', 'active', '2026-05-05 07:02:18'),
(6, 'user4', 'วรรณา โรจนกุล', 'wanna@somapha.co.th', '021110006', 'Marketing', 'user', 'active', '2026-05-05 07:02:18'),
(7, 'user5', 'กิตติพงษ์ พรมมา', 'kitti@somapha.co.th', '021110007', 'Engineering', 'user', 'active', '2026-05-05 07:02:18');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `booking`
--
ALTER TABLE `booking`
  ADD PRIMARY KEY (`booking_id`),
  ADD KEY `fk_booking_user` (`user_id`),
  ADD KEY `fk_booking_room` (`room_id`);

--
-- Indexes for table `booking_attendee`
--
ALTER TABLE `booking_attendee`
  ADD PRIMARY KEY (`attendee_id`),
  ADD KEY `fk_att_booking` (`booking_id`),
  ADD KEY `fk_att_user` (`user_id`);

--
-- Indexes for table `booking_equipment`
--
ALTER TABLE `booking_equipment`
  ADD PRIMARY KEY (`booking_eq_id`),
  ADD KEY `fk_beq_booking` (`booking_id`),
  ADD KEY `fk_beq_equip` (`equipment_id`);

--
-- Indexes for table `equipment`
--
ALTER TABLE `equipment`
  ADD PRIMARY KEY (`equipment_id`),
  ADD KEY `fk_equip_room` (`room_id`);

--
-- Indexes for table `room`
--
ALTER TABLE `room`
  ADD PRIMARY KEY (`room_id`);

--
-- Indexes for table `user`
--
ALTER TABLE `user`
  ADD PRIMARY KEY (`user_id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `email` (`email`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `booking`
--
ALTER TABLE `booking`
  MODIFY `booking_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT for table `booking_attendee`
--
ALTER TABLE `booking_attendee`
  MODIFY `attendee_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=18;

--
-- AUTO_INCREMENT for table `booking_equipment`
--
ALTER TABLE `booking_equipment`
  MODIFY `booking_eq_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=26;

--
-- AUTO_INCREMENT for table `equipment`
--
ALTER TABLE `equipment`
  MODIFY `equipment_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=28;

--
-- AUTO_INCREMENT for table `room`
--
ALTER TABLE `room`
  MODIFY `room_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT for table `user`
--
ALTER TABLE `user`
  MODIFY `user_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `booking`
--
ALTER TABLE `booking`
  ADD CONSTRAINT `fk_booking_room` FOREIGN KEY (`room_id`) REFERENCES `room` (`room_id`),
  ADD CONSTRAINT `fk_booking_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`);

--
-- Constraints for table `booking_attendee`
--
ALTER TABLE `booking_attendee`
  ADD CONSTRAINT `fk_att_booking` FOREIGN KEY (`booking_id`) REFERENCES `booking` (`booking_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_att_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`) ON DELETE SET NULL;

--
-- Constraints for table `booking_equipment`
--
ALTER TABLE `booking_equipment`
  ADD CONSTRAINT `fk_beq_booking` FOREIGN KEY (`booking_id`) REFERENCES `booking` (`booking_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_beq_equip` FOREIGN KEY (`equipment_id`) REFERENCES `equipment` (`equipment_id`);

--
-- Constraints for table `equipment`
--
ALTER TABLE `equipment`
  ADD CONSTRAINT `fk_equip_room` FOREIGN KEY (`room_id`) REFERENCES `room` (`room_id`) ON DELETE SET NULL;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
