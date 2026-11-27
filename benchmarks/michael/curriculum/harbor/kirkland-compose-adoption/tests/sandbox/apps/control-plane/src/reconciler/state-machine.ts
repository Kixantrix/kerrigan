import { SCHEMA_DEPLOYMENT_STATES, type Deployment } from "../db/schema.ts";

/**
 * Deployment state machine (T23, R6 §3.2). Reconciler-owned. The canonical
 * states are the closed set persisted by the T22 schema
 * (`SCHEMA_DEPLOYMENT_STATES`): a deployment is enqueued `pending`, moves to
 * `deploying` when a runner picks it up, then settles on `succeeded` or
 * `failed`. A failed (or superseded) deployment may be `rolled_back` to its
 * previous target. R6's transient `running`/`degraded`/`rolling_back` are
 * service-status concepts; here they collapse onto the persisted set so DB and
 * reconciler never disagree.
 */
export type DeploymentState = (typeof SCHEMA_DEPLOYMENT_STATES)[number];

/** Events that drive a deployment between states. */
export type DeployEvent =
  | "start" // runner picked up the job
  | "succeed" // compose up --wait converged
  | "fail" // up failed / healthcheck timed out
  | "rollback" // begin reverting to the previous deployment
  | "supersede"; // a newer deployment replaced this one

const TABLE: Record<DeploymentState, Partial<Record<DeployEvent, DeploymentState>>> = {
  pending: { start: "deploying", fail: "failed" },
  deploying: { succeed: "succeeded", fail: "failed" },
  succeeded: { supersede: "rolled_back", rollback: "rolled_back" },
  failed: { rollback: "rolled_back", start: "deploying" },
  rolled_back: { start: "deploying" },
};

/** Terminal states: no further reconciliation drives them forward unaided. */
const TERMINAL: ReadonlySet<DeploymentState> = new Set(["succeeded", "failed", "rolled_back"]);

/**
 * Apply `event` to `current`, returning the next state. Unknown transitions are
 * a no-op (the state is unchanged) so the loop is idempotent and never throws.
 */
export function transition(current: DeploymentState, event: DeployEvent): DeploymentState {
  return TABLE[current]?.[event] ?? current;
}

/** True when an event would change the state (i.e. the transition is legal). */
export function canTransition(current: DeploymentState, event: DeployEvent): boolean {
  return transition(current, event) !== current;
}

export function isTerminal(state: DeploymentState): boolean {
  return TERMINAL.has(state);
}

/** A deployment is "active" while still being driven (pending/deploying). */
export function isActive(state: DeploymentState): boolean {
  return state === "pending" || state === "deploying";
}

/** True when this deployment can be a rollback target (it ran successfully). */
export function isRollbackTarget(d: Pick<Deployment, "state">): boolean {
  return d.state === "succeeded";
}
