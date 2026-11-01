# MASTER PROJECT PROMPT: MechSense
## Industrial Predictive Maintenance & Machine Health Intelligence Platform

Act as a senior full-stack software engineer, Python backend architect, mechanical engineering domain expert, data engineer, ML engineer, and professional UI/UX designer.

Your task is to design, implement, test, and document a complete, portfolio-quality industrial machine monitoring application named **MechSense**.

Do not build a generic CRUD dashboard. Build a functional, engineering-focused software product that demonstrates real backend engineering, time-series data handling, anomaly detection, interactive analytics, database design, testing, and production-minded development.

The result must be suitable for a software developer portfolio and demonstrate my mechanical engineering background as a competitive advantage.

---

# 1. Product Vision

MechSense is an industrial machine-health monitoring platform for maintenance engineers, plant operators, and reliability engineers.

It monitors industrial equipment using vibration, temperature, rotational speed, load, and pressure readings. It stores historical sensor measurements, identifies unusual machine behavior, visualizes trends, generates alerts, and allows engineers to record maintenance activities.

The application must support both:

1. **Demo mode:** Generates realistic synthetic industrial sensor readings so anyone can explore the application without physical sensors.
2. **Data import mode:** Allows engineers to upload CSV sensor datasets, validate them, and analyze their readings.

The application should feel like a real industrial SaaS product, not a college assignment.

## Main use case

A maintenance engineer opens MechSense and sees that Industrial Pump P-101 has an abnormal increase in vibration and bearing temperature.

The engineer can open the machine's detail page, inspect recent sensor readings, view the detected anomaly and its contributing signals, acknowledge the alert, examine previous maintenance records, and create a maintenance work order.

Implement this complete workflow.

---

# 2. Mandatory Technology Stack

Use a modern, maintainable, well-supported stack. Check current official documentation and package compatibility before choosing versions. Pin compatible dependencies instead of blindly installing the newest versions.

## Frontend

- React with TypeScript
- Vite
- Tailwind CSS using a version compatible with the current shadcn/ui setup
- shadcn/ui as the primary component system
- Lucide React for consistent icons
- Recharts through shadcn/ui chart components for data visualization
- TanStack Query for API requests, caching, and query invalidation
- TanStack Table for advanced sensor and alert tables
- React Hook Form with Zod for forms and validation
- Motion for React for subtle animations and transitions
- date-fns for date formatting and time-range utilities
- Sonner for toast notifications
- React Router for application navigation

Use additional libraries only when they genuinely improve the product.

## Backend

- Python
- FastAPI
- Pydantic v2 for input/output schemas and validation
- SQLAlchemy 2.x ORM
- Alembic for database migrations
- PostgreSQL for persistent relational data
- pandas and NumPy for data processing
- scikit-learn for an optional, genuinely implemented anomaly-detection model
- pytest and HTTPX for automated backend testing

## Development and deployment

- Docker and Docker Compose
- Environment variables managed through `.env` files
- GitHub Actions for continuous integration
- Ruff for Python linting and formatting
- ESLint and Prettier for frontend code quality
- Vitest and React Testing Library for frontend tests

Use current compatible versions of these packages. Do not invent APIs or copy outdated setup commands from old tutorials.

---

# 3. Professional UI/UX Requirements

The user interface is a major part of this portfolio project. Treat visual quality and functional quality as equally important.

## Design direction

Create a premium industrial analytics application inspired by the visual quality of modern SaaS dashboards and professional monitoring tools.

The design should be clean, refined, information-dense without feeling crowded, and appropriate for industrial engineering.

Use:

- A dark charcoal or deep navy foundation with carefully chosen teal or cyan accents.
- Optional polished light mode.
- Neutral surfaces, subtle borders, restrained shadows, and consistent spacing.
- Green for healthy status, amber for warnings, and red for critical conditions.
- Excellent typography and clear visual hierarchy.
- Large, readable numerical sensor values and properly formatted engineering units.
- Attractive responsive charts and professional data tables.
- Consistent border radii and reusable layout patterns.
- Responsive desktop, tablet, and mobile experiences.

Do not make every element glow, bounce, or animate. Avoid excessive gradients, glassmorphism, random colors, giant empty cards, and decorative charts that add no useful information.

