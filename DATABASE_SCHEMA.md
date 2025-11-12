# DATABASE SCHEMA DOCUMENTATION
## Personalized Medical Assistant (PMA) Project

**Database Name:** personalized_medicine_db  
**Database Type:** MySQL  
**Connection:** localhost:3300  
**Generated On:** November 7, 2025  
**Total Tables:** 19

---

## TABLE SCHEMA DETAILS

### 1. AUTH_USER
**Description:** Core user authentication table

| Column | Data Type | Constraints |
|--------|-----------|-------------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT, NOT NULL |
| username | VARCHAR(150) | UNIQUE, NOT NULL |
| password | VARCHAR(128) | NOT NULL |
| email | VARCHAR(254) | NOT NULL |
| first_name | VARCHAR(150) | NOT NULL |
| last_name | VARCHAR(150) | NOT NULL |
| is_staff | TINYINT(1) | NOT NULL |
| is_active | TINYINT(1) | NOT NULL |
| is_superuser | TINYINT(1) | NOT NULL |
| last_login | DATETIME(6) | NULL |
| date_joined | DATETIME(6) | NOT NULL |

**Current Records:** 6 users

---

### 2. AUTH_GROUP
**Description:** User groups for permission management

| Column | Data Type | Constraints |
|--------|-----------|-------------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT, NOT NULL |
| name | VARCHAR(150) | UNIQUE, NOT NULL |

**Current Records:** 2 groups (Doctors, Patients)

---

### 3. AUTH_GROUP_PERMISSIONS
**Description:** Links groups to specific permissions

| Column | Data Type | Constraints |
|--------|-----------|-------------|
| id | BIGINT | PRIMARY KEY, AUTO_INCREMENT, NOT NULL |
| group_id | INT | FOREIGN KEY REFERENCES auth_group(id), NOT NULL |
| permission_id | INT | FOREIGN KEY REFERENCES auth_permission(id), NOT NULL |

**Current Records:** 0

---

### 4. AUTH_PERMISSION
**Description:** All available system permissions

| Column | Data Type | Constraints |
|--------|-----------|-------------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT, NOT NULL |
| name | VARCHAR(255) | NOT NULL |
| content_type_id | INT | FOREIGN KEY REFERENCES django_content_type(id), NOT NULL |
| codename | VARCHAR(100) | NOT NULL |

**Current Records:** 60 permissions

---

### 5. AUTH_USER_GROUPS
**Description:** Many-to-many relationship between users and groups

| Column | Data Type | Constraints |
|--------|-----------|-------------|
| id | BIGINT | PRIMARY KEY, AUTO_INCREMENT, NOT NULL |
| user_id | INT | FOREIGN KEY REFERENCES auth_user(id), NOT NULL |
| group_id | INT | FOREIGN KEY REFERENCES auth_group(id), NOT NULL |

**Current Records:** 6

---

### 6. AUTH_USER_USER_PERMISSIONS
**Description:** Direct user permissions (bypass groups)

| Column | Data Type | Constraints |
|--------|-----------|-------------|
| id | BIGINT | PRIMARY KEY, AUTO_INCREMENT, NOT NULL |
| user_id | INT | FOREIGN KEY REFERENCES auth_user(id), NOT NULL |
| permission_id | INT | FOREIGN KEY REFERENCES auth_permission(id), NOT NULL |

**Current Records:** 0

---

### 7. DOCTORS_DOCTORPROFILE
**Description:** Extended profile information for doctors

| Column | Data Type | Constraints |
|--------|-----------|-------------|
| id | BIGINT | PRIMARY KEY, AUTO_INCREMENT, NOT NULL |
| user_id | INT | FOREIGN KEY REFERENCES auth_user(id), UNIQUE, NOT NULL |
| full_name | VARCHAR(100) | NOT NULL |
| specialization | VARCHAR(20) | NOT NULL |
| license_number | VARCHAR(50) | NOT NULL |
| years_of_experience | INT UNSIGNED | NOT NULL |
| hospital_clinic | VARCHAR(200) | NOT NULL |
| address | LONGTEXT | NOT NULL |
| phone_number | VARCHAR(20) | NOT NULL |
| consultation_fee | DECIMAL(8,2) | NOT NULL |
| qualifications | LONGTEXT | NOT NULL |
| about | LONGTEXT | NOT NULL |
| is_available | TINYINT(1) | NOT NULL |
| created_at | DATETIME(6) | NOT NULL |
| updated_at | DATETIME(6) | NOT NULL |

