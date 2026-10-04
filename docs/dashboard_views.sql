-- The two dashboard views as warehouse SQL (Snowflake dialect). In the prototype the same numbers come from
-- scripts/export_dashboard_data.py over the app database. Production would load `cases` and `case_events` from the app
-- on a schedule and point a BI tool at these views. No patient names are needed by either view.

-- cases: one row per case.   case_id, status, priority, ai_recommendation, received_at, due_at, decided_at, assignee_id, director_id
-- case_events: one row per action.   case_id, action ('approved','approved_override','pended','escalated','returned','denied'), user_id, return_reason, at

CREATE OR REPLACE VIEW exec_summary AS
SELECT
  COUNT(*)                                                         AS cases,
  COUNT_IF(ai_recommendation <> 'approve')                         AS at_risk,
  COUNT_IF(ai_recommendation =  'approve')                         AS not_at_risk,
  COUNT_IF(status = 'escalated')                                   AS with_medical_director,
  COUNT_IF(status = 'pended')                                      AS waiting_on_provider,
  COUNT_IF(status = 'denied')                                      AS denied,
  AVG(DATEDIFF('hour', received_at, decided_at))                   AS avg_hours_to_decision,
  100 * COUNT_IF(decided_at <= due_at) / NULLIF(COUNT_IF(decided_at IS NOT NULL), 0) AS pct_decided_within_deadline,
  COUNT_IF(decided_at IS NULL AND due_at < CURRENT_TIMESTAMP())    AS open_past_deadline
FROM cases;

-- Month over month: the same measures, one row per month received.
CREATE OR REPLACE VIEW exec_by_month AS
SELECT DATE_TRUNC('month', received_at) AS month, COUNT(*) AS cases,
       COUNT_IF(ai_recommendation <> 'approve') AS at_risk,
       AVG(DATEDIFF('hour', received_at, decided_at)) AS avg_hours_to_decision
FROM cases GROUP BY 1;

CREATE OR REPLACE VIEW um_by_nurse AS
SELECT u.name AS nurse, COUNT(*) AS assigned,
       COUNT_IF(c.decided_at IS NULL) AS open,
       COUNT_IF(c.decided_at IS NULL AND c.ai_recommendation <> 'approve') AS open_and_at_risk,
       COUNT_IF(c.status = 'pended') AS waiting_on_provider,
       COUNT_IF(c.status = 'escalated') AS with_director,
       COUNT_IF(c.decided_at IS NULL AND c.due_at < CURRENT_TIMESTAMP()) AS past_deadline,
       AVG(DATEDIFF('hour', c.received_at, c.decided_at)) AS avg_hours_to_decision
FROM cases c JOIN users u ON u.id = c.assignee_id GROUP BY u.name;

CREATE OR REPLACE VIEW um_unassigned AS
SELECT COUNT(*) AS waiting_at_intake, MAX(DATEDIFF('day', received_at, CURRENT_TIMESTAMP())) AS oldest_days
FROM cases WHERE assignee_id IS NULL AND decided_at IS NULL;
