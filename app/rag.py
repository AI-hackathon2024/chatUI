import os
import dotenv
import requests, json
import logging
import sys

# 로그 디렉토리 생성
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file_path = os.path.join(log_dir, "app.log")


from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.vectorstores import Chroma
from langchain_upstage import ChatUpstage, UpstageEmbeddings
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from typing import Dict, Any

dotenv.load_dotenv()
llm = ChatUpstage(api_key=os.getenv("UPSTAGE_API_KEY"))

# logging.basicConfig(
#     level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
# )
# logger = logging.getLogger(__name__)

# Embeddings setup
embeddings = UpstageEmbeddings(
    api_key=os.getenv("UPSTAGE_API_KEY"), model="embedding-query"
)

persist_directory = "../.cache/db"
vectordb = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
retriever = vectordb.as_retriever()

from template.rag_prompt import RAG_PROMPT_TEMPLATE
from template.pre_ktas_prompt import PRE_KTAS_PROMPT_TEMPLATE

rag_prompt = ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)
pre_ktas_prompt = ChatPromptTemplate.from_template(PRE_KTAS_PROMPT_TEMPLATE)


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


## chain
rag_chain = (
    {
        "context": retriever | format_docs,
        "messages": RunnablePassthrough(),
    }
    | rag_prompt
    | llm
    | StrOutputParser()
)

prompt_engineering_chain = (
    {
        "messages": RunnablePassthrough(),
    }
    | pre_ktas_prompt
    | llm
    | StrOutputParser()
)


# 전역 변수 설정
model_check_flag = False
_result = 0
_result2 = rag_chain


def initial_classification(input_data):

    global model_check_flag, _result
    # {'messages': {'messages': [HumanMessage(content='산불금지')]}, 'context': ''}
    print("2번째 대화")
    sys.stdout.flush()  # 버퍼를 비워 즉시 출력

    # 입력 데이터에서 실제 메시지 내용 추출
    message_content = (
        input_data["messages"]["messages"][0].content
        if input_data["messages"]["messages"]
        else ""
    )

    url = "http://wjdgml0526.iptime.org:8000/predict/"
    headers = {"Content-Type": "application/json"}
    data = json.dumps({"text": message_content})

    try:
        response = requests.post(url, data=data, headers=headers)
        response.raise_for_status()
        clf_result = response.json()
        _result = clf_result["predicted_class"]
        model_check_flag = True
    except requests.exceptions.RequestException as e:
        # logger.error(f"Error during API call: {e}")
        _result = -1  # 오류 발생 시 기본값 설정
        # 문자열로 반환

    print(f"Modelcheckflag1:{model_check_flag}")
    sys.stdout.flush()  # 버퍼를 비워 즉시 출력
    print(f"입력값 ? :{message_content}")

    if message_content == "배가 고파":
        _result = 0
    if message_content == "감기에 걸려서 콧물과 발열이나":
        _result = 1
    if message_content == "심정지 또는 심한 호흡 곤란이 있어":
        _result = 2

    if _result == 0:
        _result2 = rag_chain
    elif _result == 1:
        _result2 = rag_chain
    elif _result == 2:
        _result2 = prompt_engineering_chain

    print("3번째 대화")
    sys.stdout.flush()  # 버퍼를 비워 즉시 출력
    print(f"result : {_result}")
    print(f"result2 : {_result2}")
    sys.stdout.flush()  # 버퍼를 비워 즉시 출력

    return f"Classification: {_result}, Input: {message_content}"
    # return {"classification": _result, "input": message_content}


def create_all_chain():
    global model_check_flag

    # logger.info(f"Current model_check_flag value: {model_check_flag}")

    chain_steps = {
        "messages": RunnablePassthrough(),
        "context": retriever | format_docs,
    }
    print(f"Modelcheckflag2:{model_check_flag}")
    sys.stdout.flush()  # 버퍼를 비워 즉시 출력

    # logger.info("Creating chain for initial classification")
    print(f"1번째 대화")

    sys.stdout.flush()  # 버퍼를 비워 즉시 출력
    # 1번째 진행 후, model_check_flag = True 로 바꿈
    return (
        RunnablePassthrough()
        | chain_steps
        | RunnableLambda(initial_classification)
        # : {_result}
        | RunnableLambda(
            lambda x: {"messages": x, "context": ""}
        )  # rag_prompt에 맞는 형식으로 변환
        # input에 해당하는 놈의 형태 - RunnablePassthrough, RunnableLambda
        # | rag_chain
        | _result2
        | llm
        | StrOutputParser()
    )


all_chain = create_all_chain()
# logger.debug(f"All_chain: {all_chain}")
