## Why

Workspace feedback issues now exist, but they are still mostly isolated inside the workspace detail page. To become useful as a project workflow loop, issues need to connect to resources, action planning, notifications, AI context, global search, and resource-level entry points.

## What Changes

- Add optional resource references to workspace issues so feedback can point to a paper, research direction, writing draft, chat context, or workspace section.
- Add project-space detail tabs for overview, issues, resources, assistant, and activity so the growing workspace surface stays navigable.
- Surface high-priority open issues in workspace next actions and cross-module action center.
- Create in-app notifications for workspace issue creation, comments, closing, and reopening.
- Include open issue context in the workspace AI assistant prompt and references.
- Allow issue search from the global command palette and navigate directly to a workspace issue.
- Add "提 Issue" entry points on paper detail, research project, and writing pages that can create workspace-scoped issues tied to the current resource.

## Capabilities

### New Capabilities

### Modified Capabilities

- `workspace-feedback-issues`: Extend workspace issues with resource references, direct issue links, resource-page creation entry points, and tabbed project-space UI.
- `workspace-ai-assistant`: Include open feedback issues in workspace assistant context and references.
- `cross-module-action-center`: Include high-priority open workspace issues in next-action recommendations.
- `notification-digest-center`: Add in-app workspace issue notifications for relevant members.
- `global-command-palette`: Search and navigate workspace issues from the command palette.

## Impact

- Backend workspace issue models, migration, service methods, API schemas, search/list responses, action service, notification writes, and assistant context builder.
- Frontend workspace detail layout, issue drawer deep-link support, resource-level issue creation UI, command palette search, and action center display.
- Backend and frontend contract tests.