**Current Records:** 3 doctors

---

### 8. DOCTORS_DOCTORAVAILABILITY
**Description:** Doctor working hours and availability schedule

| Column | Data Type | Constraints |
|--------|-----------|-------------|
| id | BIGINT | PRIMARY KEY, AUTO_INCREMENT, NOT NULL |
| doctor_id | BIGINT | FOREIGN KEY REFERENCES doctors_doctorprofile(id), NOT NULL |
| weekday | INT | NOT NULL |
| start_time | TIME(6) | NOT NULL |
| end_time | TIME(6) | NOT NULL |
| is_active | TINYINT(1) | NOT NULL |

**Current Records:** 21 availability slots  
**Note:** weekday: 0=Monday, 1=Tuesday, ... 6=Sunday

---

### 9. PATIENTS_PATIENTPROFILE
**Description:** Extended profile information for patients

| Column | Data Type | Constraints |
|--------|-----------|-------------|
| id | BIGINT | PRIMARY KEY, AUTO_INCREMENT, NOT NULL |
| user_id | INT | FOREIGN KEY REFERENCES auth_user(id), UNIQUE, NOT NULL |
| full_name | VARCHAR(100) | NOT NULL |
| age | INT UNSIGNED | NULL |
| height | DOUBLE | NULL |
| weight | DOUBLE | NULL |
| blood_group | VARCHAR(3) | NOT NULL |
| medical_history | LONGTEXT | NOT NULL |
| allergies | LONGTEXT | NOT NULL |
| current_medications | LONGTEXT | NOT NULL |
| bmi | DOUBLE | NULL |
| bmi_status | VARCHAR(20) | NOT NULL |
| created_at | DATETIME(6) | NOT NULL |
| updated_at | DATETIME(6) | NOT NULL |

**Current Records:** 2 patients

---

### 10. PATIENTS_APPOINTMENT
**Description:** Appointment bookings between patients and doctors

| Column | Data Type | Constraints |
|--------|-----------|-------------|
| id | BIGINT | PRIMARY KEY, AUTO_INCREMENT, NOT NULL |
| patient_id | BIGINT | FOREIGN KEY REFERENCES patients_patientprofile(id), NOT NULL |
| doctor_id | BIGINT | FOREIGN KEY REFERENCES doctors_doctorprofile(id), NOT NULL |
| appointment_date | DATE | NOT NULL |
| appointment_time | TIME(6) | NOT NULL |
| reason | LONGTEXT | NOT NULL |
| status | VARCHAR(20) | NOT NULL |
| doctor_notes | LONGTEXT | NOT NULL |
| created_at | DATETIME(6) | NOT NULL |
| updated_at | DATETIME(6) | NOT NULL |

**Current Records:** 9 appointments  
**Status Values:** pending, confirmed, completed, cancelled

---

### 11. PATIENTS_MEDICALRECORD
**Description:** Medical documents and records uploaded by patients

| Column | Data Type | Constraints |
|--------|-----------|-------------|
| id | BIGINT | PRIMARY KEY, AUTO_INCREMENT, NOT NULL |
| patient_id | BIGINT | FOREIGN KEY REFERENCES patients_patientprofile(id), NOT NULL |
| title | VARCHAR(200) | NOT NULL |
| record_type | VARCHAR(20) | NOT NULL |
| description | LONGTEXT | NOT NULL |
| file | VARCHAR(100) | NULL |
| date_created | DATE | NOT NULL |
| uploaded_at | DATETIME(6) | NOT NULL |

