FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN pip install --no-cache-dir "mcp>=2,<3" "httpx==0.28.1"
WORKDIR /app
COPY mcp_server.py /app/mcp_server.py
USER 65532:65532
EXPOSE 18768
CMD ["python","/app/mcp_server.py","--host","0.0.0.0","--port","18768"]
LABEL org.opencontainers.image.source="https://github.com/GodsQuantum/Cloud9-GodsEye-MCP" org.opencontainers.image.title="Cloud9-GodsEye-MCP" org.opencontainers.image.description="Four contextual Gods Eye View MCP tools for remote clients" org.opencontainers.image.licenses="MIT"
