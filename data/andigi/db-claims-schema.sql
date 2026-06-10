-- claims service schema (excerpt, current production)

CREATE TABLE claims (
    id              BIGSERIAL PRIMARY KEY,
    policy_id       BIGINT NOT NULL REFERENCES policies(id),
    amount_vnd      BIGINT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'fnol',      -- fnol|triage|review|approved|paid|rejected
    triage_score    NUMERIC(5,2),
    fraud_flag      BOOLEAN NOT NULL DEFAULT FALSE,
    adjuster_id     BIGINT REFERENCES staff(id),       -- nullable: no adjuster assigned yet
    payout_due_days INTEGER NOT NULL DEFAULT 5,        -- days from approval to disbursement
    approved_at     TIMESTAMPTZ,
    paid_at         TIMESTAMPTZ
);
