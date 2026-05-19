#!/bin/bash
# 智能获取 PostgreSQL 连接地址
# 若 localhost 端口映射可达则用 localhost，否则获取 Docker 容器 IP 直连

if command -v pg_isready >/dev/null 2>&1 && pg_isready -h localhost -p ${DB_PORT:-15432} >/dev/null 2>&1; then
    echo "localhost"
else
    CONTAINER_IP=$(docker inspect WeKnora-postgres-dev -f '{{(index .NetworkSettings.Networks "bridge").IPAddress}}' 2>/dev/null)
    if [ -z "$CONTAINER_IP" ]; then
        CONTAINER_IP=$(docker inspect WeKnora-postgres-dev -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' 2>/dev/null | head -1 | tr -d '[:space:]')
    fi
    if [ -n "$CONTAINER_IP" ]; then
        echo "$CONTAINER_IP"
    else
        echo "localhost"
    fi
fi