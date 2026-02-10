# GitHub Issues: StudyMate → NotebookLM-like Platform

This document contains all issues needed to transform StudyMate into a NotebookLM-like platform with RAG capabilities.

---

## PHASE 1: Git Version Control & Dependencies ✅

### Issue #1: Verify Git Repository Setup
**Labels:** `setup` `priority:high`

**Description:**
Ensure the project has proper git version control with `.gitignore` configured to exclude sensitive files and build artifacts.

**Tasks:**
- [ ] Verify `.gitignore` includes:
  - `instance/` directory (contains database and uploads)
  - `*.pyc`, `__pycache__/`
  - `.env` file (secrets)
  - `venv/` or virtual environment folders
- [ ] Check `.env.example` exists with template environment variables
- [ ] Verify all commits are properly tracked
- [ ] Create initial commit if needed with current stable state

**Acceptance Criteria:**
- `.gitignore` properly excludes sensitive data
- Repository has clean git status
- Environment variables documented in `.env.example`

---

### Issue #2: Update Dependencies for RAG Implementation
**Labels:** `dependencies` `priority:high`

**Description:**
Add required packages for PDF text extraction, vector embeddings, and RAG functionality.

**Tasks:**
- [ ] Add to `requirements.txt`:
  ```
  PyPDF2==3.0.1          # PDF text extraction
  numpy==1.26.4          # Vector operations
  scikit-learn==1.4.0    # Cosine similarity calculations
  ```
- [ ] Create virtual environment setup documentation
- [ ] Test installation with `pip install -r requirements.txt`
- [ ] Verify all packages compatible with Python 3.11+

**Acceptance Criteria:**
- `requirements.txt` updated with new dependencies
- All packages install without conflicts
- Documentation for setting up environment exists

---

## PHASE 2: UI Bug Fixes & Design Improvements 🎨

### Issue #3: Fix Notes Page Broken HTML/CSS
**Labels:** `bug` `ui` `priority:critical`

**Description:**
The notes editor page has broken HTML (unclosed div tag) and missing CSS styles causing layout issues.

**Related Files:**
- `templates/notes.html` (line 42)
- `static/dashboard.css`

**Tasks:**
- [ ] **Fix HTML:** Change line 42 from `</div` to `</div>` in `templates/notes.html`
- [ ] **Add missing CSS classes** to `static/dashboard.css`:
  ```css
  .notes-container {
      width: 100%;
      height: 100vh;
      display: flex;
      flex-direction: column;
      background: #1e1e1e;
  }
  
  .notes-content {
      flex: 1;
      display: flex;
      flex-direction: column;
      padding: 24px;
      overflow-y: auto;
  }
  
  .notes-header {
      margin-bottom: 24px;
  }
  
  .notes-title {
      width: 100%;
      background: transparent;
      border: none;
      color: #cccccc;
      font-size: 32px;
      font-weight: 600;
      padding: 8px 0;
      margin-bottom: 12px;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  }
  
  .notes-title:focus {
      outline: none;
      color: #ffffff;
  }
  
  .notes-meta {
      display: flex;
      gap: 12px;
      color: #858585;
      font-size: 13px;
  }
  
  .notes-editor {
      width: 100%;
      min-height: 500px;
      background: #252526;
      border: 1px solid #3e3e42;
      border-radius: 6px;
      color: #cccccc;
      font-size: 15px;
      line-height: 1.6;
      padding: 20px;
      font-family: 'SF Mono', Monaco, 'Cascadia Code', Consolas, monospace;
      resize: vertical;
  }
  
  .notes-editor:focus {
      outline: none;
      border-color: #007acc;
      box-shadow: 0 0 0 2px rgba(0, 122, 204, 0.2);
  }
  
  .notes-editor.hidden {
      display: none;
  }
  
  .notes-preview {
      display: none;
      width: 100%;
      min-height: 500px;
      background: #252526;
      border: 1px solid #3e3e42;
      border-radius: 6px;
      color: #cccccc;
      font-size: 15px;
      line-height: 1.6;
      padding: 20px;
  }
  
  .notes-preview.active {
      display: block;
  }
  
  .notes-preview h1, .notes-preview h2, .notes-preview h3 {
      color: #4ec9b0;
      margin-top: 24px;
      margin-bottom: 12px;
  }
  
  .notes-preview code {
      background: #1e1e1e;
      padding: 2px 6px;
      border-radius: 3px;
      color: #ce9178;
  }
  
  .notes-preview pre {
      background: #1e1e1e;
      padding: 16px;
      border-radius: 6px;
      overflow-x: auto;
  }
  ```
