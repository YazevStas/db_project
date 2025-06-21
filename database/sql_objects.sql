CREATE OR REPLACE FUNCTION validate_staff_age()
RETURNS TRIGGER AS $$
BEGIN
    IF (EXTRACT(YEAR FROM AGE(NEW.birth_date))) < 18 THEN
        RAISE EXCEPTION 'Сотрудник должен быть старше 18 лет';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_validate_staff_age ON staff;
CREATE TRIGGER trg_validate_staff_age
BEFORE INSERT OR UPDATE ON staff
FOR EACH ROW EXECUTE FUNCTION validate_staff_age();


CREATE OR REPLACE FUNCTION update_client_subscription_status()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD IS NOT NULL AND OLD.status_name = 'blocked' AND NEW.status_name != 'blocked' THEN
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

DROP TRIGGER IF EXISTS trg_update_subscription_status ON client_subscriptions;
CREATE TRIGGER trg_update_subscription_status
BEFORE INSERT OR UPDATE ON client_subscriptions
FOR EACH ROW EXECUTE FUNCTION update_client_subscription_status();


CREATE OR REPLACE FUNCTION check_max_participants()
RETURNS TRIGGER AS $$
DECLARE
    max_allowed INT;
    current_count INT;
BEGIN
    IF NEW.status_name = 'confirmed' THEN
        SELECT t.max_participants INTO max_allowed FROM trainings t WHERE t.id = NEW.training_id;
        SELECT COUNT(*) INTO current_count FROM training_participants tp WHERE tp.training_id = NEW.training_id AND tp.status_name = 'confirmed';

        IF current_count >= max_allowed THEN
            RAISE EXCEPTION 'Достигнут лимит участников для тренировки %', NEW.training_id;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_check_max_participants ON training_participants;
CREATE TRIGGER trg_check_max_participants
BEFORE INSERT ON training_participants
FOR EACH ROW EXECUTE FUNCTION check_max_participants();


DROP VIEW IF EXISTS client_full_info_view CASCADE;
CREATE VIEW client_full_info_view AS
SELECT
    c.id as client_id,
    c.last_name,
    c.first_name,
    c.middle_name,
    c.reg_date,
    c.discount,
    cs.id as subscription_id,
    st.name as subscription_name,
    cs.status_name AS subscription_status,
    cs.start_date,
    cs.end_date,
    (SELECT COUNT(*) FROM warnings w WHERE w.client_id = c.id) AS warnings_count
FROM clients c
LEFT JOIN client_subscriptions cs ON c.id = cs.client_id AND cs.status_name = 'active'
LEFT JOIN subscription_types st ON cs.subscription_type_id = st.id;


DROP VIEW IF EXISTS staff_details_view CASCADE;
CREATE VIEW staff_details_view AS
SELECT
    s.id as staff_id,
    s.last_name,
    s.first_name,
    s.middle_name,
    s.hire_date,
    p.name AS position
FROM staff s
LEFT JOIN positions p ON s.position_id = p.id;


DROP INDEX IF EXISTS idx_subscription_client_status;
DROP INDEX IF EXISTS idx_subscription_dates;

CREATE INDEX IF NOT EXISTS idx_client_subscription_client_status ON client_subscriptions(client_id, status_name);
CREATE INDEX IF NOT EXISTS idx_client_subscription_dates ON client_subscriptions(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_training_start_time ON trainings(start_time);
CREATE INDEX IF NOT EXISTS idx_warnings_client ON warnings(client_id);