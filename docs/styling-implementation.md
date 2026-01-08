# StudyMate Dashboard & Topic Page Styling

## Overview
This document outlines the styling implementation for the StudyMate dashboard and topic pages following a VS Code-inspired dark theme design.

## Main Dashboard (`main.html`)

### Features Implemented:
1. **Welcome State** - Displayed when no topics exist
   - Clean welcome card with call-to-action
   - "Create Your First Topic" button

2. **Topics Grid** - Displayed when topics exist
   - Responsive grid layout
   - Topic cards with:
     - Topic name (title)
     - Description
     - "View Topic" button
     - Hover effects with border highlight and lift animation
   
3. **Add Topic Card**
   - Dashed border design
   - Plus icon
   - Centered layout
   - Opens create topic modal on click

4. **Modal Form**
   - Clean, centered modal
   - Dark theme styling
   - Fields for:
     - Topic name
     - Topic description
   - Smooth transitions and animations

## Topic Page (`topic.html`)

### Layout Structure:
1. **Back Navigation**
   - "← Back to Dashboard" link at the top
   - Hover effects

2. **Topic Header**
   - Large title (topic name)
   - Description text
   - Clean, spacious design

3. **Action Buttons Bar**
   - Fixed horizontal bar with three action buttons:
     - Add Note
     - Add Resource
     - Add Subtopic
   - Consistent styling with primary action color

4. **Content Sections**
   Each section includes:
   - Section title with icon
   - Grid layout for items
   - Empty state messaging when no items exist

### Resources Section
- **Resource Cards:**
  - Thumbnail area with type-specific gradient backgrounds
  - Color-coded by type:
    - PDF: Red gradient
    - Image: Blue gradient
    - Video: Purple gradient
    - Link: Green gradient
  - Icon representation for file types
  - Resource title and type label

### Notes Section
- **Note Cards:**
  - Icon header with note emoji
  - Note title
  - Content preview (truncated to 4 lines)
  - Last edited timestamp
  - Hover effects

### Subtopics Section
- **Subtopic Cards:**
  - Icon/emoji area (50x50px with gradient background)
  - Title and description
  - Horizontal layout with icon on left
  - Full clickable area

## Design System

### Color Palette:
- **Background:** `#1e1e1e`
- **Cards:** `#252526`
- **Borders:** `#3e3e42`
- **Primary (Accent):** `#007acc`
- **Primary Hover:** `#0098ff`
- **Text Primary:** `#ffffff`
- **Text Secondary:** `#cccccc`
- **Text Muted:** `#858585`
- **Text Placeholder:** `#6a6a6a`

### Typography:
- **Font Family:** System fonts (-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, etc.)
- **Sizes:**
  - Page Title: 28px
  - Section Title: 20px
  - Card Title: 18px (topics), 16px (subtopics)
  - Body Text: 14px
  - Small Text: 13px
  - Meta Text: 11px

### Spacing:
- **Card Padding:** 20-24px
- **Section Margins:** 32px bottom
- **Grid Gaps:** 16-20px
- **Content Padding:** 24px

### Interactions:
- **Hover Effects:**
  - Border color changes to primary (#007acc)
  - Subtle lift animation (translateY(-2px))
  - Box shadow with primary color
  
- **Transitions:** 
  - All: 0.3s ease
  - Buttons: 0.2s
  
- **Active States:**
  - Button scale: 0.98

## Responsive Breakpoints

### Desktop (> 1024px)
- Multi-column grids
- Full sidebar panels

### Tablet (768px - 1024px)
- Adjusted grid columns
- Smaller side panels

### Mobile (< 768px)
- Single column layouts
- Stacked action buttons
- Full-width cards
- Compact spacing

## Empty States
Each section has a thoughtful empty state with:
- Large icon (64px, 50% opacity)
- Helpful message explaining what to do
- Centered layout

## Accessibility Considerations
- High contrast colors
- Clear focus states
- Keyboard navigation support (via HTML structure)
- Semantic HTML elements
- Descriptive button text

## Future Enhancements
- Add actual backend connections for buttons
- Implement drag-and-drop for resource uploads
- Add filtering and sorting options
- Include search functionality
- Add progress indicators for topics
- Implement inline editing for cards
- Add confirmation dialogs for destructive actions

## Notes for Backend Integration
- All forms are wrapped but actions are not connected yet
- Card click handlers use onclick for navigation
- Modal uses JavaScript functions: `createTopic()` and `closeCreateTopicModal()`
- Empty states check for existence of items in template variables
- Date formatting uses Jinja2 filters (`.strftime()`)
