# langchain_rag.py

import os

from langchain_groq import ChatGroq
from langchain_community.document_loaders import TextLoader
from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

# Upewnij się, że poniższa ścieżka jest poprawna
file_path = os.path.join(os.path.dirname(__file__), 'Chatbot.txt')

if not os.path.exists(file_path):
    raise RuntimeError(f"Error loading {file_path}")

os.environ["GROQ_API_KEY"] = ''

HUGGINGFACEHUB_API_TOKEN = ''

docs = TextLoader(file_path).load()

embeddings = HuggingFaceInferenceAPIEmbeddings(
    api_key=HUGGINGFACEHUB_API_TOKEN, model_name="sentence-transformers/all-MiniLM-l6-v2"
)

llm = ChatGroq(model="llama3-8b-8192")

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
splits = text_splitter.split_documents(docs)
vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings)
retriever = vectorstore.as_retriever()

system_prompt = (
    "You are an Assystem AI of the question-answer type named Sakura who answers questions related to reservations and guides about Japan "
    "Use the following pieces of retrieved context to answer "
    "the question. If you don't know the answer, say that you "
    "don't know. Use three sentences maximum and keep the "
    "answer concise."
    "\n\n"
    "{context}"
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{input}"),
    ]
)

question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain)

class LangChainRAG:
    def __init__(self):
        self.chain = rag_chain

    def get_answer(self, input_text):
        print(input_text)
        response = self.chain.invoke({"input": input_text})
        print(response)
        return response["answer"]
