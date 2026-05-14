-- Create Students Table
CREATE TABLE IF NOT EXISTS students (
    id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    department VARCHAR(50),
    year INT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Events Table
CREATE TABLE IF NOT EXISTS events (
    event_id VARCHAR(20) PRIMARY KEY,
    event_name VARCHAR(100) NOT NULL,
    max_capacity INT NOT NULL,
    event_date DATE NOT NULL
);

-- Create Event Attendance (Tracker)
CREATE TABLE IF NOT EXISTS event_attendance (
    event_id VARCHAR(20) PRIMARY KEY,
    count INT DEFAULT 0,
    FOREIGN KEY (event_id) REFERENCES events(event_id)
);

-- Create Scan History / Audit Trail
CREATE TABLE IF NOT EXISTS scan_history (
    scan_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(20) NOT NULL,
    event_id VARCHAR(20) NOT NULL,
    scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('GRANTED', 'DENIED') NOT NULL,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (event_id) REFERENCES events(event_id)
);

-- Insert Mock Data
INSERT IGNORE INTO students (id, name, department, year, is_active) 
VALUES ('STU-12345', 'Abhi', 'Computer Science', 3, TRUE);

INSERT IGNORE INTO events (event_id, event_name, max_capacity, event_date)
VALUES ('EVT-2026', 'Cloud Computing Summit', 100, CURDATE());

INSERT IGNORE INTO event_attendance (event_id, count)
VALUES ('EVT-2026', 0);