**Current Records:** 1  
**Record Types:** prescription, lab_report, xray, scan, other

---

### 12. PATIENTS_MEDICINEREMINDER
**Description:** Medication reminders and schedules for patients

| Column | Data Type | Constraints |
|--------|-----------|-------------|
| id | BIGINT | PRIMARY KEY, AUTO_INCREMENT, NOT NULL |
| patient_id | BIGINT | FOREIGN KEY REFERENCES patients_patientprofile(id), NOT NULL |
| medicine_name | VARCHAR(200) | NOT NULL |
| dosage | VARCHAR(100) | NOT NULL |
| frequency | VARCHAR(10) | NOT NULL |
| time_1 | TIME(6) | NOT NULL |
| time_2 | TIME(6) | NULL |
| time_3 | TIME(6) | NULL |
| time_4 | TIME(6) | NULL |
| start_date | DATE | NOT NULL |
| end_date | DATE | NOT NULL |
| notes | LONGTEXT | NOT NULL |
| is_active | TINYINT(1) | NOT NULL |
| created_at | DATETIME(6) | NOT NULL |

**Current Records:** 2  
**Frequency Values:** daily, weekly, monthly, as_needed

---

### 13. PATIENTS_DISEASEPREDICTION
**Description:** ML-based disease predictions from symptoms

| Column | Data Type | Constraints |
|--------|-----------|-------------|
| id | BIGINT | PRIMARY KEY, AUTO_INCREMENT, NOT NULL |
| patient_id | BIGINT | FOREIGN KEY REFERENCES patients_patientprofile(id), NOT NULL |
| symptoms | LONGTEXT | NOT NULL |
| predicted_disease | VARCHAR(200) | NOT NULL |
| confidence_score | DOUBLE | NOT NULL |
| recommended_medicines | LONGTEXT | NOT NULL |
| recommended_diet | LONGTEXT | NOT NULL |
| created_at | DATETIME(6) | NOT NULL |

**Current Records:** 6 predictions

---

### 14. PATIENTS_MESSAGE
**Description:** Messaging system between patients and doctors

| Column | Data Type | Constraints |
|--------|-----------|-------------|
| id | BIGINT | PRIMARY KEY, AUTO_INCREMENT, NOT NULL |
| sender_id | INT | FOREIGN KEY REFERENCES auth_user(id), NOT NULL |
| recipient_id | INT | FOREIGN KEY REFERENCES auth_user(id), NOT NULL |
| appointment_id | BIGINT | FOREIGN KEY REFERENCES patients_appointment(id), NOT NULL |
| subject | VARCHAR(200) | NOT NULL |
| content | LONGTEXT | NOT NULL |
| original_content | LONGTEXT | NOT NULL |
| is_read | TINYINT(1) | NOT NULL |
| is_edited | TINYINT(1) | NOT NULL |
| is_deleted | TINYINT(1) | NOT NULL |
| is_deleted_for_everyone | TINYINT(1) | NOT NULL |
| deleted_by_id | INT | FOREIGN KEY REFERENCES auth_user(id), NULL |
| edit_count | INT UNSIGNED | NOT NULL |
| last_edited_at | DATETIME(6) | NULL |
| created_at | DATETIME(6) | NOT NULL |
| updated_at | DATETIME(6) | NOT NULL |

**Current Records:** 16 messages

---

### 15. PATIENTS_MESSAGEEDITHISTORY
**Description:** Tracks all edits made to messages

| Column | Data Type | Constraints |
|--------|-----------|-------------|
| id | BIGINT | PRIMARY KEY, AUTO_INCREMENT, NOT NULL |
| message_id | BIGINT | FOREIGN KEY REFERENCES patients_message(id), NOT NULL |
| previous_content | LONGTEXT | NOT NULL |
| edited_by_id | INT | FOREIGN KEY REFERENCES auth_user(id), NOT NULL |
| edited_at | DATETIME(6) | NOT NULL |

**Current Records:** 1

---

