from dotenv import load_dotenv

from langchain_community.vectorstores.pgvector import PGVector
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.runnables import RunnableParallel
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import get_buffer_string
from operator import itemgetter


# from fin_advisor_llm_api.app.prompts import prompt as system_prompts

from test_prompt import generate_system_prompt, reflective_system_prompt


load_dotenv()
llm = ChatOpenAI(temperature=0)

config = {"configurable": {"session_id": "test123456"}}

# vector_store = PGVector(
#     collection_name="vijender_intro",
#     connection_string="postgresql://neondb_owner:npg_I4RYFuxEd8tv@ep-restless-forest-a5h95qgf-pooler.us-east-2.aws.neon.tech/neondb",
#     embedding_function=OpenAIEmbeddings()
# )

postgres_memory_url = "postgresql://neondb_owner:npg_y8IjUwmbv0sW@ep-flat-glade-a4m83cg4-pooler.us-east-1.aws.neon.tech/neondb"
get_session_history = lambda session_id: SQLChatMessageHistory(
    connection_string=postgres_memory_url,
    session_id=session_id
)


prompt = ChatPromptTemplate.from_messages([
    ("system", generate_system_prompt),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}")
])






generate_chain = (
    {
        "question": itemgetter("question"),
        "history": itemgetter("history"),
        "critique_output": itemgetter("critique_output")
    }
    | prompt
    | llm
    | StrOutputParser()
)



generate_chain_with_history = RunnableWithMessageHistory(
    generate_chain,
    lambda session_id: SQLChatMessageHistory(
        connection_string=postgres_memory_url,
        session_id=session_id
    ),
    input_messages_key="question",
    history_messages_key="history",
    critique_messages_key="critique_output"
)

critique_output = ""
generated_output = generate_chain_with_history.invoke(
    {"question": "Hi , I have income of 190000 INr as salaried emp;oyee , from which expenses/liabilities are of 110000 INR including my home loan emi , saving is 0 INR , and i am seeking help for the improve my current situation.", "critique_output": critique_output},
    config=config
)

print(generated_output)

reflective_prompt = ChatPromptTemplate.from_messages([
    ("system", reflective_system_prompt),
    ("human", "{generated_output}")
])

from langchain_core.output_parsers import JsonOutputParser
from langchain.schema import OutputParserException
import json

class ReflectiveJsonOutputParser(JsonOutputParser):
    def parse(self, text: str) -> dict:
        """Parse the output text into a JSON object with required keys."""
        try:
            # Parse the JSON text
            parsed = super().parse(text)
            
            # Check for required keys
            required_keys = ["output", "status"]
            missing_keys = [key for key in required_keys if key not in parsed]
            if missing_keys:
                raise OutputParserException(f"Missing required keys: {missing_keys}")
            
            # Validate status value
            if parsed["status"] not in ["IN_PROGRESS", "DONE"]:
                raise OutputParserException(
                    'Status must be either "IN_PROGRESS" or "DONE"'
                )
            
            return parsed
        except json.JSONDecodeError as e:
            raise OutputParserException(f"Failed to parse JSON: {e}")




reflective_chain = (
    {
        "generated_output": itemgetter("generated_output")
    }
    | reflective_prompt
    | llm
    | ReflectiveJsonOutputParser()
)


critique_response = reflective_chain.invoke(
    {"generated_output": generated_output}
)

print("critique response ----------------- \n", critique_response)