- [ ] Test notes creation, editing, and preview toggle
- [ ] Verify mobile responsiveness

**Acceptance Criteria:**
- Notes page renders correctly without layout breaks
- All buttons and inputs properly styled
- Preview mode works and displays markdown correctly
- Consistent with VS Code dark theme

---

### Issue #4: Add Toolbar Styling for Consistency
**Labels:** `ui` `enhancement` `priority:medium`

**Description:**
Ensure toolbar component has consistent styling across notes and resource pages.

**Tasks:**
- [ ] Add/verify `.toolbar` and `.toolbar-btn` CSS classes exist
- [ ] Ensure consistent spacing and colors
- [ ] Add hover states and transitions
- [ ] Test across all pages using toolbar (notes, resources)

**Acceptance Criteria:**
- Toolbar looks consistent on all pages
- Buttons have proper hover/active states
- Matches VS Code aesthetic

---

### Issue #5: Create Balanced UI for Document Reading
**Labels:** `ui` `enhancement` `priority:medium`

**Description:**
Add a "Reading Mode" toggle for better document viewing while maintaining VS Code aesthetic.

**Tasks:**
- [ ] Create reading mode CSS class with:
  - Increased font size (16-18px)
  - Better line height (1.8)
  - Max-width for optimal reading (800px)
  - Improved contrast for long-form content
- [ ] Add toggle button in main content area
- [ ] Persist preference in localStorage
- [ ] Apply to resource viewer and notes preview

**Acceptance Criteria:**
- Reading mode improves readability without losing dark theme
- Toggle works and persists across sessions
- Smooth transition between modes

---

## PHASE 3: AI Features & RAG Implementation 🤖

### Issue #6: Create Database Models for Document Chunks
**Labels:** `backend` `database` `priority:high`

**Description:**
Add new database models to support document chunking and vector embeddings for RAG.

**File:** `app/models.py`

**Tasks:**
- [ ] Create `ResourceChunk` model:
  ```python
  class ResourceChunk(db.Model):
      __tablename__ = "resource_chunk"
      
      id: Mapped[int] = mapped_column(primary_key=True)
      
      resource_id: Mapped[int] = mapped_column(
          ForeignKey("resource.id"),
          nullable=False,
          index=True
      )
      
      chunk_text: Mapped[str] = mapped_column(db.Text, nullable=False)
      chunk_index: Mapped[int] = mapped_column(db.Integer, nullable=False)
      
      # For PDFs
      page_number: Mapped[int | None] = mapped_column(db.Integer)
      
      # Vector embedding (stored as JSON array)
      embedding: Mapped[str | None] = mapped_column(db.Text)
      
      # Metadata
      token_count: Mapped[int | None] = mapped_column(db.Integer)
      
      created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
      
      resource = relationship("Resource", backref="chunks")
  ```
- [ ] Add summary fields to `Resource` model:
  ```python
  summary: Mapped[str | None] = mapped_column(db.Text)
  summary_generated_at: Mapped[datetime | None] = mapped_column()
  ```
- [ ] Create database migration script
- [ ] Test model creation and relationships

**Acceptance Criteria:**
- New models created without errors
- Database migrations run successfully
- Relationships work correctly between Resource and ResourceChunk

---

### Issue #7: Implement PDF Text Extraction
**Labels:** `backend` `ai` `priority:critical`

**Description:**
Extract text from uploaded PDFs and chunk them for RAG processing.

**File:** `app/resource.py`

