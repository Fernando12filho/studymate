## 🧱 Milestone 3 — Study Content Ingestion

### Goal
Enable users to add learning material to projects.

### User Stories
- As a user, I can add notes or pasted content
- As a user, I can view all content within a project
- As a user, I can open individual content items

### Data Model
`Content` (or `Document`)
- id
- title
- raw_text
- project_id
- created_at

### Tasks
- [ ] Create Content model
- [ ] Project → Content relationship
- [ ] Add content creation form (textarea)
- [ ] List content per project
- [ ] Create content detail page

### Done When
- Projects contain multiple content items
- Content is stored and retrievable
- Database structure is clean and normalized