The visual result should look carefully designed by a professional product team.

## Mandatory shadcn/ui ecosystem

Use the official shadcn/ui component system as the foundation. Initialize it properly and use reusable components instead of creating every button, modal, input, tooltip, or dropdown from scratch.

Official documentation:
https://ui.shadcn.com/docs

Use shadcn/ui components and appropriate supporting libraries for:

- Sidebar navigation and responsive application shell
- Cards and metric summaries
- Buttons, inputs, selects, switches, and sliders
- Tabs and segmented controls
- Tooltips, popovers, and dropdown menus
- Dialogs, sheets, and confirmation dialogs
- Forms with validation
- Badges and status indicators
- Skeletons and loading states
- Toast notifications through Sonner
- Data tables with sorting, filtering, pagination, and row actions
- Responsive chart containers, legends, and rich tooltips
- Date-range and time-range selection
- Search and command palette
- Empty states, error messages, and confirmation feedback

## Modern supporting UI libraries

Use the following where appropriate:

**shadcn/ui Blocks**
https://ui.shadcn.com/blocks

Use official dashboard blocks as a starting point when helpful. Adapt their layout, typography, component composition, and responsiveness to MechSense instead of copying an unrelated dashboard blindly.

**Recharts**
https://recharts.org/

Use Recharts through shadcn/ui's chart infrastructure for time-series visualizations, tooltips, threshold indicators, and historical comparisons.

**TanStack Table**
https://tanstack.com/table/latest/docs/framework/react

Use it for advanced data grids with searchable columns, filters, sorting, pagination, column visibility, and row actions.

**Motion for React**
https://motion.dev/docs/react

Use subtle entrance transitions, animated status changes, layout transitions, and micro-interactions. Respect reduced-motion preferences.

**Lucide React**
https://lucide.dev/

Use consistent, meaningful icons throughout navigation, actions, sensor cards, status indicators, and alerts.

You may also explore community component registries such as https://21st.dev/ for a particularly polished component or design pattern. Review the implementation, dependencies, accessibility, and license before adopting it.

You may use Magic UI or Aceternity UI selectively if a component provides real value. Do not install many competing design systems. shadcn/ui must remain the primary source of interface components.

### Important visual rules

1. Every chart must represent real application data.
2. Every visible button must perform a meaningful action.
3. Every filter must change the displayed results.
4. Every table must have working search, sorting, and pagination where applicable.
5. Every form must validate input and display success or error feedback.
6. Every page must include proper loading, error, empty, and populated states.
7. Every modal must support its intended submit and cancel behavior.
8. The frontend must remain attractive when data is missing or an API request fails.
9. Use shared components and design tokens instead of repeating CSS.
10. Check the final layout at mobile, tablet, and desktop widths.

Build a real application, not a collection of disconnected screenshots.

---

# 4. Application Navigation

Create a persistent sidebar with the MechSense identity, clear navigation labels, active-route indicators, and collapsible behavior on smaller screens.

Include these pages:

1. Overview
2. Machines
3. Machine Details
4. Sensor Explorer
5. Anomaly Events
6. Maintenance
7. Data Import
8. Analytics
9. Settings

Add a global header containing:

- Current page title and breadcrumbs
- Machine or dataset search where appropriate
- Notification access
- Theme toggle
- User or demo profile menu
- A useful quick-action menu

Use a command palette for frequently used navigation and actions. Make sure keyboard accessibility works.

---

# 5. Overview Dashboard

The overview should be the primary landing page and must use real data from the backend.

## A. Summary metrics

Display metrics such as:

- Total registered machines
- Healthy machines
- Machines requiring attention
- Active unacknowledged alerts
- Anomalies detected over the selected period
- Average availability or uptime, only if you define and calculate it correctly

Each metric should include relevant context, such as its time range or comparison with the previous period.

Do not display fake percentage changes just to make the dashboard look impressive.

## B. Sensor trends

Create responsive time-series charts for:

- Vibration RMS in mm/s
- Temperature in °C
- Rotational speed in RPM
- Machine load in %
- Pressure in bar, when available

Allow users to choose time ranges such as the last hour, 24 hours, 7 days, and 30 days where sufficient data exists.