**Tasks:**
- [ ] Create `extract_pdf_text()` function using PyPDF2:
  ```python
  def extract_pdf_text(file_path):
      """Extract text from PDF file with page numbers"""
      import PyPDF2
      
      text_by_page = []
      try:
          with open(file_path, 'rb') as file:
              pdf_reader = PyPDF2.PdfReader(file)
              for page_num, page in enumerate(pdf_reader.pages, 1):
                  text = page.extract_text()
                  if text.strip():  # Only add non-empty pages
                      text_by_page.append({
                          'page': page_num,
                          'text': text.strip()
                      })
          return text_by_page
      except Exception as e:
          print(f"Error extracting PDF text: {e}")
          return []
  ```
- [ ] Create `chunk_text()` function:
  - 500-token chunks with 100-token overlap
  - Use tiktoken for accurate token counting
  - Preserve page numbers for each chunk
- [ ] Integrate into upload workflow in `upload_resource` route
- [ ] Store chunks in `ResourceChunk` table with embeddings placeholder
- [ ] Add error handling for corrupted/scanned PDFs

**Acceptance Criteria:**
- PDF uploads automatically extract and chunk text
- Chunks stored with correct page numbers
- Error handling prevents upload failures
- Handles multi-page PDFs correctly

---

### Issue #8: Implement OpenAI Embeddings for RAG
**Labels:** `backend` `ai` `priority:high`

**Description:**
Generate vector embeddings for document chunks to enable semantic search and RAG.

**File:** `app/ai_utils.py`

**Tasks:**
- [ ] Create `generate_embedding()` function:
  ```python
  def generate_embedding(text: str) -> list[float]:
      """Generate embedding vector using OpenAI"""
      from openai import OpenAI
      from flask import current_app
      
      client = OpenAI(api_key=current_app.config['OPENAI_API_KEY'])
      response = client.embeddings.create(
          model="text-embedding-3-small",
          input=text
      )
      return response.data[0].embedding
  ```
- [ ] Create `find_relevant_chunks()` function:
  ```python
  def find_relevant_chunks(query: str, resource_ids: list[int], top_k: int = 5):
      """Find most relevant chunks using cosine similarity"""
      import json
      import numpy as np
      from sklearn.metrics.pairwise import cosine_similarity
      
      # Generate query embedding
      query_embedding = generate_embedding(query)
      
      # Get all chunks for specified resources
      chunks = ResourceChunk.query.filter(
          ResourceChunk.resource_id.in_(resource_ids),
          ResourceChunk.embedding.isnot(None)
      ).all()
      
      # Calculate similarities
      similarities = []
      for chunk in chunks:
          chunk_embedding = json.loads(chunk.embedding)
          similarity = cosine_similarity(
              [query_embedding], 
              [chunk_embedding]
          )[0][0]
          similarities.append((chunk, similarity))
      
      # Sort and return top_k
      similarities.sort(key=lambda x: x[1], reverse=True)
      return similarities[:top_k]
  ```
- [ ] Add batch embedding generation for efficiency
- [ ] Update `ResourceChunk` creation to generate embeddings
- [ ] Add config for embedding model in `config.py`:
  ```python
  OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
  ```

**Acceptance Criteria:**
- Embeddings generated successfully for new chunks
- Semantic search returns relevant results
- Cosine similarity calculation works correctly
- Batch processing handles multiple chunks efficiently

---

### Issue #9: Update AI Context Building with RAG
**Labels:** `backend` `ai` `priority:high`

**Description:**
Modify the chat context building to use RAG retrieval instead of sending full documents.

**File:** `app/chat.py`

**Tasks:**
- [ ] Update `build_context()` function to use RAG:
  ```python
  def build_context(conversation_id: int, user_message: str) -> str:
      """Build context using RAG retrieval"""
      conversation = Conversation.query.get(conversation_id)
      attached_resources = conversation.attached_resources.all()
      attached_notes = conversation.attached_notes.all()
      
      context_parts = []
      
      # Get relevant chunks using RAG
      if attached_resources:
          resource_ids = [r.id for r in attached_resources]
          relevant_chunks = find_relevant_chunks(
              query=user_message,
              resource_ids=resource_ids,
              top_k=10
          )
          
          for chunk, score in relevant_chunks:
              resource = chunk.resource
              context_parts.append(
                  f"[Source: {resource.title}, Page {chunk.page_number}]\n"
                  f"{chunk.chunk_text}\n"
              )
      
      # Add relevant notes (full text, they're usually short)
      for note in attached_notes:
          context_parts.append(
              f"[Note: {note.title}]\n{note.content}\n"
          )
      
      # Limit total context to ~3000 tokens
      context = "\n---\n".join(context_parts)
      return context[:12000]  # Rough char limit
  ```
