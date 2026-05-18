# Test strategy (v1)

Canonical guidance for Kerrigan's two-axis test selection.

## Axis 1: Test level ladder

| Level | Definition | Use when |
|---|---|---|
| unit | Verifies one function/module in isolation. | The AC is pure logic, data transforms, or branch behavior. |
| integration | Verifies interactions between components. | The AC depends on APIs, persistence, queues, or service boundaries. |
| smoke | Verifies one happy-path system check fast. | The AC needs proof that the deployable entry point still works. |
| e2e | Verifies an end-user flow through the real interface. | The AC is UI/browser workflow behavior or multi-step user flow. |
| scenario | Verifies real-world/platform behavior that cloud cannot fully reproduce. | The AC depends on local devices, platform hardware, or attested local execution. |

## Axis 2: Environment taxonomy

- `cloud-linux`
- `cloud-windows`
- `cloud-macos`
- `cloud-self-hosted-<name>`
- `local-attested-<class>`
- `manual-human`

## Decision tree (AC shape -> level + environment)

1. If AC is pure function/module logic -> `unit` + `cloud-linux`.
2. If AC crosses component/service boundaries -> `integration` + first cloud env matching stack (`cloud-linux`, `cloud-windows`, or `cloud-macos`).
3. If AC requires deployable happy-path confidence -> `smoke` + primary CI environment.
4. If AC is browser/UI flow and headless is valid -> `e2e` + cloud environment (usually `cloud-linux`).
5. If AC needs hardware/platform-only behavior (for example Windows NPU or iOS device) -> `scenario` + `local-attested-<class>`.
6. If AC needs direct human judgment without automatable oracle -> `scenario` + `manual-human`.

## Skill cross-references

- [test-ladder skill](../.github/skills/test-ladder/SKILL.md)
- [test-environment skill](../.github/skills/test-environment/SKILL.md)
- [e2e-test skill](../.github/skills/e2e-test/SKILL.md)
- [scenario-test skill](../.github/skills/scenario-test/SKILL.md)
