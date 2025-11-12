from server.main import app 

if __name__ == "__main__":
    import uvicorn
    from server.config import HOST, PORT, DEBUG
    uvicorn.run(app, host=HOST, port=PORT, log_level="debug" if DEBUG else "info")

