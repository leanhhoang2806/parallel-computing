from pydantic import BaseModel


class InternalParameters(BaseModel):
    wait_time: int

class WorkerInfo(BaseModel):
    host: str
    port: int

class SchedulerInfo(BaseModel):
    host: str
    port: int