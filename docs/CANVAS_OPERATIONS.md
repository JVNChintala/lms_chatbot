# Canvas LMS Chatbot - Comprehensive Operations

## Available Operations by Role

### Student Operations
- **Courses**: List courses, Get course details
- **Modules**: List modules, Get module details
- **Assignments**: List assignments, Get assignment, Submit assignment
- **Content**: List announcements, discussions, quizzes, pages, files
- **Grades**: Get grades
- **Profile**: Get user profile

### Teacher/Faculty/Instructor Operations
All student operations PLUS:
- **Course Management**: Create course, Update course, Publish course
- **Module Management**: Create module, Update module, Delete module
- **Assignment Management**: Create assignment, Update assignment, Delete assignment, Grade assignment
- **Content Creation**: Create announcement, Create discussion, Create quiz, Create page
- **File Management**: Upload file
- **User Management**: Enroll user, List enrollments
- **Grading**: View gradebook

### Admin Operations
All teacher operations PLUS:
- **User Management**: List users, Create user, Unenroll user
- **Full System Access**: All Canvas LMS operations

## Intent Classification

The system recognizes 50+ intents across categories:

### Course Operations (6)
- list_courses, get_course_details, create_course, update_course, publish_course, unpublish_course

### Assignment Operations (7)
- list_assignments, get_assignment, create_assignment, update_assignment, delete_assignment, grade_assignment, submit_assignment

### Module Operations (5)
- list_modules, get_module, create_module, update_module, delete_module

### User Operations (6)
- list_users, get_user, create_user, enroll_user, unenroll_user, list_enrollments

### Content Operations (10)
- list_announcements, create_announcement
- list_discussions, create_discussion
- list_quizzes, create_quiz
- list_pages, create_page
- list_files, upload_file

### Grade Operations (2)
- get_grades, view_gradebook

## Conversational Features

1. **Context-Aware Parameter Extraction**: Extracts course IDs from previous responses
2. **Natural Clarification**: Uses OpenAI to generate conversational prompts for missing parameters
3. **Multi-Turn Conversations**: Maintains context across multiple requests
4. **Role-Based Access Control**: Automatically filters available operations by user role

## Example Conversations

**Student:**
- "List my courses" → Shows enrolled courses
- "Show assignments in Biology" → Lists assignments (extracts course_id from context)
- "What are my grades?" → Shows grade summary

**Teacher:**
- "Create a quiz in Python course" → Asks for quiz title, creates quiz
- "Grade John's assignment" → Asks for grade and feedback
- "Upload lecture notes" → Handles file upload

**Admin:**
- "Create a new user" → Asks for name, email, login_id
- "Enroll Sarah in Math 101" → Enrolls user in course
- "View system users" → Lists all users

## Technical Implementation

- **Intent Classifier**: 50+ intents with confidence scoring
- **Tool Executor**: 35+ Canvas API wrapper functions
- **OpenAI Integration**: GPT-4o-mini with Responses API
- **Context Management**: Raw tool data included in conversation history
- **Error Handling**: Graceful fallback to general conversation mode