- [ ] Add fallback if no relevant chunks found
- [ ] Implement token budget management (stay under 4000 tokens total)
- [ ] Add logging for retrieved chunks and scores
- [ ] Update system prompt to emphasize source-grounded responses

**Acceptance Criteria:**
- Chat uses RAG retrieval instead of full documents
- Context stays within token limits
- Most relevant chunks are selected
- Source information preserved for citations

---

### Issue #10: Implement Citation System in AI Responses
**Labels:** `backend` `ai` `ui` `priority:high`

**Description:**
Add inline citations to AI responses linking back to source documents with specific pages.

**Files:** `app/chat.py`, `templates/dashboard/rightpanel.html`, `static/dashboard.css`

**Tasks:**
- [ ] **Backend - Update System Prompt:** Modify in `app/chat.py`:
  ```python
  system_prompt = """You are a study assistant helping students understand their course materials.
  
  CRITICAL RULES:
  - Answer questions using ONLY the provided sources below
  - Always cite your sources using this exact format: [Source: Resource Title, Page X]
  - If the answer requires information from multiple sources, cite each one
  - If information isn't in the provided sources, clearly state: "I cannot find this information in your materials"
  - Be accurate and concise
  
  When citing:
  - Use the exact resource title from the [Source: ...] tags
  - Include the page number when available
  - Place citations at the end of the relevant sentence
  """
  ```
- [ ] **Backend - Parse Citations:** Create citation parsing function:
  ```python
  def parse_citations(ai_response: str, attached_resources: list) -> dict:
      """Extract citations from AI response and match to resources"""
      import re
      
      citation_pattern = r'\[Source: ([^,]+), Page (\d+)\]'
      citations = re.findall(citation_pattern, ai_response)
      
      citation_data = []
      for title, page in citations:
          # Find matching resource
          resource = next((r for r in attached_resources if title.strip() in r.title), None)
          if resource:
              citation_data.append({
                  'resource_id': resource.id,
                  'resource_title': title.strip(),
                  'page': int(page)
              })
      
      return citation_data
  ```
- [ ] **Frontend - Render Citations:** Update chat message rendering in `rightpanel.html`:
  ```html
  <div class="chat-message ai-message">
      <div class="message-content" data-citations='{{ message.citations_json }}'></div>
  </div>
  ```
- [ ] **Frontend - Add Click Handlers:** JavaScript to handle citation clicks:
  ```javascript
  document.querySelectorAll('.citation').forEach(cite => {
      cite.addEventListener('click', () => {
          const resourceId = cite.dataset.resourceId;
          const page = cite.dataset.page;
          openPDFModal(resourceId, page);
      });
  });
  ```
- [ ] **CSS - Style Citations:**
  ```css
  .citation {
      background: #264f78;
      color: #4fc3f7;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: 500;
      cursor: pointer;
      margin: 0 4px;
      display: inline-block;
      transition: all 0.2s;
  }
  
  .citation:hover {
      background: #1a3a52;
      transform: translateY(-1px);
      box-shadow: 0 2px 4px rgba(79, 195, 247, 0.3);
  }
  
  .citation::before {
      content: '📎 ';
  }
  ```

**Acceptance Criteria:**
- AI responses include source citations with page numbers
- Citations are clickable and properly styled
- Citations link to correct document and page
- System prompt enforces source-grounded responses
- Citations parsed and stored with messages

---

### Issue #11: Auto-Generate Resource Summaries on Upload
**Labels:** `backend` `ai` `priority:medium`

**Description:**
Automatically generate a concise summary when a resource is uploaded using GPT.

**File:** `app/resource.py`