Support machine selection, chart tooltips, sensible axis labels, threshold indicators, and clear missing-data handling.

Allow the engineer to inspect abnormal readings directly from the chart.

## C. Machine health summary

Build a professional machine list with:

- Machine name and identifier
- Equipment type
- Current health status
- Latest reading time
- Current vibration RMS
- Current temperature
- Most recent anomaly
- Action to open details

Use status badges consistently.

## D. Recent anomalies

Create a prioritized list of recently detected events.

Each event must display:

- Severity
- Machine
- Triggering measurement
- Observed reading
- Applicable configured threshold or baseline
- Event timestamp
- Acknowledgment status

Provide a direct action to investigate the associated machine or event.

## E. Latest activity

Show actual recent events such as sensor data imports, generated anomalies, alert acknowledgments, and maintenance records.

Do not fabricate operational history.

---

# 6. Machine Management

Create a fully functional machine management module.

Users must be able to:

- View all machines.
- Search by machine name or identifier.
- Filter by equipment type and health status.
- Sort and paginate the results.
- Register a new machine.
- Edit machine details.
- View full machine details.
- View its sensor readings and anomaly history.
- View its maintenance records.
- Configure sensor warning and critical thresholds.
- Deactivate a machine without destroying its historical data.

Each machine should include:

- Unique identifier
- Name
- Equipment type
- Location or production area
- Manufacturer, if known
- Model, if known
- Installation date
- Operating status
- Description
- Configurable sensor thresholds
- Creation and update timestamps

Seed the demo application with realistic example equipment such as:

- Centrifugal Pump P-101
- Electric Motor M-204
- Industrial Fan F-301
- Compressor C-401
- Bearing Assembly B-501

These are demo assets. Clearly label generated information as simulated.

---

# 7. Machine Details and Engineering Analytics

Each machine must have a dedicated detail page.

## Machine overview

Display the asset's identity, equipment type, current status, current sensor readings, latest alert, and recent maintenance history.

## Sensor time-series explorer

Provide a chart with selectable sensor metrics and time ranges.

Support:

- Independent sensor selection
- Hover tooltips with exact timestamps
- Threshold and anomaly markers
- Historical comparisons
- Zoom or a clear time-window filter
- Missing-data indication
- Exporting the selected dataset to CSV

Do not plot unrelated sensors on one shared scale when their units are incompatible.

## Engineering context

Explain the meaning of the displayed measurements.

For example:

- Vibration RMS is an indicator of vibration severity.
- Increasing bearing temperature may indicate friction, lubrication problems, or other developing issues.
- Unexpected RPM changes may indicate operating changes or faults.
- Load and pressure provide operating context for interpreting other measurements.

These are possible interpretations, not definitive diagnoses. Make it clear that readings depend on machine type, operating conditions, sensor placement, and configured thresholds.

Do not represent generic thresholds as official safety limits or universal industrial standards.

---

# 8. Sensor Data and Simulation Engine

Implement a proper backend data pipeline for sensor readings.

A sensor reading should contain:

- Reading ID
- Machine ID
- Timestamp with timezone
- Vibration RMS
- Temperature
- RPM
- Load percentage
- Pressure, if available
- Source type, such as simulated or imported
- Relevant validation or quality metadata

Use appropriate numeric precision and database types.

## Synthetic data generation

Generate realistic, deterministic demo datasets for the application.

Requirements:

- Generate readings over at least seven historical days.
- Produce multiple readings per hour for useful chart resolution.
- Represent different machine operating ranges.
- Include normal operation, shutdown periods, gradual drift, sudden spikes, and occasional sensor noise.
- Introduce controlled abnormal events so the anomaly-detection interface can be demonstrated.
- Ensure timestamps and units are consistent.
- Use a configurable random seed so tests and demonstrations can be reproduced.

Do not simply generate independent random numbers for every metric. Model reasonable correlations and trends.

For example, a simulated bearing fault might produce rising vibration followed by rising temperature. The system should not assume that every vibration increase must cause a temperature increase.

## Interactive demo mode

Provide a user-visible action to generate additional readings.

When clicked:

1. Generate the next plausible reading for a selected machine.
2. Persist it through the backend.
3. Run the configured detection rules.
4. Create an event if the reading triggers an anomaly.
5. Update relevant dashboard queries.
6. Notify the user of the result.

Optionally provide a live-demo toggle that polls the backend at a sensible interval. Stop unnecessary polling when live mode is disabled or the page is inactive.

Protect the application against duplicate simulator processes and uncontrolled generation.

---

# 9. Anomaly Detection Engine

This is one of the most important technical features. Implement actual detection logic rather than randomly labeling readings as abnormal.

## Phase 1: Engineering thresholds

Implement a transparent, configurable rule-based detection engine.

Support per-machine warning and critical thresholds for relevant sensors.

Each detection should record:

- Machine ID
- Sensor or metric name
- Observed value
- Threshold or baseline used
- Severity
- Detection method
- Detection timestamp
- Related sensor reading
- Explanation of the trigger
- Acknowledgment state

Define consistent rules for normal, warning, and critical conditions.

Handle missing values, invalid measurements, and boundary cases deliberately.

Avoid generating a new duplicate event on every repeated reading while an equivalent condition is already active. Implement a documented deduplication or event-grouping strategy.

## Phase 2: Statistical detection

Add a statistical detector using a rolling baseline, robust statistics, or a rolling z-score.

It must:

- Require sufficient historical data.
- Handle zero variance and missing values.
- Support minimum observation requirements.
- Explain why a point was flagged.
- Distinguish a statistical anomaly from a threshold violation.

## Phase 3: Optional machine-learning model

Add scikit-learn's Isolation Forest only if it can be implemented and evaluated correctly.

Requirements:

- Use engineered numeric features from sensor readings.
- Prevent future data from leaking into a historical evaluation.
- Fit and evaluate the model on clearly documented datasets.
- Persist or reproducibly rebuild the model.
- Return documented anomaly scores and detection results.
- Record model version and parameters where relevant.
- Compare its results with the rule-based detector.
- Include tests and an evaluation report.

Do not use an untrained model and pretend it is intelligent.

Do not label an anomaly score as a probability of machine failure unless a properly trained and calibrated model supports that interpretation.

Do not claim predictive accuracy without a meaningful evaluation dataset and reported metrics.

The system should remain fully functional even if the optional ML model is disabled.

---

# 10. Anomaly Events and Alerts

Build a dedicated anomaly-management page.

Support:

- Search
- Severity filters
- Machine filters
- Sensor-type filters
- Date-range filters
- Sorting and pagination
- Event detail views
- Acknowledge and resolve actions
- Notes and investigation details
- Links to the corresponding machine and sensor reading

Use an explicit event lifecycle, such as open, acknowledged, and resolved.

Do not confuse acknowledgment with resolution.

Store acknowledgment and resolution timestamps separately and retain the event history.

Provide readable explanations such as:

"Warning: vibration RMS reached 7.2 mm/s against the configured warning threshold of 4.5 mm/s."

Those numbers are illustrative; the actual values must come from the persisted reading and the machine's configuration.

Show warning and critical states prominently but avoid unnecessary alarm animations.

---

# 11. Maintenance Management

Create a functional maintenance module.

Allow a user to:

- Create a maintenance record.
- Schedule maintenance.
- Edit maintenance details.
- Mark a work order as in progress or completed.
- Add inspection notes.
- Associate maintenance with a machine.
- Record maintenance type, priority, technician, and dates.
- Link the work order to one or more relevant anomaly events.

Suggested maintenance fields:

- Work order ID
- Machine ID
- Title
- Description
- Maintenance type
- Priority
- Status
- Scheduled date
- Start and completion timestamps
- Technician
- Findings
- Actions taken

Include overdue work orders and upcoming maintenance on the dashboard when appropriate.

Use server-side validation and clear form feedback. Do not calculate or display maintenance savings unless the data and calculation actually support it.

---

# 12. CSV Import and Data Quality

Create an end-to-end CSV upload flow.

The user should be able to:

1. Select a CSV file.
2. Preview the headers and sample rows.
3. Map input columns to supported sensor fields if necessary.
4. Validate timestamps, required columns, numeric fields, ranges, and missing values.
5. Review validation errors before importing.
6. Import valid data.
7. View how many records were accepted or rejected.
8. See an import-history record.
9. Open charts and anomaly results for the imported machine readings.
10. Export filtered sensor readings and events to CSV.

