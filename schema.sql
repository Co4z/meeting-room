-- ============================================================
--  Meeting Room Booking System – MySQL Schema + Seed Data
--  Database: meeting_room_db
-- ============================================================

CREATE DATABASE IF NOT EXISTS meeting_room_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE meeting_room_db;

-- ----------------------------------------------------------
-- 1. USER
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS USER (
    user_id    INT AUTO_INCREMENT PRIMARY KEY,
    username   VARCHAR(50)  NOT NULL UNIQUE,
    full_name  VARCHAR(100) NOT NULL,
    email      VARCHAR(100) NOT NULL UNIQUE,
    phone      VARCHAR(20),
    department VARCHAR(100),
    role       ENUM('admin','maid','user') NOT NULL DEFAULT 'user',
    status     ENUM('active','inactive') NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ----------------------------------------------------------
-- 2. Room
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS Room (
    room_id        INT AUTO_INCREMENT PRIMARY KEY,
    room_name      VARCHAR(100) NOT NULL,
    capacity       INT NOT NULL,
    location_floor VARCHAR(50),
    description    TEXT,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ----------------------------------------------------------
-- 3. Equipment
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS Equipment (
    equipment_id  INT AUTO_INCREMENT PRIMARY KEY,
    room_id       INT NULL,   -- NULL = shared / portable equipment
    name          VARCHAR(100) NOT NULL,
    type          VARCHAR(50),
    is_room_fixed BOOLEAN NOT NULL DEFAULT FALSE,
    status        ENUM('available','in_use','maintenance') NOT NULL DEFAULT 'available',
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description   TEXT,
    CONSTRAINT fk_equip_room FOREIGN KEY (room_id) REFERENCES Room(room_id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ----------------------------------------------------------
-- 4. Booking
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS Booking (
    booking_id     INT AUTO_INCREMENT PRIMARY KEY,
    user_id        INT NOT NULL,
    room_id        INT NOT NULL,
    title          VARCHAR(200) NOT NULL,
    start_datetime DATETIME NOT NULL,
    end_datetime   DATETIME NOT NULL,
    status         ENUM('confirmed','pending','cancelled') NOT NULL DEFAULT 'confirmed',
    require_break  BOOLEAN NOT NULL DEFAULT FALSE,
    break_note     TEXT,
    note           TEXT,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    agenda_file    VARCHAR(255),
    CONSTRAINT fk_booking_user FOREIGN KEY (user_id) REFERENCES USER(user_id),
    CONSTRAINT fk_booking_room FOREIGN KEY (room_id) REFERENCES Room(room_id)
) ENGINE=InnoDB;

-- ----------------------------------------------------------
-- 5. Booking_attendee
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS Booking_attendee (
    attendee_id   INT AUTO_INCREMENT PRIMARY KEY,
    booking_id    INT NOT NULL,
    user_id       INT NULL,   -- NULL = external / non-system email
    email         VARCHAR(100) NOT NULL,
    notify_status ENUM('pending','sent','failed') NOT NULL DEFAULT 'pending',
    response      ENUM('pending','accepted','declined') NOT NULL DEFAULT 'pending',
    CONSTRAINT fk_att_booking FOREIGN KEY (booking_id) REFERENCES Booking(booking_id) ON DELETE CASCADE,
    CONSTRAINT fk_att_user    FOREIGN KEY (user_id)    REFERENCES USER(user_id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ----------------------------------------------------------
-- 6. Booking_Equipment
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS Booking_Equipment (
    booking_eq_id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id    INT NOT NULL,
    equipment_id  INT NOT NULL,
    quantity      INT NOT NULL DEFAULT 1,
    return_status ENUM('pending','returned','lost') NOT NULL DEFAULT 'pending',
    CONSTRAINT fk_beq_booking FOREIGN KEY (booking_id)   REFERENCES Booking(booking_id) ON DELETE CASCADE,
    CONSTRAINT fk_beq_equip   FOREIGN KEY (equipment_id) REFERENCES Equipment(equipment_id)
) ENGINE=InnoDB;


-- ============================================================
--  SEED DATA
-- ============================================================

-- Users (bcrypt placeholder passwords — replace in production)
INSERT INTO USER (username, full_name, email, phone, department, role, status) VALUES
('admin',   'ผู้ดูแลระบบ',      'admin@somapha.co.th',   '021110001', 'IT',              'admin', 'active'),
('maid1',   'สมฤดี วงศ์ทอง',    'maid1@somapha.co.th',   '021110002', 'Facility',        'maid',  'active'),
('user1',   'นภา ศรีสวัสดิ์',    'napa@somapha.co.th',    '021110003', 'Finance',         'user',  'active'),
('user2',   'ธนพล เจริญสุข',     'thanaphon@somapha.co.th','021110004','HR',              'user',  'active'),
('user3',   'ปิยะ มีชัย',        'piya@somapha.co.th',    '021110005', 'Engineering',     'user',  'active'),
('user4',   'วรรณา โรจนกุล',     'wanna@somapha.co.th',   '021110006', 'Marketing',       'user',  'active'),
('user5',   'กิตติพงษ์ พรมมา',   'kitti@somapha.co.th',   '021110007', 'Engineering',     'user',  'active');

-- Rooms: 1×50, 2×15, 2×7
INSERT INTO Room (room_name, capacity, location_floor, description) VALUES
('ห้องประชุมใหญ่', 50, 'ชั้น 10', 'ห้องประชุมขนาดใหญ่สำหรับงานสัมมนาและอบรม'),
('ห้อง M-1',       15, 'ชั้น 8',  'ห้องประชุมขนาดกลาง สำหรับประชุมทีม'),
('ห้อง M-2',       15, 'ชั้น 8',  'ห้องประชุมขนาดกลาง พร้อมระบบขยายเสียง'),
('ห้อง S-1',        7, 'ชั้น 6',  'ห้องประชุมเล็ก เหมาะสำหรับสัมภาษณ์หรือประชุมย่อย'),
('ห้อง S-2',        7, 'ชั้น 6',  'ห้องประชุมเล็ก พร้อม TV สำหรับการนำเสนอ');

-- Fixed equipment per room
INSERT INTO Equipment (room_id, name, type, is_room_fixed, status, description) VALUES
(1, 'Projector 4K',       'Visual',     TRUE, 'available', 'โปรเจกเตอร์ 4K ขนาดใหญ่'),
(1, 'ไมค์ประชุม (set)',   'Audio',      TRUE, 'available', 'ชุดไมค์โครโฟนประชุม 10 ตัว'),
(1, 'บันทึกเสียง',        'Audio',      TRUE, 'available', 'เครื่องบันทึกเสียงประชุม'),
(1, 'Laptop ประจำห้อง',   'Computing',  TRUE, 'available', 'Laptop สำหรับนำเสนอ'),
(2, 'Projector HD',       'Visual',     TRUE, 'available', 'โปรเจกเตอร์ HD'),
(2, 'กระดานบันทึก',       'Whiteboard', TRUE, 'available', 'กระดานไวท์บอร์ด 120×80 cm'),
(3, 'Projector HD',       'Visual',     TRUE, 'available', 'โปรเจกเตอร์ HD'),
(3, 'กระดานบันทึก',       'Whiteboard', TRUE, 'available', 'กระดานไวท์บอร์ด 120×80 cm'),
(3, 'เครื่องขยายเสียง',   'Audio',      TRUE, 'available', 'ลำโพงขยายเสียงห้องประชุม'),
(4, 'TV 65"',             'Visual',     TRUE, 'available', 'Smart TV 65 นิ้ว'),
(4, 'กระดานบันทึก',       'Whiteboard', TRUE, 'available', 'กระดานไวท์บอร์ด 90×60 cm'),
(5, 'TV 65"',             'Visual',     TRUE, 'available', 'Smart TV 65 นิ้ว');

-- Shared / portable equipment (room_id = NULL)
INSERT INTO Equipment (room_id, name, type, is_room_fixed, status, description) VALUES
(NULL, 'Projector พกพา',     'Visual',    FALSE, 'available',   'โปรเจกเตอร์แบบพกพา'),
(NULL, 'Laptop พกพา',        'Computing', FALSE, 'available',   'Notebook สำรอง'),
(NULL, 'ไมค์ Wireless',      'Audio',     FALSE, 'available',   'ไมค์ไร้สาย 2 ตัว'),
(NULL, 'เครื่องขยายเสียงพกพา','Audio',   FALSE, 'maintenance', 'อยู่ระหว่างซ่อมบำรุง'),
(NULL, 'กล้อง Webcam 4K',    'Video',     FALSE, 'available',   'กล้องประชุมออนไลน์');

-- Bookings (seed – realistic past + future around 2026-05-05)
INSERT INTO Booking (user_id, room_id, title, start_datetime, end_datetime, status, require_break, break_note, note) VALUES
(3, 1, 'ประชุมคณะกรรมการบริหาร',          '2026-05-05 09:00:00', '2026-05-05 11:00:00', 'confirmed', TRUE,  'เบรกช่วงเช้า', ''),
(5, 2, 'หารือโปรเจกต์ระบบ ERP',           '2026-05-05 09:00:00', '2026-05-05 10:00:00', 'confirmed', FALSE, '', ''),
(4, 4, 'สัมภาษณ์ผู้สมัครงาน',              '2026-05-05 13:00:00', '2026-05-05 14:00:00', 'confirmed', FALSE, '', ''),
(6, 5, 'ประชุมทีม Marketing',              '2026-05-05 13:00:00', '2026-05-05 15:00:00', 'confirmed', FALSE, '', ''),
(3, 3, 'Safety Training',                  '2026-05-05 14:00:00', '2026-05-05 16:00:00', 'confirmed', TRUE,  'เบรกช่วงบ่าย', ''),
(5, 2, 'ประชุมทีมพัฒนา Sprint 12',         '2026-05-08 14:00:00', '2026-05-08 15:00:00', 'pending',   FALSE, '', ''),
(3, 1, 'ประชุมทบทวนยุทธศาสตร์',            '2026-05-07 09:00:00', '2026-05-07 10:30:00', 'confirmed', FALSE, '', ''),
(3, 1, 'Workshop AI for Business',         '2026-05-12 10:00:00', '2026-05-12 12:00:00', 'confirmed', TRUE,  'อาหารกลางวัน', ''),
(4, 5, 'หารืองบประมาณ Q3',                 '2026-05-15 15:00:00', '2026-05-15 16:00:00', 'confirmed', FALSE, '', '');

-- Attendees
INSERT INTO Booking_attendee (booking_id, user_id, email, notify_status, response) VALUES
(1, 2, 'maid1@somapha.co.th',     'sent', 'accepted'),
(1, 4, 'thanaphon@somapha.co.th', 'sent', 'accepted'),
(1, 6, 'wanna@somapha.co.th',     'sent', 'pending'),
(2, 7, 'kitti@somapha.co.th',     'sent', 'accepted'),
(3, 5, 'piya@somapha.co.th',      'sent', 'accepted'),
(4, 3, 'napa@somapha.co.th',      'sent', 'pending'),
(5, 4, 'thanaphon@somapha.co.th', 'sent', 'accepted'),
(7, 4, 'thanaphon@somapha.co.th', 'sent', 'accepted'),
(7, 6, 'wanna@somapha.co.th',     'sent', 'accepted');

-- Booking Equipment links
INSERT INTO Booking_Equipment (booking_id, equipment_id, quantity, return_status) VALUES
(1, 13, 1, 'pending'),   -- shared projector
(2, 6,  1, 'returned'),  -- M-1 projector
(4, 12, 1, 'pending'),   -- S-2 TV fixed
(5, 15, 2, 'pending');   -- wireless mic