**Tasks:**
- [ ] Create `generate_resource_summary()` function:
  ```python
  def generate_resource_summary(text_by_page: list, title: str) -> str:
      """Generate summary of resource content"""
      from openai import OpenAI
      from flask import current_app
      import tiktoken
      
      # Combine first pages (up to ~2000 tokens)
      enc = tiktoken.encoding_for_model("gpt-4o-mini")
      combined_text = ""
      token_count = 0
      
      for page_data in text_by_page:
          page_text = page_data['text']
          page_tokens = len(enc.encode(page_text))
          
          if token_count + page_tokens > 2000:
              break
          
          combined_text += f"\n{page_text}"
          token_count += page_tokens
      
      if not combined_text.strip():
          return "No text content available for summary."
      
      # Generate summary
      client = OpenAI(api_key=current_app.config['OPENAI_API_KEY'])
      
      response = client.chat.completions.create(
          model="gpt-4o-mini",
          messages=[
              {
                  "role": "system",
                  "content": "You are a helpful assistant that creates concise summaries of academic documents. Create a summary in 3-5 sentences covering the main topics and key points."
              },
              {
                  "role": "user",
                  "content": f"Summarize this document titled '{title}':\n\n{combined_text}"
              }
          ],
          max_tokens=200,
          temperature=0.5
      )
      
      return response.choices[0].message.content.strip()
  ```
- [ ] Integrate into upload workflow after text extraction
- [ ] Store summary in `Resource.summary` field
- [ ] Display summary in resource cards on dashboard
- [ ] Add "🔄 Regenerate Summary" button in resource view page
- [ ] Handle cases where text extraction fails

**Acceptance Criteria:**
- Summaries generated automatically on PDF upload
- Summaries are concise (3-5 sentences) and accurate
- Summaries displayed in resource list/cards
- Manual regeneration works
- Graceful handling of empty or scanned PDFs

---

### Issue #12: Implement Study Guide Generation
**Labels:** `backend` `ai` `priority:medium`

**Description:**
Generate comprehensive study guides from all resources and notes in a topic using RAG.

**File:** Create new `app/study_guide.py` blueprint

**Tasks:**
- [ ] Create new blueprint file `app/study_guide.py`
- [ ] Register blueprint in `app/__init__.py`
- [ ] Create route `/topic/<int:topic_id>/generate-study-guide` (POST):
  ```python
  @bp.route('/<int:topic_id>/generate-study-guide', methods=['POST'])
  @login_required
  def generate_study_guide(topic_id):
      """Generate comprehensive study guide for topic"""
      topic = Topic.query.filter_by(id=topic_id, user_id=current_user.id).first_or_404()
      
      # Gather all content
      resources = topic.resources.all()
      notes = topic.notes.filter_by(is_ai_generated=False).all()
      
      # Use RAG to extract key information
      guide_sections = []
      
      # 1. Overview
      # 2. Key Concepts
      # 3. Important Definitions
      # 4. Summary of Main Ideas
      # 5. Review Questions
      
      # Generate with OpenAI
      study_guide_content = generate_study_guide_content(topic, resources, notes)
      
      # Save as AI-generated note
      guide_note = Note(
          title=f"Study Guide: {topic.name}",
          content=study_guide_content,
          user_id=current_user.id,
          topic_id=topic_id,
          is_ai_generated=True
      )
      db.session.add(guide_note)
      db.session.commit()
      
      return jsonify({'success': True, 'note_id': guide_note.id})
  ```
- [ ] Create `generate_study_guide_content()` helper function
- [ ] Add "📚 Generate Study Guide" button in topic view page
- [ ] Show loading state during generation
- [ ] Handle topics with no resources gracefully

**Acceptance Criteria:**
- Study guide generation works from topic page
- Guide includes: overview, key concepts, definitions, summary, questions
- Guide saved as AI-generated note with clear title
- Content is comprehensive and well-structured
- Button shows loading state during generation

---

### Issue #13: Add "Pin Response" Feature for Important Chat Messages
**Labels:** `backend` `ui` `priority:low`

**Description:**
Allow users to convert important AI chat responses into saved notes with one click.

**Files:** `app/chat.py`, `templates/dashboard/rightpanel.html`

