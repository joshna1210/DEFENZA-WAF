import uvicorn
import os

if __name__ == "__main__":
    port = int(os.getenv("PROXY_PORT", 9000))
    uvicorn.run("app.proxy_server:app", host="0.0.0.0", port=port, reload=True)
