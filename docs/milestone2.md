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
- [ x ] Create `Project` model
  - id
  - name
  - description
  - user_id (foreign key)
  - created_at
- [ x ] Define `User.projects` relationship
- [ x ] Create project CRUD routes
- [ x ] Display projects on dashboard
- [ x ] Restrict access to project owner
- [ x ] Create delete Button 
(Both either on the card at the dashboard page and at the topic page itself)
- [ x ] Make sure they are working

### Done When
- Projects belong to users
- Users only see their own projects
- Full create/read/delete flow works





------------------------------
TO WORK LATER:
- [ ] Create edit button
- [ ] When loggin out, and go to register page, it appears all past request allerts, example: topic deleted successfully