**Tasks:**
- [ ] **Backend - Add Route:** Create `/chat/pin-message/<int:message_id>` endpoint:
  ```python
  @bp.route('/pin-message/<int:message_id>', methods=['POST'])
  @login_required
  def pin_message(message_id):
      """Convert chat message to saved note"""
      message = ChatMessage.query.filter_by(id=message_id).first_or_404()
      conversation = message.conversation
      
      # Verify ownership
      if conversation.user_id != current_user.id:
          return jsonify({'error': 'Unauthorized'}), 403
      
      # Generate title from first line or auto-generate
      lines = message.content.split('\n')
      title = lines[0][:100] if lines[0] else f"Chat Response - {datetime.utcnow().strftime('%Y-%m-%d')}"
      
      # Create note
      note = Note(
          title=title,
          content=message.content,
          user_id=current_user.id,
          topic_id=conversation.topic_id,
          is_ai_generated=True
      )
      db.session.add(note)
      db.session.commit()
      
      return jsonify({
          'success': True,
          'note_id': note.id,
          'message': 'Response saved as note!'
      })
  ```
- [ ] **Frontend - Add Button:** Add pin button to each AI message in `rightpanel.html`:
  ```html
  {% if msg.role == 'assistant' %}
  <div class="message-actions">
      <button class="pin-btn" onclick="pinMessage({{ msg.id }})">
          📌 Save as Note
      </button>
  </div>
  {% endif %}
  ```
- [ ] **Frontend - Add JavaScript Handler:**
  ```javascript
  function pinMessage(messageId) {
      fetch(`/chat/pin-message/${messageId}`, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'}
      })
      .then(res => res.json())
      .then(data => {
          if (data.success) {
              showToast('✅ Saved as note!', 'success');
          }
      })
      .catch(err => showToast('❌ Error saving note', 'error'));
  }
  ```
- [ ] **CSS - Style Button:**
  ```css
  .message-actions {
      display: flex;
      gap: 8px;
      margin-top: 8px;
      opacity: 0;
      transition: opacity 0.2s;
  }
  
  .chat-message:hover .message-actions {
      opacity: 1;
  }
  
  .pin-btn {
      background: transparent;
      border: 1px solid #3e3e42;
      color: #858585;
      padding: 4px 12px;
      border-radius: 4px;
      font-size: 11px;
      cursor: pointer;
      transition: all 0.2s;
  }
  
  .pin-btn:hover {
      background: #2d2d30;
      color: #4fc3f7;
      border-color: #4fc3f7;
  }
  ```
- [ ] Add toast notification component for feedback

**Acceptance Criteria:**
- Pin button appears on AI messages on hover
- Messages convert to notes successfully
- Notes appear in topic's notes list marked as AI-generated
- Toast notification confirms successful save
- Button has proper styling and hover states

---

### Issue #14: Implement PDF Preview Modal with Citation Highlighting
**Labels:** `frontend` `ui` `priority:medium`

**Description:**
Create a modal viewer to preview PDFs in-app with ability to jump to specific pages from citations.

**Files:** `templates/dashboard.html`, `static/dashboard.css`, create new `static/pdf-viewer.js`

**Tasks:**
- [ ] Add PDF.js library to project:
  ```html
  <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
  ```
- [ ] Create PDF modal component in `dashboard.html`:
  ```html
  <div id="pdfModal" class="modal">
      <div class="modal-content pdf-viewer-container">
          <div class="pdf-header">
              <h3 id="pdfTitle"></h3>
              <button class="close-btn" onclick="closePDFModal()">×</button>
          </div>
          <div class="pdf-controls">
              <button onclick="prevPage()">← Previous</button>
              <span>Page <span id="pageNum"></span> of <span id="pageCount"></span></span>
              <button onclick="nextPage()">Next →</button>
          </div>
          <canvas id="pdfCanvas"></canvas>
      </div>
  </div>
  ```
