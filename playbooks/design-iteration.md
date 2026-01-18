# Design System Iteration Playbook

## Overview

This playbook guides users and the Design Agent through iterative refinement of design systems. It covers the complete workflow from initial creation to final approval.

## Roles

- **User**: Product designer, developer, or stakeholder providing requirements and feedback
- **Design Agent**: AI agent creating and refining design systems
- **SWE Agent**: (Later phase) Implements the approved design system

## Workflow Scenarios

### Scenario 1: Initial Design Direction

**Goal**: Establish the design philosophy and overall aesthetic direction.

#### Steps

1. **User creates issue** with design requirements
   - Add label: `role:design`
   - Include: Target users, use cases, brand guidelines, constraints
   - Example: "Need design system for developer dashboard with technical aesthetic"

2. **Design Agent proposes 3 options** with visual examples
   - Creates 3 design philosophy proposals
   - Each includes: Color palette, typography, example components
   - Commits to branch, comments with preview links

3. **User provides feedback**
   - Reviews proposals in playground comparison mode
   - Creates feedback file in `feedback/design-feedback/`
   - Feedback type: `philosophy`
   - Example: "Technical Precision aligns best, but prefer less saturated greens"

4. **Design Agent refines**
   - Reads feedback file
   - Adjusts selected philosophy
   - Updates proposal with changes
   - Updates feedback file with response

5. **Repeat steps 3-4 until approved**
   - Usually 2-3 iterations
   - User sets `status: "approved"` in feedback file

6. **Design Agent creates full system**
   - Builds complete token set
   - Creates all required components
   - Generates implementations
   - Builds interactive playground

#### Success Criteria

- User approves design philosophy within 5 iterations
- Design direction clearly documented
- Token foundation established
- Example components demonstrate philosophy

#### Time Estimate

- First proposal: 2-4 hours (agent work)
- Each iteration: 1-2 hours (agent work) + user review time
- Total: 1-2 days to establish direction

---

### Scenario 2: Component Refinement

**Goal**: Iterate on specific components based on real usage and testing.

#### Steps

1. **Design Agent creates initial component set**
   - Implements all required components
   - Deploys to playground
   - Notifies user components are ready for testing

2. **User tests components in playground**
   - Uses components in realistic scenarios
   - Tests different states and variants
   - Identifies issues and improvements

3. **User provides feedback**
   - Creates feedback file per component (or grouped)
   - Feedback type: `refinement`
   - Example: "Button padding too small, feels cramped"
   - Includes specific requests and rationale

4. **Design Agent iterates on components**
   - Processes all feedback files
   - Makes requested changes
   - Validates accessibility maintained
   - Updates feedback files with responses

5. **Updated components deployed to playground**
   - Agent rebuilds playground
   - Commits changes
   - Notifies user of updates

6. **Repeat steps 2-5 per component**
   - Each component may need multiple iterations
   - Can work on multiple components in parallel
   - Track progress in feedback files

7. **User approves components**
   - Sets `status: "approved"` in feedback files
   - All components meet requirements
   - Ready for implementation

#### Success Criteria

- Each component tested in realistic scenarios
- All feedback addressed or explained
- Accessibility validated for every component
- User approves all components within 3-5 iterations per component

#### Time Estimate

- Initial component set: 4-8 hours (agent work)
- Per iteration cycle: 2-4 hours (agent) + user testing time
- Per component: 1-3 iterations average
- Total: 3-7 days for complete component library

---

### Scenario 3: Token Adjustment

**Goal**: Fine-tune design tokens (colors, spacing, typography) based on usage.

#### Steps

1. **User requests token change**
   - Creates feedback file
   - Feedback type: `token_adjustment`
   - Specifies token name, current value, requested value
   - Example: "color.primary too bright, reduce saturation 20%"

2. **Design Agent analyzes impact**
   - Identifies all components using the token
   - Checks for accessibility implications
   - Creates before/after examples
   - Lists all affected components

3. **Design Agent shows impact**
   - Updates feedback file with impact analysis
   - Shows contrast ratios for color changes
   - Lists all components that will change
   - Sets `status: "needs_clarification"` if concerns exist

4. **User reviews impact**
   - Checks all affected components
   - Verifies acceptable changes
   - Approves or requests adjustments
   - Updates feedback file