### 16. DJANGO_CONTENT_TYPE
**Description:** Django's model registry

| Column | Data Type | Constraints |
|--------|-----------|-------------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT, NOT NULL |
| app_label | VARCHAR(100) | NOT NULL |
| model | VARCHAR(100) | NOT NULL |

**Current Records:** 15

---

### 17. DJANGO_MIGRATIONS
**Description:** Database migration history

| Column | Data Type | Constraints |
|--------|-----------|-------------|
| id | BIGINT | PRIMARY KEY, AUTO_INCREMENT, NOT NULL |
| app | VARCHAR(255) | NOT NULL |
| name | VARCHAR(255) | NOT NULL |
| applied | DATETIME(6) | NOT NULL |

**Current Records:** 23 migrations applied

---

### 18. DJANGO_SESSION
**Description:** User session management

| Column | Data Type | Constraints |
|--------|-----------|-------------|
| session_key | VARCHAR(40) | PRIMARY KEY, NOT NULL |
| session_data | LONGTEXT | NOT NULL |
| expire_date | DATETIME(6) | NOT NULL |

**Current Records:** 2 active sessions

---

### 19. DJANGO_ADMIN_LOG
**Description:** Admin action audit trail

| Column | Data Type | Constraints |
|--------|-----------|-------------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT, NOT NULL |
| action_time | DATETIME(6) | NOT NULL |
| object_id | LONGTEXT | NULL |
| object_repr | VARCHAR(200) | NOT NULL |
| action_flag | SMALLINT UNSIGNED | NOT NULL |
| change_message | LONGTEXT | NOT NULL |
| content_type_id | INT | FOREIGN KEY REFERENCES django_content_type(id), NULL |
| user_id | INT | FOREIGN KEY REFERENCES auth_user(id), NOT NULL |

**Current Records:** 0

---

## DATABASE STATISTICS

| Metric | Count |
|--------|-------|
| Total Tables | 19 |
| Core Application Tables | 9 |
| Django System Tables | 10 |
| Total Users | 6 |
| Doctors | 3 |
| Patients | 2 |
| Appointments | 9 |
| Disease Predictions | 6 |
| Messages | 16 |
| Medical Records | 1 |
| Medicine Reminders | 2 |
| Doctor Availability Slots | 21 |

---

## RELATIONSHIPS DIAGRAM (ER Model)

```
AUTH_USER (1) ──────┬──── (1) DOCTORS_DOCTORPROFILE
                    │
                    └──── (1) PATIENTS_PATIENTPROFILE

DOCTORS_DOCTORPROFILE (1) ──── (*) DOCTORS_DOCTORAVAILABILITY

PATIENTS_PATIENTPROFILE (1) ──┬── (*) PATIENTS_APPOINTMENT
                               ├── (*) PATIENTS_MEDICALRECORD
                               ├── (*) PATIENTS_MEDICINEREMINDER
                               └── (*) PATIENTS_DISEASEPREDICTION

DOCTORS_DOCTORPROFILE (1) ──── (*) PATIENTS_APPOINTMENT

PATIENTS_APPOINTMENT (1) ──── (*) PATIENTS_MESSAGE

AUTH_USER (*) ──── (*) PATIENTS_MESSAGE (sender/recipient)

PATIENTS_MESSAGE (1) ──── (*) PATIENTS_MESSAGEEDITHISTORY
```

---

## NOTES

1. **Primary Keys:** All tables use auto-incrementing integer/bigint primary keys
2. **Foreign Keys:** All relationships enforced at database level
3. **Timestamps:** All major tables include created_at and updated_at fields
4. **Soft Deletes:** Messages support soft deletion with is_deleted flags
5. **Audit Trail:** Message edits are tracked in a separate history table
6. **Data Types:** 
   - Text fields use VARCHAR for limited length, LONGTEXT for unlimited
   - Money stored as DECIMAL(8,2)
   - Boolean values stored as TINYINT(1)
   - Timestamps use DATETIME(6) for microsecond precision

---

**End of Database Schema Documentation**