- [ ] Create `static/pdf-viewer.js`:
  ```javascript
  let pdfDoc = null;
  let pageNum = 1;
  let pageRendering = false;
  let pageNumPending = null;
  
  function openPDFModal(resourceId, page = 1) {
      // Fetch PDF and render
      pageNum = page;
      document.getElementById('pdfModal').style.display = 'flex';
      loadPDF(resourceId);
  }
  
  function loadPDF(resourceId) {
      fetch(`/resource/${resourceId}/pdf-url`)
          .then(res => res.json())
          .then(data => {
              pdfjsLib.getDocument(data.url).promise.then(pdf => {
                  pdfDoc = pdf;
                  document.getElementById('pageCount').textContent = pdf.numPages;
                  renderPage(pageNum);
              });
          });
  }
  
  function renderPage(num) {
      pageRendering = true;
      pdfDoc.getPage(num).then(page => {
          const canvas = document.getElementById('pdfCanvas');
          const ctx = canvas.getContext('2d');
          const viewport = page.getViewport({scale: 1.5});
          
          canvas.height = viewport.height;
          canvas.width = viewport.width;
          
          page.render({canvasContext: ctx, viewport: viewport}).promise.then(() => {
              pageRendering = false;
              if (pageNumPending !== null) {
                  renderPage(pageNumPending);
                  pageNumPending = null;
              }
          });
      });
      
      document.getElementById('pageNum').textContent = num;
  }
  
  function queueRenderPage(num) {
      if (pageRendering) {
          pageNumPending = num;
      } else {
          renderPage(num);
      }
  }
  
  function prevPage() {
      if (pageNum <= 1) return;
      pageNum--;
      queueRenderPage(pageNum);
  }
  
  function nextPage() {
      if (pageNum >= pdfDoc.numPages) return;
      pageNum++;
      queueRenderPage(pageNum);
  }
  
  function closePDFModal() {
      document.getElementById('pdfModal').style.display = 'none';
  }
  ```
- [ ] Add CSS for modal:
  ```css
  .modal {
      display: none;
      position: fixed;
      z-index: 1000;
      left: 0;
      top: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.8);
      align-items: center;
      justify-content: center;
  }
  
  .pdf-viewer-container {
      background: #1e1e1e;
      border-radius: 8px;
      width: 90%;
      max-width: 1200px;
      max-height: 90vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
  }
  
  .pdf-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px 24px;
      border-bottom: 1px solid #3e3e42;
  }
  
  .pdf-controls {
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 16px;
      padding: 12px;
      background: #252526;
      border-bottom: 1px solid #3e3e42;
  }
  
  #pdfCanvas {
      flex: 1;
      overflow: auto;
      padding: 20px;
      background: #2d2d30;
  }
  ```
- [ ] Add backend route to serve PDF URL: `/resource/<id>/pdf-url`
- [ ] Test with multi-page PDFs
- [ ] Add keyboard navigation (arrow keys)

**Acceptance Criteria:**
- PDFs render in modal viewer
- Can navigate between pages
- Clicking citation opens PDF at correct page
- Modal styled consistent with VS Code theme
- Keyboard shortcuts work (arrows, escape)
- Modal closes properly

---

### Issue #15: Add Semantic Search for Notes and Resources
**Labels:** `backend` `ai` `frontend` `priority:low`

**Description:**
Implement search functionality using vector embeddings for better relevance than keyword search.

**Files:** Create new `app/search.py` blueprint, update `templates/dashboard.html`

**Tasks:**
- [ ] Create new blueprint `app/search.py`:
  ```python
  @bp.route('/search', methods=['GET'])
  @login_required
  def search():
      """Semantic search across notes and resources"""
      query = request.args.get('q', '')
      
      if not query:
          return jsonify({'results': []})
      
      # Generate query embedding
      query_embedding = generate_embedding(query)
      
      # Search resource chunks
      resource_results = search_resource_chunks(query_embedding, current_user.id)
      
      # Search notes (generate embeddings on-demand or pre-compute)
      note_results = search_notes(query, current_user.id)
      
      # Combine and rank results
      all_results = resource_results + note_results
      all_results.sort(key=lambda x: x['score'], reverse=True)
      
      return jsonify({'results': all_results[:20]})
  ```
