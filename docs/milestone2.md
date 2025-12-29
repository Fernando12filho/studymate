## 🧱 Milestone 2 — Core Study Domain (Projects)

### Goal
Allow users to create and manage study projects (subjects, courses, exams).

### Concepts to Study
- One-to-Many relationships (User → Projects)
- SQLAlchemy `relationship()` and foreign keys
- Authorization checks

### User Stories
- As a user, I can create a study project
- As a user, I can view all my projects
- As a user, I can rename or delete a project

### Tasks
- [ ] Create `Project` model
  - id
  - name
  - description
  - user_id (foreign key)
  - created_at
- [ ] Define `User.projects` relationship
- [ ] Create project CRUD routes
- [ ] Display projects on dashboard
- [ ] Restrict access to project owner

### Done When
- Projects belong to users
- Users only see their own projects
- Full create/read/delete flow works