Requirements:

- Set reasonable upload size and row-count limits.
- Validate content rather than trusting filenames or MIME types.
- Handle malformed timestamps and duplicate records.
- Return actionable validation errors with row numbers.
- Avoid partial imports when an atomic transaction is required.
- Use transactions or staging tables where appropriate.
- Do not crash when a CSV file is empty or incorrectly formatted.

Include a downloadable sample CSV and clear schema instructions.

Support timezone-aware timestamps and document the import convention.

---

# 13. Backend API Design

Use a versioned REST API under `/api/v1`.

Create logically organized routers for the following domains:

- Health
- Dashboard
- Machines
- Sensor readings
- Anomaly events
- Maintenance
- Data imports
- Analytics
- Simulation
- Configuration

Include endpoints equivalent to:

GET /health

GET /api/v1/dashboard/summary

GET /api/v1/machines

POST /api/v1/machines

GET /api/v1/machines/{machine_id}

PATCH /api/v1/machines/{machine_id}

GET /api/v1/machines/{machine_id}/readings

GET /api/v1/readings

GET /api/v1/anomalies

GET /api/v1/anomalies/{anomaly_id}

POST /api/v1/anomalies/{anomaly_id}/acknowledge

POST /api/v1/anomalies/{anomaly_id}/resolve

GET /api/v1/maintenance

POST /api/v1/maintenance

PATCH /api/v1/maintenance/{work_order_id}

POST /api/v1/imports/csv

GET /api/v1/analytics/trends

POST /api/v1/simulation/step

POST /api/v1/demo/generate

These paths are a starting contract. Adjust them if needed for consistent REST semantics and document the final API.

## API requirements

- Use Pydantic request and response schemas.
- Use proper HTTP status codes.
- Provide consistent error responses.
- Add pagination for potentially large results.
- Support date and machine filters for sensor data.
- Enforce configurable maximum page sizes.
- Avoid N+1 query patterns.
- Use database transactions where appropriate.
- Validate machine IDs and related records.
- Use timezone-aware timestamps.
- Do not expose database models directly as API contracts.
- Configure CORS through environment variables.
- Provide OpenAPI documentation.
- Add structured server-side logging.
- Never expose credentials, stack traces, or private environment variables in client-facing errors.

Organize the backend into routes, schemas, models, services, repositories when useful, configuration, database setup, and tests.

Keep sensor processing and anomaly-detection logic outside route handlers so it can be tested independently.

---

# 14. Database Design

Create proper SQLAlchemy models and Alembic migrations.

At minimum, model:

1. Machine
2. SensorReading
3. AnomalyEvent
4. MaintenanceWorkOrder
5. DataImportJob
6. DetectionRun or ModelVersion where appropriate

Create appropriate relationships, foreign keys, indexes, uniqueness constraints, and deletion rules.

Consider indexes for:

- Machine ID and timestamp on sensor readings
- Machine ID and event creation time on anomalies
- Event status and severity
- Maintenance status and scheduled date

Keep sensor measurement history when a machine is deactivated.

Avoid unnecessary data duplication, unbounded queries, and overly complicated abstraction layers.

Create a deterministic seed command that generates demo machines, readings, anomaly events, and maintenance records.

The seed command should be safe to rerun, without duplicating the entire dataset.

Document any PostgreSQL-specific design choices.

---

# 15. Frontend Engineering

Use a maintainable TypeScript structure.

Create reusable modules for:

- API client
- Typed API responses
- Query keys and API hooks
- Shared chart components
- Metric cards
- Machine status badges
- Reusable data tables
- Loading and error states
- Form schemas
- Date-range filtering
- Formatting dates, values, and engineering units

Use TanStack Query to synchronize frontend state with persisted backend data.

After a mutation, update or invalidate relevant queries so the user sees current information.

Do not store the same server state in several unrelated state managers.

Keep API base URLs in environment variables.

Do not hardcode application data into the dashboard components. Demo data must originate from the backend seed or simulator.

Implement:

- Responsive navigation
- Search and filter state
- URL query parameters for useful filterable pages where practical
- Forms with accessible labels
- Error and empty states
- Optimistic updates only when rollback and error handling are implemented
- Clean component boundaries
- Shared design tokens
- Accessible keyboard focus and contrast

Use realistic engineering units and consistent number formatting.

---

# 16. Security and Reliability

Implement sensible protections even for a portfolio application:

- Parameterized database operations through the ORM
- Strict request validation
- Safe CSV parsing
- File-upload limits
- CORS restrictions
- Safe exception handling
- No secrets committed to source control
- Separate environment examples from real credentials
- Consistent HTTP error handling
- Input length and range validation
- Appropriate rate limits or abuse protection for public endpoints
- Safe resource and query limits

Do not present the demo application as certified industrial control software.

It is a monitoring and decision-support prototype, not a replacement for machinery interlocks, safety systems, certified condition-monitoring equipment, or qualified maintenance decisions.

If public authentication is included, implement it properly. Never create decorative login screens that do not actually protect the underlying resources.

---

# 17. Testing Requirements

Tests are mandatory.

## Backend tests

Use pytest and HTTPX.

Test:

- Health endpoint
- Machine CRUD
- Sensor-reading queries and date filtering
- Invalid input handling
- Threshold boundary conditions
- Warning and critical events
- Statistical anomaly detection
- Duplicate-event suppression
- Anomaly acknowledgment and resolution
- Maintenance workflows
- CSV import validation
- Database transaction behavior
- Dashboard aggregation correctness
- Simulation behavior
- Authorization if authentication is implemented

Use an isolated test database and deterministic fixtures.

Do not run destructive tests against the development or production database.

## Frontend tests

Use Vitest and React Testing Library.

Test:

- Dashboard loading and failure states
- Metric rendering from API responses
- Search and filter behavior
- Machine forms and validation
- Anomaly action flows
- Maintenance forms
- CSV-import feedback
- Key interactions in tables and dialogs

## End-to-end tests

If practical, use Playwright to verify the critical workflow:

1. Open the demo application.
2. Generate sample readings.
3. Navigate to a machine.
4. Trigger or inspect an anomaly.
5. Acknowledge the event.
6. Create a maintenance work order.
7. Confirm the result persists after navigating away and returning.

Fix failed tests rather than disabling or weakening them to obtain a green result.

---

# 18. Deployment and DevOps

Provide a working local development environment and deployment instructions.

Include:

- `docker-compose.yml`
- Frontend Dockerfile if useful for the deployment strategy
- Backend Dockerfile
- PostgreSQL service with persistent development storage
- `.env.example`
- Database migration commands
- Demo-data seed command
- Backend health check
- Frontend build command
- Lint and test commands
- GitHub Actions workflow for automated checks

Ensure startup order and database readiness are handled properly.

Never copy a development secret into the repository.

Document a realistic deployment path:

- Frontend: Vercel or another suitable static/frontend host
- Backend: Render, Fly.io, or another suitable Python host
- PostgreSQL: a managed PostgreSQL provider

Use the actual deployment platform's current setup instructions when implementing deployment configuration. Do not claim that a deployment has succeeded unless it has actually been tested.

The app should work locally even before cloud deployment.

---

# 19. Required Project Structure

Organize the project as a small monorepo:

mechsense/
  frontend/
    src/
      components/
      features/
        dashboard/
        machines/
        sensors/
        anomalies/
        maintenance/
        imports/
        analytics/
      hooks/
      lib/
      routes/
      types/
      test/
    public/
    Dockerfile
    package.json

  backend/
    app/
      api/
        v1/
      core/
      db/
      models/
      schemas/
      services/
      repositories/
      detection/
      simulation/
      utils/
      main.py
    migrations/
    tests/
    scripts/
    Dockerfile
    pyproject.toml

  docs/
    architecture.md
    api.md
    data-dictionary.md
    anomaly-detection.md
    deployment.md

  docker-compose.yml
  .env.example
  .gitignore
  README.md

Adjust this structure if a simpler organization is better, but retain clear separation between the frontend, backend, and engineering logic.

Avoid creating dozens of empty files just to match this structure.

---

# 20. README and Portfolio Presentation

Write a professional README that explains:

