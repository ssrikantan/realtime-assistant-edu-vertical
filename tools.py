from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from chainlit.logger import logger
import pyodbc
from envconfig import DefaultConfig
from atlassian import Jira
from functions import (
    perform_search_based_qna,
    get_mark_status_summary,
    get_grievance_status_def,
    register_user_grievance_def,
)


tools_list = [
    {
        "type": "function",
        "name": "perform_search_based_qna",
        "description": "call this function to respond to the user query on subjects like Accountancy, Chemistry & Physics, based on the course material.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "type": "function",
        "name": "get_mark_status_summary",
        "description": "retrieve the mark status summary for a student based on the user name",
        "parameters": {
            "type": "object",
            "properties": {
                "user_name": {
                    "type": "string",
                    "description": "The user name of the student registered in the College System",
                }
            },
            "required": ["user_name"],
        },
    },
    {
        "type": "function",
        "name": "get_grievance_status_def",
        "description": "fetch real time grievance status for a grievance id",
        "parameters": {
            "type": "object",
            "properties": {
                "grievance_id": {
                    "type": "number",
                    "description": "The grievance id of the user registered in the Grievance System",
                }
            },
            "required": ["grievance_id"],
        },
    },
    {
        "type": "function",
        "name": "register_user_grievance_def",
        "description": "register a grievance, or complaint or issue from the user in the college facilities, academics system",
        "parameters": {
            "type": "object",
            "properties": {
                "grievance_category": {
                    "type": "string",
                    "enum": [
                        "facilities issues",
                        "Exams issues",
                        "Onboarding issues",
                        "Library issues",
                        "other issues",
                    ],
                },
                "grievance_description": {
                    "type": "string",
                    "description": "The detailed description of the grievance faced by the user",
                },
            },
            "required": ["grievance_category", "grievance_description"],
        },
    },
]


available_functions = {
    "perform_search_based_qna": perform_search_based_qna,
    "get_mark_status_summary": get_mark_status_summary,
    "get_grievance_status_def": get_grievance_status_def,
    "register_user_grievance_def": register_user_grievance_def,
}

