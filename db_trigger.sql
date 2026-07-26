-- PostgreSQL Trigger: Prevent UPDATE or DELETE on score_breakdown when evaluation is locked

CREATE OR REPLACE FUNCTION check_score_breakdown_immutability()
RETURNS TRIGGER AS $$
DECLARE
    eval_status VARCHAR(50);
BEGIN
    -- Look up evaluation status for the target row
    SELECT status INTO eval_status
    FROM evaluations
    WHERE id = OLD.evaluation_id;

    IF eval_status = 'locked' THEN
        RAISE EXCEPTION 'Cannot modify or delete score_breakdown rows for a locked evaluation (evaluation_id: %). Ledger is immutable.', OLD.evaluation_id
            USING ERRCODE = '23514'; -- check_violation
    END IF;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS enforce_score_breakdown_immutability ON score_breakdown;

CREATE TRIGGER enforce_score_breakdown_immutability
BEFORE UPDATE OR DELETE ON score_breakdown
FOR EACH ROW
EXECUTE FUNCTION check_score_breakdown_immutability();
