"""
Minimal Tutor service entrypoint for hackathon demos.

Run:
  python -m examples.tutor_service

Then call:
  POST /tutor/1559/explain
  POST /tutor/7702/explain
"""

from __future__ import annotations

import os

import uvicorn


def main() -> None:
    host = os.getenv("TUTOR_HOST", "0.0.0.0") #服务监听的网卡地址，0.0.0.0表示监听所有网卡，同局域网的其他设备也能访问
    port = int(os.getenv("TUTOR_PORT", "8009")) #默认端口，与前端请求一致
    reload_enabled = os.getenv("TUTOR_RELOAD", "0").lower() in {"1", "true", "yes"} #热更新

    uvicorn.run(
        "spoon_ai.tutor.service:app",
        host=host,
        port=port,
        reload=reload_enabled,
        log_level=os.getenv("TUTOR_LOG_LEVEL", "info"),
    )


if __name__ == "__main__":
    main()