5. **Design Agent updates tokens**
   - Makes approved changes
   - Regenerates all affected components
   - Validates accessibility maintained
   - Updates documentation

6. **Agent updates feedback file**
   - Documents what changed
   - Includes validation results
   - Sets `status: "implemented"`

7. **User confirms in playground**
   - Tests updated components
   - Verifies changes meet expectations
   - Sets `status: "approved"` or requests more changes

#### Success Criteria

- Token change maintains accessibility standards
- Impact on all components acceptable
- Semantic meaning of token preserved
- User approves change within 2-3 iterations

#### Time Estimate

- Per token change: 1-2 hours (agent work)
- Multiple tokens can be adjusted together
- Total: 1-2 days for major token adjustments

---

## Playground Features

### Interactive Token Editor

**Purpose**: Allow users to adjust tokens and see live previews.

**How to use**:
1. Open playground token editor
2. Select token to adjust (color picker, slider, or input)
3. See instant preview across all components
4. Export adjusted token set to feedback file
5. Submit feedback for agent to validate and implement

**Features**:
- Color picker with accessibility validation
- Spacing sliders with pixel values
- Typography controls
- Before/after comparison
- Export to YAML feedback format

### Annotation System

**Purpose**: Click-to-comment on any component in playground.

**How to use**:
1. Click on any component in playground
2. Annotation form appears
3. Enter feedback (text, rating, suggestions)
4. Optional: Attach screenshot or sketch
5. Save annotation
6. Export all annotations to feedback file

**Features**:
- Click-to-annotate any component
- Rate components (like/dislike/neutral)
- Natural language suggestions
- Screenshot capture
- Bulk export to feedback YAML

### Comparison Mode

**Purpose**: View multiple design philosophies or versions side-by-side.

**How to use**:
1. Select design systems/versions to compare
2. View side-by-side or toggle between them
3. Vote on preferred option
4. Add comments explaining preference
5. Export comparison results

**Features**:
- Side-by-side layout
- Toggle between versions
- A/B testing with sample data
- Vote on preferences
- Keyboard navigation

---

## Feedback File Workflow

### Creating Feedback

1. **Copy template**:
   ```bash
   cp feedback/design-feedback/TEMPLATE.yaml \
      feedback/design-feedback/2026-01-17-myproject-button-feedback.yaml
   ```

2. **Fill in required fields**:
   - timestamp, project, design_system, component, feedback_type
   - user_comment (be specific!)
   - current_state
   - requested_change

3. **Commit and push**:
   ```bash
   git add feedback/design-feedback/
   git commit -m "Feedback: Button padding too small"
   git push
   ```

4. **Notify Design Agent**: Comment on issue/PR

### Processing Feedback (Design Agent)

1. **Find new feedback**:
   ```bash
   grep -l 'status: "new"' feedback/design-feedback/*.yaml
   ```

2. **Read and analyze feedback**

3. **Make changes** to design system

4. **Update feedback file**:
   - Add detailed `agent_response`
   - Increment `iteration` number
   - Change `status` to "implemented" or "needs_clarification"
   - Add validation results

5. **Commit changes**:
   ```bash
   git add design-system/ feedback/design-feedback/
   git commit -m "Implemented feedback: Increased button padding"
   git push
   ```

6. **Notify user**: Comment on issue/PR with summary

### Approving Changes (User)

1. **Review changes** in playground

2. **Test thoroughly**

3. **Update feedback file**:
   ```yaml
   status: "approved"
   notes: |
     Tested all button variants. Changes look good!
   ```

4. **Commit approval**:
   ```bash
   git add feedback/design-feedback/
   git commit -m "Approved: Button padding changes"
   git push
   ```

---

## Best Practices

### For Users

**Do**:
- Be specific in feedback ("increase padding by 8px" not "make it bigger")
- Explain your reasoning ("for better touch targets")
- Test in realistic scenarios
- Provide context about use cases
- Respond to agent questions promptly

**Don't**:
- Give vague feedback ("make it look better")
- Request conflicting changes simultaneously
- Skip testing before approval
- Ignore accessibility concerns
- Change requirements mid-iteration without discussion

### For Design Agent

