import os
import re
from operator import itemgetter

from langchain_groq import ChatGroq
from langchain_community.utilities.sql_database import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough

os.environ["GROQ_API_KEY"] = ''

llm = ChatGroq(model="llama3-8b-8192")
db = SQLDatabase.from_uri("postgresql://postgres:admin@localhost:5432/JapanTravel")

def extract_sql_code(text):
    pattern = r'\[(.*?)\]'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1)
    else:
        return "Brak zapytania"

tables_to_query = ["myapp_guideprofile", "myapp_rating", "myapp_userprofile", "myapp_reservation", "myapp_customuser"]
structure_database = db.get_table_info(table_names=tables_to_query)

answer_prompt = PromptTemplate.from_template(
    """You are an agent designed to interact with a SQL database. Given an input question, create a syntactically correct SQLite query and store that query MUST BE ALWAYS between []
If you get an error while executing the query, rewrite the query and try again.

DO NOT create any DML statements (INSERT, UPDATE, DELETE, DROP, etc.) in the database

Based on the database structure, which is given below as SQL code, create SQL queries for the given question
{structure_database}

Ignore the password, is_superuser, is_staff and is_active columns in the myapp_customuser table

Question: {question}
Answer:
"""
).partial(structure_database=structure_database)

sql_prompt = PromptTemplate.from_template(
    """You are an agent designed to create responses to the generated results by SQL code.
You will be given a Question that was tasked with generating a SQL query, the SQL query itself
and the result of this query with column names, data and calculations such as number or sum

Question:
{Question}

SQL Query:
{Query}

SQL Query Result:
{Final}
"""
)

parser = StrOutputParser()

chain = (
    RunnablePassthrough.assign(query=create_sql_query_chain(llm, db)).assign(
        result=itemgetter("query") | QuerySQLDataBaseTool(db=db)
    )
    | answer_prompt
    | llm
    | StrOutputParser()
)

class LangChainSQL:
    def __init__(self):
        self.chain = chain
        self.sql_prompt_chain = sql_prompt | llm | parser

    def get_answer(self, input_text):
        code_sql = self.chain.invoke({"question": input_text})
        sql_code = extract_sql_code(code_sql)
        answer_sql = db.run(sql_code, include_columns=True)
        res = self.sql_prompt_chain.invoke({"Question": input_text, "Query": sql_code, "Final": answer_sql})
        return {"sql_code": sql_code, "answer_sql": answer_sql, "res": res}
