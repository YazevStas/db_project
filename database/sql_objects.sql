-- Триггерная функция для проверки возраста сотрудника
CREATE OR REPLACE FUNCTION validate_staff_age()
RETURNS TRIGGER AS $$
BEGIN
    IF (EXTRACT(YEAR FROM AGE(NEW.birth_date))) < 18 THEN
        RAISE EXCEPTION 'Сотрудник должен быть старше 18 лет';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер для проверки возраста сотрудника
DROP TRIGGER IF EXISTS trg_validate_staff_age ON staff;
CREATE TRIGGER trg_validate_staff_age
BEFORE INSERT OR UPDATE ON staff
FOR EACH ROW EXECUTE FUNCTION validate_staff_age();


-- Триггерная функция для обновления статуса абонемента
CREATE OR REPLACE FUNCTION update_subscription_status()
RETURNS TRIGGER AS $$
BEGIN
    -- Не меняем статус, если он принудительно заблокирован
    IF OLD.status_name = 'blocked' AND NEW.status_name != 'blocked' THEN
        NEW.status_name := 'blocked';
        RETURN NEW;
    END IF;

    IF NEW.end_date < CURRENT_DATE THEN
        NEW.status_name := 'expired';
    ELSIF NEW.start_date > CURRENT_DATE THEN
        NEW.status_name := 'pending';
    ELSE
        NEW.status_name := 'active';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер для обновления статуса абонемента
DROP TRIGGER IF EXISTS trg_update_subscription_status ON subscriptions;
CREATE TRIGGER trg_update_subscription_status
BEFORE INSERT OR UPDATE ON subscriptions
FOR EACH ROW EXECUTE FUNCTION update_subscription_status();


-- Триггерная функция для проверки лимита участников
CREATE OR REPLACE FUNCTION check_max_participants()
RETURNS TRIGGER AS $$
DECLARE
    max_allowed INT;
    current_count INT;
BEGIN
    -- Проверяем только при добавлении подтвержденного участника
    IF NEW.status_name = 'confirmed' THEN
        SELECT max_participants INTO max_allowed FROM trainings WHERE id = NEW.training_id;
        SELECT COUNT(*) INTO current_count FROM training_participants WHERE training_id = NEW.training_id AND status_name = 'confirmed';

        IF current_count >= max_allowed THEN
            RAISE EXCEPTION 'Достигнут лимит участников для тренировки %', NEW.training_id;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер для проверки лимита участников
DROP TRIGGER IF EXISTS trg_check_max_participants ON training_participants;
CREATE TRIGGER trg_check_max_participants
BEFORE INSERT ON training_participants
FOR EACH ROW EXECUTE FUNCTION check_max_participants();


-- Представления (Views)
-- Здесь синтаксис практически совпадает, но добавим DROP VIEW IF EXISTS для надежности

DROP VIEW IF EXISTS client_full_info_view;
CREATE VIEW client_full_info_view AS
SELECT 
    c.id,
    c.last_name,
    c.first_name,
    c.middle_name,
    c.reg_date,
    c.discount,
    sub.id as subscription_id,
    sub.status_name AS subscription_status,
    sub.start_date,
    sub.end_date,
    (SELECT COUNT(*) FROM warnings w WHERE w.client_id = c.id) AS warnings_count
FROM clients c
LEFT JOIN subscriptions sub ON c.id = sub.client_id
WHERE sub.status_name = 'active' OR sub.id IS NULL;

-- !!! ДОБАВЛЕНО: Детальная информация по сотрудникам (не хватало для admin.py) !!!
DROP VIEW IF EXISTS staff_details_view;
CREATE VIEW staff_details_view AS
SELECT
    s.id,
    s.last_name,
    s.first_name,
    s.middle_name,
    s.hire_date,
    p.name AS position_name,
    p.min_salary,
    p.max_salary
FROM staff s
LEFT JOIN positions p ON s.position_id = p.id;

-- Остальные представления из вашего оригинального файла в большинстве случаев будут работать,
-- но для надежности лучше всегда проверять синтаксис на PostgreSQL.
-- Этот пример показывает, как адаптировать скрипты.

-- Индексы (синтаксис CREATE INDEX в PostgreSQL такой же)
CREATE INDEX IF NOT EXISTS idx_subscription_client_status ON subscriptions(client_id, status_name);
CREATE INDEX IF NOT EXISTS idx_subscription_dates ON subscriptions(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_training_start_time ON trainings(start_time);
CREATE INDEX IF NOT EXISTS idx_warnings_client ON warnings(client_id);