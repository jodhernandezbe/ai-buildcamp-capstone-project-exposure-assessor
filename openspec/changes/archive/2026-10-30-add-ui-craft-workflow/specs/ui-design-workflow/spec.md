## Purpose

The agent-facing design layer of the frontend: a design document that any contributor (human or
agent) must follow when building UI, a self-run visual verification step, a reminder that fires
after frontend edits, and a consistency check that keeps the document aligned with the design
tokens in code.

## ADDED Requirements

### Requirement: Design document is the single source of UI intent
The frontend SHALL ship a design document at `frontend/DESIGN.md` that states the aesthetic
direction, the meaning and allowed use of every design token, the type and spacing scale,
materials and motion rules, the inventory of reusable primitives with when to use each, the
states every data panel MUST render (loading, empty, absent value, error, success), copy rules
and anti-patterns. `frontend/CLAUDE.md` SHALL reference the document and require that UI work
follow it. The document SHALL describe the UI as it exists; it SHALL NOT introduce a restyle.

#### Scenario: New panel is built
- **WHEN** a contributor adds a panel to the frontend
- **THEN** every colour, radius, font size and spacing it uses is one named in `DESIGN.md`, and it renders each state the document lists

#### Scenario: Document references
- **WHEN** `frontend/CLAUDE.md` is read
- **THEN** it names `DESIGN.md` as the design authority and the verification step as a prerequisite for finishing UI work

### Requirement: Design document and tokens stay consistent
A frontend test SHALL fail when a design token declared in the stylesheet's light theme is not
documented in `DESIGN.md`, or when `DESIGN.md` documents a token that the stylesheet does not
declare. The test SHALL run as part of the frontend `check` script.

#### Scenario: Token added without documentation
- **WHEN** a new `--token` is declared in the light theme and `DESIGN.md` is unchanged
- **THEN** the frontend check fails naming the undocumented token

#### Scenario: Token documented but removed from code
- **WHEN** `DESIGN.md` lists a token that the stylesheet no longer declares
- **THEN** the frontend check fails naming the stale token

#### Scenario: Consistent state
- **WHEN** every declared token is documented and every documented token is declared
- **THEN** the test passes

### Requirement: Visual verification command
The project SHALL provide a `/ui-check` command that, for the surface being changed, renders the
running UI in light and dark colour schemes, captures screenshots, compares what is shown against
the design document's checklist (tokens only, every required state present, colour never the only
cue, focus visible, reduced motion respected, numbers with units and "not reported" for absent
values), and runs the frontend visual and contrast tests. The command SHALL report each checklist
item as pass or fail with the evidence used, and SHALL NOT approve new screenshot references
without each new image having been looked at.

#### Scenario: Checklist item fails
- **WHEN** a screenshot shows a status conveyed by colour alone
- **THEN** the command reports that item as failed, names the component, and the UI work is not done

#### Scenario: All items pass
- **WHEN** every checklist item passes and the visual and contrast tests pass
- **THEN** the command reports the surface as verified in both colour schemes

### Requirement: Frontend edits trigger a verification reminder
After any file under the frontend source tree with a `.tsx` or `.css` extension is created or
edited by the agent, the project configuration SHALL surface a short reminder to run `/ui-check`
before the work is called done. The reminder SHALL run in well under one second, SHALL NOT start
servers, browsers or tests, and SHALL stay silent for edits outside the frontend source tree.

#### Scenario: Component edited
- **WHEN** the agent edits a `.tsx` file under `frontend/src/`
- **THEN** a one-line reminder to run `/ui-check` is shown

#### Scenario: Backend edited
- **WHEN** the agent edits a Python file under `tools/`
- **THEN** no reminder is shown

### Requirement: Design method is a reusable skill
The project SHALL provide a `ui-craft` skill that the agent loads for any frontend UI task. The
skill SHALL instruct the agent to read `DESIGN.md` first and, when a project has none, to derive
one from the existing stylesheet and components (or from a short brief for a new project) before
writing UI code; to compose from existing primitives and tokens rather than invent new ones; to
cover every required state; and to finish with the verification command. The skill SHALL be
project-agnostic: it SHALL NOT name this project's components, colours or domain.

#### Scenario: Project without a design document
- **WHEN** the skill is used in a project that has no `DESIGN.md`
- **THEN** the agent produces one from the project's stylesheet and components (or the brief) and asks for confirmation of the direction before building UI

#### Scenario: Project with a design document
- **WHEN** the skill is used here
- **THEN** the agent follows `frontend/DESIGN.md` and does not propose a new direction

### Requirement: Kit installs into another project
The skill, command, hook, document template and test templates SHALL exist as a standalone kit
outside this repository with an installer and a README. Running the installer against a target
project SHALL copy the skill and command into the target's `.claude/` folder, add the hook to the
target's project settings without removing existing hooks, and scaffold a `DESIGN.md` from the
template only when the target has none. The README SHALL explain, step by step, how to integrate
the kit into an existing project and into a new one, and how to update an installed copy.

#### Scenario: Fresh install
- **WHEN** the installer runs against a project with no `.claude/` folder and no `DESIGN.md`
- **THEN** the skill, command, hook and settings are created and a `DESIGN.md` scaffold with placeholders is written at the given frontend path

#### Scenario: Existing design document
- **WHEN** the installer runs against a project that already has a `DESIGN.md`
- **THEN** the document is left untouched and the installer says so

#### Scenario: Existing settings
- **WHEN** the target already has a `.claude/settings.json` with hooks
- **THEN** the kit's hook is added alongside them and nothing existing is removed

### Requirement: Whole-app UI audit command
The project SHALL provide a `/ui-audit` command that inventories every UI surface, renders each
in light and dark colour schemes in every reachable state, scores each surface against a fixed
set of heuristics with evidence per score, runs the static checks of the verification command
across the UI source, and writes a report with a scoreboard, ranked improvement proposals (each
with observation, evidence, smallest change, design document impact, effort and value) and a list
of surfaces or states not assessed with the reason. The audit SHALL NOT change application code.

#### Scenario: Surface scores below the maximum
- **WHEN** a surface scores 0 or 1 on a heuristic
- **THEN** the report contains a proposal for it with evidence, effort and value, and no code is changed

#### Scenario: Surface cannot be rendered
- **WHEN** a surface or state cannot be rendered with the available tools
- **THEN** the report lists it under "Not assessed" with the reason, and it is not scored as passing