**Do**:
- Respond to all feedback within 24 hours (if possible)
- Explain your reasoning for design decisions
- Show impact analysis for token changes
- Validate accessibility for every change
- Ask questions when feedback is unclear
- Track iterations meticulously

**Don't**:
- Make changes that break accessibility
- Ignore user preferences without explanation
- Forget to update feedback files with responses
- Skip impact analysis for token changes
- Assume what user means - ask questions

---

## Common Issues and Solutions

### Issue: Feedback is vague

**Solution**: Design Agent sets `status: "needs_clarification"` and asks specific questions:
```yaml
agent_response: |
  Could you clarify what aspect should be "better"? For example:
  - Color (which specific colors?)
  - Spacing (more/less padding/margin?)
  - Typography (size, weight, font family?)
  - Layout (arrangement, alignment?)
  
  Please update this feedback with more specific requests.
```

### Issue: Requested change breaks accessibility

**Solution**: Design Agent explains constraint and proposes alternative:
```yaml
agent_response: |
  I understand you'd like a lighter gray for the text. However, 
  #999999 on white background has a contrast ratio of 2.85:1, 
  which fails WCAG AA (requires 4.5:1).
  
  Alternative options that maintain accessibility:
  1. #767676 (4.5:1 - meets AA)
  2. #6B6B6B (5.0:1 - meets AA comfortably)
  
  Could you review these options and let me know which works best?
```

### Issue: Change impacts many components

**Solution**: Design Agent provides comprehensive impact analysis:
```yaml
agent_response: |
  This token change will affect 14 components:
  
  **Major impact** (visual change obvious):
  - Primary buttons (all variants)
  - Links in body text
  - Selected state in navigation
  
  **Minor impact** (subtle change):
  - Badge backgrounds
  - Focus rings
  - Status indicators
  
  All changes maintain accessibility. Would you like to see 
  before/after screenshots of the major impacts?
```

### Issue: Multiple iterations not converging

**Solution**: Schedule synchronous discussion:
```yaml
agent_response: |
  We've gone through 5 iterations on this component and seem to 
  be circling different preferences. 
  
  Could we schedule a quick video call to discuss? This might help us:
  1. Understand the core requirements better
  2. Explore options interactively
  3. Reach consensus faster
  
  Or, could you provide a visual reference (sketch, screenshot from 
  another app) showing what you have in mind?
```

---

## Iteration Metrics

Track these metrics to improve the process:

- **Iterations to approval**: Target 3-5 per component
- **Response time**: Agent response within 24 hours
- **Feedback quality**: Specific vs vague (aim for >80% specific)
- **Accessibility issues**: Zero accessibility regressions
- **User satisfaction**: Survey after completion

---

## Examples

See these example feedback files for patterns:

- `feedback/design-feedback/2026-01-17-task-dashboard-button-feedback.yaml` - Component refinement
- `feedback/design-feedback/2026-01-17-wellness-app-philosophy-feedback.yaml` - Philosophy selection (to be created)
- `feedback/design-feedback/2026-01-17-admin-portal-color-feedback.yaml` - Token adjustment (to be created)

---

## Related Documentation

- `feedback/design-feedback/README.md` - Feedback system overview
- `specs/kerrigan/agents/design/spec.md` - Design Agent specification
- `.github/agents/role.design.md` - Design Agent prompt
- `feedback/design-feedback/TEMPLATE.yaml` - Feedback template

---

## Quick Reference

| Task | Command/Location |
|------|------------------|
| Create feedback | `cp feedback/design-feedback/TEMPLATE.yaml feedback/design-feedback/YYYY-MM-DD-project-component.yaml` |
| Find new feedback | `grep -l 'status: "new"' feedback/design-feedback/*.yaml` |
| View playground | `open design-system/playground/index.html` |
| Export annotations | Playground UI → Export button |
| Approve changes | Set `status: "approved"` in feedback file |
| Request clarification | Set `status: "needs_clarification"` with questions |

---

## Success Stories

(To be filled in as teams use this workflow)

- **Project**: Task Dashboard
- **Components**: 12 components
- **Iterations**: Average 2.5 per component
- **Time**: 5 days from start to approval
- **Outcome**: Approved design system with 95% user satisfaction
