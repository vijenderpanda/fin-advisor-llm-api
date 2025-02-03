from typing import Union

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from fin_advisor_llm_api.app.api.routes import router



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Hello": "World"}



app.include_router(router)



if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