- [ ] Create `search_resource_chunks()` helper:
  ```python
  def search_resource_chunks(query_embedding, user_id):
      """Find relevant resource chunks"""
      # Get all chunks for user's resources
      # Calculate cosine similarity
      # Return top matches with context
  ```
- [ ] Create `search_notes()` helper (simple text search or embeddings)
- [ ] Add search bar to dashboard:
  ```html
  <div class="search-bar">
      <input type="text" id="searchInput" placeholder="🔍 Search notes and resources...">
      <div id="searchResults" class="search-results"></div>
  </div>
  ```
- [ ] Add JavaScript for search with debouncing:
  ```javascript
  let searchTimeout;
  document.getElementById('searchInput').addEventListener('input', (e) => {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => {
          performSearch(e.target.value);
      }, 300);
  });
  
  function performSearch(query) {
      if (query.length < 3) {
          document.getElementById('searchResults').innerHTML = '';
          return;
      }
      
      fetch(`/search?q=${encodeURIComponent(query)}`)
          .then(res => res.json())
          .then(data => {
              displaySearchResults(data.results);
          });
  }
  ```
- [ ] Style search results dropdown
- [ ] Add result highlighting
- [ ] Link results to source documents/notes

**Acceptance Criteria:**
- Search returns relevant results based on semantic meaning
- Results ranked by relevance score
- Search UI integrated into dashboard
- Results display with snippets and highlights
- Clicking result navigates to source
- Search is fast and responsive (< 500ms)

---

## Priority & Timeline

### Sprint 1 (Quick Wins - Week 1)
1. ✅ Issue #1: Git setup
2. ✅ Issue #2: Dependencies
3. 🔥 Issue #3: Fix notes UI bug (CRITICAL)
4. ✅ Issue #4: Toolbar styling

### Sprint 2 (Foundation - Weeks 2-3)
5. 🏗️ Issue #6: Database models
6. 🔥 Issue #7: PDF extraction (CRITICAL)
7. 🔥 Issue #8: Embeddings/RAG (CRITICAL)

### Sprint 3 (Core AI Features - Weeks 4-5)
8. 🔥 Issue #9: RAG context building (CRITICAL)
9. 🔥 Issue #10: Citation system (CRITICAL)
10. 🎯 Issue #11: Auto-summaries

### Sprint 4 (Enhanced Features - Week 6)
11. 🎨 Issue #5: Reading mode UI
12. 🎯 Issue #12: Study guides
13. 🎨 Issue #14: PDF preview modal

### Sprint 5 (Nice-to-Have - Week 7-8)
14. ⭐ Issue #13: Pin responses
15. ⭐ Issue #15: Semantic search

---

## Legend
- 🔥 **Critical Path** - Required for NotebookLM-like functionality
- 🏗️ **Foundation** - Required before other features
- 🎯 **High Value** - Significant user-facing benefit
- 🎨 **UI Enhancement** - Improves user experience
- ⭐ **Nice-to-Have** - Enhances but not essential

---

## Notes for Implementation

### Configuration Updates Needed
Add to `app/config.py`:
```python
# RAG Configuration
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
CHUNK_SIZE = 500  # tokens
CHUNK_OVERLAP = 100  # tokens
MAX_CONTEXT_CHUNKS = 10  # number of chunks to retrieve
```

### Database Migration Commands
After creating new models:
```bash
# Create migration
flask db migrate -m "Add ResourceChunk model and embeddings"

# Apply migration
flask db upgrade
```

### Testing Strategy
1. **Unit Tests**: Test each helper function independently
2. **Integration Tests**: Test RAG pipeline end-to-end
3. **Manual Testing**: Verify UI/UX with real PDFs and conversations
4. **Performance Testing**: Measure embedding generation and search speed

### Cost Considerations
- **Embeddings**: ~$0.02 per 1M tokens (text-embedding-3-small)
- **GPT Calls**: Current usage tracking already in place
- **Estimate**: ~$5-10 for processing 100 PDFs with RAG

---

**Total Estimated Timeline:** 6-8 weeks (part-time development)

**End Goal:** StudyMate with NotebookLM-like source-grounded AI, citation system, automatic summaries, and RAG-powered chat, all while maintaining a beautiful VS Code aesthetic.
