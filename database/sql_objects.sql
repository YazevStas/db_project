-- Триггеры
CREATE TRIGGER IF NOT EXISTS trg_validate_staff_age
BEFORE INSERT ON staff
FOR EACH ROW
BEGIN
    SELECT 
        CASE
            WHEN (julianday('now') - julianday(NEW.birth_date)) / 365.25 < 18 THEN
                RAISE(ABORT, 'Сотрудник должен быть старше 18 лет')
        END;
END;

CREATE TRIGGER IF NOT EXISTS trg_update_subscription_status
BEFORE INSERT OR UPDATE ON subscriptions
FOR EACH ROW
BEGIN
    UPDATE subscriptions
    SET status_name = 
        CASE 
            WHEN NEW.end_date < date('now') THEN 'expired'
            WHEN NEW.start_date > date('now') THEN 'pending'
            ELSE 'active'
        END
    WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_check_max_participants
BEFORE INSERT ON training_participants
FOR EACH ROW
BEGIN
    DECLARE current_count INT;
    DECLARE max_allowed INT;
    
    SELECT max_participants INTO max_allowed
    FROM trainings
    WHERE id = NEW.training_id;
    
    SELECT COUNT(*) INTO current_count
    FROM training_participants
    WHERE training_id = NEW.training_id
      AND status_name = 'confirmed';
    
    IF current_count >= max_allowed THEN
        RAISE(ABORT, 'Достигнут лимит участников для тренировки');
    END IF;
END;

CREATE TRIGGER IF NOT EXISTS trg_check_trainer_availability
BEFORE INSERT OR UPDATE ON trainings
FOR EACH ROW
WHEN NEW.trainer_id IS NOT NULL
BEGIN
    -- Проверка, что тренер работает в это время
    IF NOT EXISTS (
        SELECT 1 
        FROM work_schedules
        WHERE staff_id = NEW.trainer_id
          AND day_of_week = strftime('%w', NEW.start_time)
          AND NEW.start_time BETWEEN (
              datetime(NEW.start_time, 'start of day') || ' ' || start_time
          ) AND (
              datetime(NEW.start_time, 'start of day') || ' ' || end_time
          )
    ) THEN
        RAISE(ABORT, 'Тренер не работает в это время');
    END IF;
    
    -- Проверка, что тренер не занят на другой тренировке
    IF EXISTS (
        SELECT 1 
        FROM trainings
        WHERE trainer_id = NEW.trainer_id
          AND id != NEW.id
          AND (
              (NEW.start_time BETWEEN start_time AND end_time) OR
              (NEW.end_time BETWEEN start_time AND end_time) OR
              (start_time BETWEEN NEW.start_time AND NEW.end_time)
          )
    ) THEN
        RAISE(ABORT, 'Тренер уже занят на другой тренировке');
    END IF;
END;

-- Триггер для аннулирования абонемента после 3 выговоров
CREATE TRIGGER IF NOT EXISTS trg_block_subscription_after_warnings
AFTER INSERT ON warnings
FOR EACH ROW
BEGIN
    UPDATE subscriptions
    SET status_name = 'blocked'
    WHERE client_id = NEW.client_id
      AND id IN (
          SELECT id FROM subscriptions 
          WHERE client_id = NEW.client_id 
          AND status_name = 'active'
          ORDER BY end_date DESC 
          LIMIT 1
      )
      AND (SELECT COUNT(*) FROM warnings WHERE client_id = NEW.client_id) >= 3;
END;

-- Представления
CREATE VIEW IF NOT EXISTS client_full_info_view AS
SELECT 
    c.id AS client_id,
    c.last_name,
    c.first_name,
    c.middle_name,
    c.reg_date,
    c.discount,
    cc_phone.contact_value AS phone,
    cc_email.contact_value AS email,
    s.status_name AS subscription_status,
    sub.start_date,
    sub.end_date,
    (SELECT COUNT(*) FROM warnings w WHERE w.client_id = c.id) AS warnings_count
FROM clients c
LEFT JOIN client_contacts cc_phone 
    ON c.id = cc_phone.client_id AND cc_phone.contact_type = 'phone'
LEFT JOIN client_contacts cc_email 
    ON c.id = cc_email.client_id AND cc_email.contact_type = 'email'
LEFT JOIN subscriptions sub ON c.id = sub.client_id
LEFT JOIN statuses s ON sub.status_name = s.name;

CREATE VIEW IF NOT EXISTS staff_details_view AS
SELECT 
    s.id AS staff_id,
    s.last_name,
    s.first_name,
    s.middle_name,
    p.name AS position,
    sc_phone.contact_value AS phone,
    sc_email.contact_value AS email,
    sa.address_value AS address,
    se.education_level,
    se.specialty