- What MechSense does
- The engineering problem it addresses
- Its main features
- Screenshots or GIFs of the working application
- Technology stack
- Architecture diagram
- Database entities and relationships
- Sensor data model and units
- Anomaly-detection methodology
- How to run it locally
- How to run tests
- API documentation
- CSV format and sample dataset
- Docker setup
- Deployment steps
- Limitations and future improvements

Include a section titled "Engineering Decisions" explaining why the system uses a particular database model, detection method, API design, and frontend data-fetching strategy.

Include a short demo walkthrough suitable for a recruiter.

Do not fill the README with invented benchmarks, fake evaluation metrics, imaginary customers, or unsupported claims.

---

# 21. Implementation Plan

Build the application incrementally, with a working result at each stage.

## Phase 1 — Inspect and plan

Inspect the current repository, installed tools, available runtimes, and existing code before making changes.

If a project already exists, preserve useful work and avoid overwriting unrelated files.

Produce a short implementation plan, a dependency list, and the intended architecture. Identify any incompatible packages or system requirements before adding dependencies.

Then begin implementation. Do not stop after writing the plan.

## Phase 2 — Working backend foundation

Implement database configuration, models, migrations, seed data, machine APIs, sensor-reading APIs, and tests.

Verify that the API starts and that its endpoints work.

## Phase 3 — Visual frontend foundation

Initialize the React, TypeScript, Tailwind CSS, and shadcn/ui setup.

Implement the app shell, responsive sidebar, design tokens, navigation, and polished dashboard structure.

Use realistic loading skeletons and error states while connecting actual API endpoints.

## Phase 4 — End-to-end product features

Implement machine details, charts, anomaly events, maintenance management, CSV import, analytics, and simulation.

Every major feature must connect to the backend and persist its changes.

## Phase 5 — Engineering intelligence

Implement threshold-based detection first. Add statistical detection, followed by optional machine learning when the first two layers are correct and tested.

Document the actual behavior of each detector.

## Phase 6 — Quality and deployment

Run frontend and backend tests, formatters, linters, builds, and migration checks.

Fix issues found by those commands. Verify that local setup works from a clean environment and write the final documentation.

Do not claim tests or builds passed unless you actually ran them successfully.

---

# 22. Final Acceptance Criteria

The project is complete only when the following are satisfied:

- The React frontend runs and can communicate with the FastAPI backend.
- PostgreSQL persists machines, readings, anomaly events, and maintenance records.
- The seed command generates useful and reproducible demo data.
- The dashboard displays real aggregated backend data.
- Sensor charts show persisted historical data with correct units and timestamps.
- Machine creation, editing, and viewing work end to end.
- Threshold and statistical anomaly detection work and have tests.
- Anomaly acknowledgment and resolution persist in the database.
- Maintenance work orders can be created and updated.
- CSV import validates data and reports useful errors.
- Demo simulation can create new readings and trigger detection.
- The UI is polished, responsive, accessible, and built with shadcn/ui and suitable supporting libraries.
- Loading, empty, error, and success states are handled.
- Automated tests cover key backend and frontend behaviors.
- Docker-based local setup and database migrations are documented.
- A complete README and architecture documentation exist.
- No core workflow relies on fake frontend state or decorative nonfunctional buttons.

## Final instructions to the AI coding agent

Prioritize correctness, working features, visual quality, and maintainable code.

Do not build the whole application as one huge component.

Do not create mock API responses and leave them disconnected from the real backend.

Do not randomly generate anomaly statuses in frontend components.

Do not add machine-learning libraries just for appearances.

Do not introduce unnecessary microservices, Kubernetes, Kafka, or other infrastructure that the current project does not need.

Use small, meaningful modules. Keep the architecture understandable enough for a junior developer to explain confidently in an interview.

If an advanced feature would compromise the reliability of the core application, finish the core workflow first and clearly document the advanced feature as a future extension.

When finished, report:

1. What has actually been implemented.
2. The final project structure.
3. Commands to install, configure, and run everything.
4. Commands to run migrations, seed data, and execute tests.
5. Any known limitations or unfinished features.
6. What I should demonstrate to a recruiter.
7. Which engineering decisions I should be able to explain in an interview.

