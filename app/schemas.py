from pydantic import BaseModel, ConfigDict, EmailStr
class EmployeeCreate(BaseModel):
    name: str
    email: EmailStr
    department: str

class EmployeeUpdate(BaseModel):
    name: str
    email: EmailStr
    department: str

class EmployeePatch(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    department: str | None = None

class EmployeeResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    department: str
    model_config = ConfigDict(
        from_attributes=True
    )