FROM staff s
JOIN positions p ON s.position_id = p.id
LEFT JOIN staff_contacts sc_phone 
    ON s.id = sc_phone.staff_id AND sc_phone.contact_type = 'phone'
LEFT JOIN staff_contacts sc_email 
    ON s.id = sc_email.staff_id AND sc_email.contact_type = 'email'
LEFT JOIN staff_addresses sa ON s.id = sa.staff_id
LEFT JOIN staff_education se ON s.id = se.staff_id;

CREATE VIEW IF NOT EXISTS active_subscriptions_view AS
SELECT *
FROM subscriptions
WHERE status_name = 'active'
  AND date('now') BETWEEN start_date AND end_date;

CREATE VIEW IF NOT EXISTS weekly_trainings_view AS
SELECT 
    t.id AS training_id,
    s.name AS section_name,
    st.last_name AS trainer_last_name,
    t.training_type,
    t.start_time,
    t.end_time,
    COUNT(tp.client_id) AS participants_count
FROM trainings t
JOIN sections s ON t.section_id = s.id
LEFT JOIN staff st ON t.trainer_id = st.id
LEFT JOIN training_participants tp ON t.id = tp.training_id
WHERE t.start_time BETWEEN datetime('now') AND datetime('now', '+7 days')
GROUP BY t.id;

CREATE VIEW IF NOT EXISTS staff_schedule_view AS
SELECT 
    ws.staff_id,
    st.last_name || ' ' || st.first_name AS staff_name,
    ws.day_of_week,
    ws.start_time,
    ws.end_time
FROM work_schedules ws
JOIN staff st ON ws.staff_id = st.id;

CREATE VIEW IF NOT EXISTS section_attendance_view AS
SELECT 
    a.section_id,
    s.name AS section_name,
    DATE(a.entry_time) AS visit_date,
    COUNT(DISTINCT a.client_id) AS unique_visitors,
    COUNT(*) AS total_visits,
    AVG((julianday(a.exit_time) - julianday(a.entry_time)) * 24 AS avg_hours
FROM attendances a
JOIN sections s ON a.section_id = s.id
GROUP BY a.section_id, DATE(a.entry_time);

CREATE VIEW IF NOT EXISTS expired_equipment_view AS
SELECT 
    e.id,
    e.name,
    e.model,
    e.purchase_date,
    e.warranty_months,
    e.quantity,
    s.name AS section_name,
    date(e.purchase_date, '+' || e.warranty_months || ' months') AS warranty_end
FROM equipment e
JOIN sections s ON e.section_id = s.id
WHERE warranty_end < date('now');

CREATE VIEW IF NOT EXISTS expiring_contracts_view AS
SELECT 
    s.id,
    s.last_name || ' ' || s.first_name AS staff_name,
    s.hire_date,
    date(s.hire_date, '+1 year') AS contract_end,
    p.name AS position
FROM staff s
JOIN positions p ON s.position_id = p.id
WHERE contract_end BETWEEN date('now') AND date('now', '+1 month');

-- Индексы
CREATE INDEX IF NOT EXISTS idx_subscription_client_status 
ON subscriptions(client_id, status_name);

CREATE INDEX IF NOT EXISTS idx_subscription_dates 
ON subscriptions(start_date, end_date);

CREATE INDEX IF NOT EXISTS idx_training_start_time 
ON trainings(start_time);

CREATE INDEX IF NOT EXISTS idx_attendance_entry_time 
ON attendances(entry_time);

CREATE INDEX IF NOT EXISTS idx_equipment_warranty 
ON equipment(purchase_date, warranty_months);

CREATE INDEX IF NOT EXISTS idx_staff_contract_end 
ON staff(hire_date);

CREATE INDEX IF NOT EXISTS idx_participants_training_status 
ON training_participants(training_id, status_name);

CREATE INDEX IF NOT EXISTS idx_workschedule_staff_day 
ON work_schedules(staff_id, day_of_week);

CREATE INDEX IF NOT EXISTS idx_training_trainer_time 
ON trainings(trainer_id, start_time, end_time);

CREATE INDEX IF NOT EXISTS idx_warnings_client 
ON warnings(client_id);

CREATE INDEX IF NOT EXISTS idx_subscriptions_status_enddate 
ON subscriptions(status_name, end_date) 
WHERE status_name = 'active';

CREATE INDEX IF NOT EXISTS idx_trainings_section_time 
ON trainings(section_id, start_time);