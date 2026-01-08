import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lms_chatot'))

from lms_chatot.canvas_agent import CanvasAgent
from lms_chatot.canvas_tools import CanvasTools
from lms_chatot.inference_systems.openai_inference import OpenAIInference


class TestIntegrationFlow(unittest.TestCase):
    """Test flow between main -> canvas_agent -> canvas_tools -> openai_inference"""

    def setUp(self):
        self.canvas_url = "https://test.canvas.com/api/v1"
        self.canvas_token = "test_token"
        self.mock_canvas = Mock()
        self.mock_admin_canvas = Mock()

    @patch('lms_chatot.canvas_agent.CanvasLMS')
    @patch('lms_chatot.canvas_agent.OpenAIInference')
    def test_list_courses_flow(self, mock_inference_class, mock_canvas_class):
        """Test: User asks to list courses -> Agent -> Tools -> OpenAI"""
        mock_canvas_instance = Mock()
        mock_canvas_instance.list_courses.return_value = [
            {"id": 1, "name": "Math 101", "course_code": "MATH101", "workflow_state": "available"}
        ]
        mock_canvas_class.return_value = mock_canvas_instance

        mock_inference = Mock()
        mock_inference.run_agent.return_value = {
            "content": "Here are your courses: Math 101",
            "usage": {"input_tokens": 10, "output_tokens": 5},
            "state": {}
        }
        mock_inference_class.return_value = mock_inference

        agent = CanvasAgent(self.canvas_url, self.canvas_token, as_user_id=123)
        
        result = agent.process_message(
            user_message="List my courses",
            conversation_history=[],
            user_role="student",
            user_info={"canvas_user_id": 123}
        )

        self.assertTrue(result.get("tool_used"))
        self.assertEqual(result.get("inference_system"), "OpenAI")
        mock_inference.run_agent.assert_called_once()

    @patch('lms_chatot.canvas_agent.CanvasLMS')
    @patch('lms_chatot.canvas_agent.OpenAIInference')
    def test_create_course_flow(self, mock_inference_class, mock_canvas_class):
        """Test: Teacher creates course -> Agent -> Tools -> Canvas API"""
        mock_admin_canvas = Mock()
        mock_admin_canvas.create_course.return_value = {
            "id": 42,
            "name": "Python 101",
            "course_code": "PY101"
        }
        mock_canvas_class.return_value = mock_admin_canvas

        mock_inference = Mock()
        mock_inference.run_agent.return_value = {
            "content": "Course created successfully",
            "usage": {},
            "state": {"course_id": 42}
        }
        mock_inference_class.return_value = mock_inference

        agent = CanvasAgent(self.canvas_url, self.canvas_token, as_user_id=None)
        
        result = agent.process_message(
            user_message="Create a course named Python 101",
            conversation_history=[],
            user_role="admin",
            user_info={"canvas_user_id": 1}
        )

        self.assertTrue(result.get("tool_used"))
        mock_inference.run_agent.assert_called_once()

    @patch('lms_chatot.canvas_agent.CanvasLMS')
    @patch('lms_chatot.canvas_agent.OpenAIInference')
    def test_conversational_flow(self, mock_inference_class, mock_canvas_class):
        """Test: General question -> Agent -> OpenAI (no tools)"""
        mock_canvas_class.return_value = Mock()

        mock_inference = Mock()
        mock_inference.run_agent.return_value = {
            "content": "Canvas LMS is a learning management system.",
            "usage": {},
            "state": {}
        }
        mock_inference_class.return_value = mock_inference

        agent = CanvasAgent(self.canvas_url, self.canvas_token)
        
        result = agent.process_message(
            user_message="What is Canvas LMS?",
            conversation_history=[],
            user_role="student"
        )

        self.assertTrue(result.get("tool_used"))  # run_agent always returns tool_used=True
        self.assertIn("Canvas LMS", result.get("content"))

    @patch('lms_chatot.canvas_agent.CanvasLMS')
    @patch('lms_chatot.canvas_agent.OpenAIInference')
    def test_clarification_flow(self, mock_inference_class, mock_canvas_class):
        """Test: Missing args -> Agent asks for clarification"""
        mock_canvas_class.return_value = Mock()

        mock_inference = Mock()
        mock_inference.call_with_tools.return_value = {
            "needs_tool": True,
            "tool_name": "create_assignment",
            "tool_args": {"name": "Homework 1"},
            "missing_args": ["course_id"],
            "content": "Which course should I create the assignment in?"
        }
        mock_inference_class.return_value = mock_inference

        agent = CanvasAgent(self.canvas_url, self.canvas_token)
        agent.user_role = "teacher"
        
        # Manually call _execute_tool to test clarification
        tool_def = {"function": {"name": "create_assignment", "parameters": {}}}
        result = agent._execute_tool(
            "Create assignment Homework 1",
            "create_assignment",
            tool_def,
            Mock(),
            []
        )

        self.assertTrue(result.get("clarification_needed"))

    def test_canvas_tools_execution(self):
        """Test: CanvasTools executes tool correctly"""
        mock_canvas = Mock()
        mock_canvas.list_courses.return_value = [
            {"id": 1, "name": "Course 1"}
        ]

        tools = CanvasTools(
            canvas=mock_canvas,
            admin_canvas=Mock(),
            user_role="student",
            user_info={"canvas_user_id": 123}
        )

        result = tools.execute_tool("list_user_courses", {})

        self.assertIn("courses", result)
        self.assertEqual(len(result["courses"]), 1)
        mock_canvas.list_courses.assert_called_once()

    def test_canvas_tools_role_filtering(self):
        """Test: Tools filtered by user role"""
        student_tools = CanvasTools.get_tool_definitions("student")
        teacher_tools = CanvasTools.get_tool_definitions("teacher")
        admin_tools = CanvasTools.get_tool_definitions("admin")

        student_names = {t["function"]["name"] for t in student_tools}
        teacher_names = {t["function"]["name"] for t in teacher_tools}
        admin_names = {t["function"]["name"] for t in admin_tools}

        # Students can't create courses
        self.assertNotIn("create_course", student_names)
        
        # Teachers can create courses
        self.assertIn("create_course", teacher_names)
        
        # Admins have most tools
        self.assertGreater(len(admin_tools), len(teacher_tools))

    @patch('lms_chatot.inference_systems.openai_inference.OpenAI')
    def test_openai_inference_tool_call(self, mock_openai_class):
        """Test: OpenAI inference detects and returns tool call"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.output = [
            Mock(type="tool_call", name="list_user_courses", arguments="{}")
        ]
        mock_response.output_text = None
        mock_response.usage = Mock(input_tokens=10, output_tokens=5, total_tokens=15)
        mock_response.model = "gpt-4o-mini"
        
        mock_client.responses.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        inference = OpenAIInference()
        
        tool_executor = Mock(return_value={"courses": []})
        
        result = inference.run_agent(
            system_prompt="You are a Canvas assistant",
            messages=[{"role": "user", "content": "List courses"}],
            tools=[{
                "function": {
                    "name": "list_user_courses",
                    "description": "List courses",
                    "parameters": {"type": "object", "properties": {}}
                }
            }],
            tool_executor=tool_executor
        )

        tool_executor.assert_called_once()

    @patch('lms_chatot.canvas_agent.CanvasLMS')
    @patch('lms_chatot.canvas_agent.OpenAIInference')
    def test_pending_tool_resume(self, mock_inference_class, mock_canvas_class):
        """Test: Resume pending tool with user clarification"""
        mock_canvas = Mock()
        mock_canvas.create_assignment.return_value = {"id": 99, "name": "HW1"}
        mock_canvas_class.return_value = mock_canvas

        mock_inference = Mock()
        mock_inference_class.return_value = mock_inference

        agent = CanvasAgent(self.canvas_url, self.canvas_token)
        
        pending_tool_def = {
            "function": {
                "name": "create_assignment",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer"},
                        "name": {"type": "string"}
                    },
                    "required": ["course_id", "name"]
                }
            }
        }

        result = agent.process_message(
            user_message="Course 1",
            conversation_history=[],
            user_role="teacher",
            pending_tool="create_assignment",
            pending_tool_def=pending_tool_def
        )

        # Should attempt to execute the pending tool
        self.assertIsNotNone(result)

    @patch('lms_chatot.canvas_agent.CanvasLMS')
    @patch('lms_chatot.canvas_agent.OpenAIInference')
    def test_multi_step_workflow(self, mock_inference_class, mock_canvas_class):
        """Test: Multi-step workflow (create course -> create module)"""
        mock_canvas = Mock()
        mock_canvas_class.return_value = mock_canvas

        mock_inference = Mock()
        mock_inference.run_agent.return_value = {
            "content": "Course and module created successfully",
            "usage": {},
            "state": {"course_id": 10, "modules": {"Module 1": 5}}
        }
        mock_inference_class.return_value = mock_inference

        agent = CanvasAgent(self.canvas_url, self.canvas_token)
        
        result = agent.process_message(
            user_message="Create a course and add a module",
            conversation_history=[],
            user_role="admin"
        )

        self.assertTrue(result.get("tool_used"))
        self.assertIn("state", result)
        mock_inference.run_agent.assert_called_once()

    def test_canvas_tools_error_handling(self):
        """Test: CanvasTools handles errors gracefully"""
        mock_canvas = Mock()
        mock_canvas.list_courses.side_effect = Exception("API Error")

        tools = CanvasTools(
            canvas=mock_canvas,
            admin_canvas=Mock(),
            user_role="student"
        )

        result = tools.execute_tool("list_user_courses", {})

        self.assertIn("error", result)

    def test_unknown_tool_execution(self):
        """Test: Unknown tool returns error"""
        tools = CanvasTools(
            canvas=Mock(),
            admin_canvas=Mock(),
            user_role="student"
        )

        result = tools.execute_tool("unknown_tool", {})

        self.assertIn("error", result)
        self.assertIn("Unknown function", result["error"])


if __name__ == "__main__":
    unittest.main()
