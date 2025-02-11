from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from chainlit.logger import logger
import pyodbc
from envconfig import DefaultConfig
from atlassian import Jira


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


def init_jira_connection() -> any:
    l_jira = None
    try:
        l_jira = Jira(
            url=DefaultConfig.attlassian_url,
            username=DefaultConfig.attlassian_user_name,
            password=DefaultConfig.attlassian_api_key,
        )
        l_jira.myself()
        print("Connected to Jira ticketing system....")
        logger.info("Connected to Jira ticketing system....")
        return l_jira
    except Exception as e:
        logger.error(f"Error connecting to Jira: {e}")
        logger.error("Exiting the program....")
        exit(1)


def init_database_connection() -> any:
    l_connection = None
    try:
        l_connection = pyodbc.connect(
            "Driver={ODBC Driver 18 for SQL Server};SERVER="
            + DefaultConfig.az_db_server
            + ";DATABASE="
            + DefaultConfig.az_db_database
            + ";UID="
            + DefaultConfig.az_db_username
            + ";PWD="
            + DefaultConfig.az_db_password
        )
        print("Connected to the database....")
        logger.info("Connected to the database....")
        return l_connection
    except Exception as e:
        logger.error(f"Error connecting to the database: {e}")
        logger.error("Exiting the program....")
        exit(1)


def get_grievance_status_def(grievance_id):
    response_message = ""
    response = ""
    JQL = (
        "project = "
        + DefaultConfig.grievance_project_name
        + " AND id = "
        + str(grievance_id)
    )

    l_jira = init_jira_connection()
    try:
        response_message = l_jira.jql(JQL)
        logger.info("Issue status retrieved successfully!")
        logger.info("grievance status response .. ", response_message)
        if response_message["issues"]:
            response = (
                "\n Here is the updated status of your grievance.\ngrievance_id : "
                + response_message["issues"][0]["id"]
            )
            response += (
                "\npriority : "
                + response_message["issues"][0]["fields"]["priority"]["name"]
            )
            response += (
                "\nstatus : "
                + response_message["issues"][0]["fields"]["status"]["statusCategory"][
                    "key"
                ]
            )
            response += (
                "\ngrievance description : "
                + response_message["issues"][0]["fields"]["description"]
            )
            if response_message["issues"][0]["fields"]["duedate"]:
                response += (
                    "\ndue date : " + response_message["issues"][0]["fields"]["duedate"]
                )
            else:
                response += "\ndue date : not assigned by the system yet."
        else:
            response = "sorry, we could not locate a grievance with this ID. Can you please verify your input again?"
    except Exception as e:
        logger.error(f"Error retrieving the grievance: {e.args[0]}")
        response = "We had an issue retrieving your grievance status. Please check back in some time"

    # Send the markdown table as a Chainlit message
    # await cl.Message(content=f"{response}").send()
    return response


def register_user_grievance_def(grievance_category, grievance_description):
    response_message = ""
    try:
        # Define the issue details (project key, summary, description, and issue type)

        issue_details = {
            "project": {"key": DefaultConfig.grievance_project_key},
            "summary": grievance_category,
            "description": grievance_description,
            "issuetype": {"name": "Task"},
        }
        l_jira = init_jira_connection()

        # Create the issue
        response = l_jira.create_issue(fields=issue_details)
        response_message = (
            "We are sorry about the issue you are facing. We have registered a grievance with id "
            + response["id"]
            + " to track it to closure. Please quote that in your future communications with us"
        )
        logger.info("Issue created successfully!")
    except Exception as e:
        logger.error(f"Error registering the grievance issue: {e.args[0]}")
        response_message = (
            "We had an issue registering your grievance. Please check back in some time"
        )

    # Send the markdown table as a Chainlit message
    # await cl.Message(content=f"{response_message}").send()
    return response_message


def perform_search_based_qna(query):
    logger.info("calling search to get context for the response ....")
    credential = AzureKeyCredential(DefaultConfig.ai_search_key)

    client = SearchClient(
        endpoint=DefaultConfig.ai_search_url,
        index_name=DefaultConfig.ai_index_name,
        credential=credential,
    )
    # client = init_search_connection()
    response = client.search(
        search_text=query,
        query_type="semantic",
        semantic_configuration_name=DefaultConfig.ai_semantic_config,
    )

    response_docs = ""
    counter = 0
    results = list(response)

    # iterate through all search results
    for result in results:
        logger.info(
            f"search result from document: {result['title']}\n {result['chunk']}  "
        )
        response_docs += (
            " --- Document context start ---"
            + result["chunk"]
            + "\n ---End of Document ---\n"
        )
        counter += 1
        if counter == 2:
            break

    # logger.info(f"search results from the SOW Archives are : \n {response_docs}")
    logger.info("***********  calling LLM now ....***************")
    return response_docs


def get_mark_status_summary(user_name):
    response_message = ""
    cursor = None
    logger.info(
        f"calling the database to fetch mark status summary for  student{user_name}"
    )
    l_connection = init_database_connection()
    try:
        cursor = l_connection.cursor()
        query = "SELECT [StudentID],[Name],[Branch],[Semester],[Subject],[Score],[Grade],[Attendance] FROM StudentAcademics WHERE Name = ?;"
        cursor.execute(query, user_name)
        logger.info("executed query successfully")
        response_message += ""

        table_rows = ""
        # Build markdown table
        table_header = "| StudentID| Name | Branch | Semester | Subject |Score |Grade |Attendance|\n"
        table_separator = "| --- | --- | --- | --- | --- |---|---|---| \n"
        table_rows = ""

        for row in cursor:
            table_rows += f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} |{row[5]} |{row[6]} |{row[7]} |\n"

        markdown_table = table_header + table_separator + table_rows

        # Send the markdown table as a Chainlit message
        # await cl.Message(content=f"Here is your game status summary:\n\n{markdown_table}").send()
        l_connection.close()
    except Exception as e:
        logger.error(f"Error in database query execution: {e}")
        response_message = "We had an issue retrieving your mark status. Please check back in some time"
    return markdown_table


available_functions = {
    "perform_search_based_qna": perform_search_based_qna,
    "get_mark_status_summary": get_mark_status_summary,
    "get_grievance_status_def": get_grievance_status_def,
    "register_user_grievance_def": register_user_grievance_def,
}

