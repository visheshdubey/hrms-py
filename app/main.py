from fastapi import FastAPI

app = FastAPI(title="HRMS API", version="0.1.0")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "hrms-py service is running"}


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
