#!/bin/bash

# docker-start.sh
echo "도커 빌드 및 실행 스크립트"

# UPSTAGE_API_KEY 입력받기
read -p "Enter your UPSTAGE_API_KEY: " UPSTAGE_API_KEY
export UPSTAGE_API_KEY=$UPSTAGE_API_KEY

# 도커 컴포즈로 빌드 및 실행
docker-compose up --build