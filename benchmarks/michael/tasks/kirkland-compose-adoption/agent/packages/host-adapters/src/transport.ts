/**
 * TRANSPORT abstraction for the {@link DockerComposeAdapter} (T21).
 *
 * `docker --context <name>` makes LOCAL and SSH execution byte-identical: for
 * local, the context is `default` (the Unix socket); for remote, it is an
 * `ssh://` context Docker tunnels transparently. The ONLY thing that differs is
 * *where compiled project files land*. A transport therefore has two jobs: stage
 * files, and run `docker` with the right context.
 *
 * (This slice keeps the contract only; the spawning Local/SSH transports are
 * out of scope. Tests and fixtures inject a scripted transport.)
 */

export interface ExecResult {
  code: number;
  stdout: string;
  stderr: string;
}

/** Files a deployment needs on the host before `docker compose` can run. */
export interface ProjectFiles {
  /** Rendered `docker-compose.yml`. */
  compose: string;
  /** Rendered `.env` (secret material; never logged). */
  env?: string;
}

/** What every transport must provide, identical for local and SSH. */
export interface ComposeTransport {
  readonly kind: "local" | "ssh";
  /** Docker context name; `default` for local. */
  readonly context: string;
  /** Absolute project dir on the execution host (`--project-directory`). */
  projectDir(project: string): string;
  /** Stage compose/.env into the project dir; idempotent. */
  stage(project: string, files: ProjectFiles): Promise<void>;
  /** Run `docker --context <ctx> <args>` and buffer the result. */
  docker(args: string[], env?: Record<string, string | undefined>): Promise<ExecResult>;
}
