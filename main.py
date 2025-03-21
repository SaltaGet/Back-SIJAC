import uvicorn

if __name__ == "__main__":
    uvicorn.run("src:app", host="localhost", port=8000, log_level="debug", reload=True)