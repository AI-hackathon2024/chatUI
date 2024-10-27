FROM --platform=linux/amd64 python:3.12-slim

WORKDIR /app

# 필요한 시스템 패키지 설치 (make 포함)
RUN apt-get update && \
    apt-get install -y make

COPY requirements.txt .

# 파이썬 환경 설정 및 패키지 설치
RUN python -m venv .venv && \
    . .venv/bin/activate && \
    pip install --upgrade pip

RUN pip install -r requirements.txt
RUN python -m pip install python-dotenv

# 필요한 파일들 복사
COPY Makefile .
COPY app/ ./app/
COPY preprocessing/ ./preprocessing/
COPY data/ ./data/    

# 환경변수 설정을 위한 ARG
ARG UPSTAGE_API_KEY
ENV UPSTAGE_API_KEY=${UPSTAGE_API_KEY}

# .env 파일 생성
RUN echo "UPSTAGE_API_KEY=${UPSTAGE_API_KEY}" > .env

# OCR 및 청킹 프로세스 실행
RUN make ocr && make chunk

# 포트 설정
EXPOSE 8000

# 앱 실행
CMD ["/bin/bash", "-c", "source .venv/bin/activate && python app/main.py"]