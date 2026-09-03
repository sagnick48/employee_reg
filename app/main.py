import uuid
from fastapi import FastAPI, HTTPException, status
from sqlalchemy.orm import Session
from .database import Base, SessionLocal, employees_collection, get_db_type, set_db_type, sql_engine
from .models import Employee
from .schemas import EmployeeCreate, EmployeePatch, EmployeeResponse, EmployeeUpdate
app = FastAPI(title="Employee Registration API", version="1.0.0")
Base.metadata.create_all(bind=sql_engine)
@app.get("/")
async def root():
    return {"message": "Employee API is running", "db_type": get_db_type()}

@app.post("/db-switch")
async def switch_database(db_type: str):
    db_type = db_type.lower()

    if db_type not in ["sql", "nosql"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="db_type must be either 'sql' or 'nosql'")

    set_db_type(db_type)

    return {"message": "Database switched successfully", "db_type": get_db_type()}

@app.get("/db-switch")
async def current_database():
    return {"db_type": get_db_type()}

@app.post("/employees", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(employee: EmployeeCreate):
    employee_id = str(uuid.uuid4())

    if get_db_type() == "sql":
        db: Session = SessionLocal()

        try:
            existing_employee = db.query(Employee).filter(Employee.email == employee.email).first()

            if existing_employee:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Employee with this email already exists")

            new_employee = Employee(id=employee_id, name=employee.name, email=employee.email, department=employee.department)

            db.add(new_employee)
            db.commit()
            db.refresh(new_employee)

            return new_employee

        finally:
            db.close()

    existing_employee = await employees_collection.find_one({"email": employee.email})

    if existing_employee:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Employee with this email already exists")

    employee_document = {
        "id": employee_id,
        "name": employee.name,
        "email": employee.email,
        "department": employee.department,
    }

    await employees_collection.insert_one(employee_document)

    return employee_document

@app.get("/employees", response_model=list[EmployeeResponse])
async def get_employees():
    if get_db_type() == "sql":
        db: Session = SessionLocal()

        try:
            return db.query(Employee).all()

        finally:
            db.close()

    employees = []
    cursor = employees_collection.find()

    async for employee in cursor:
        employees.append({
            "id": employee["id"],
            "name": employee["name"],
            "email": employee["email"],
            "department": employee["department"],
        })

    return employees

@app.get("/employees/{employee_id}", response_model=EmployeeResponse)
async def get_employee(employee_id: str):
    if get_db_type() == "sql":
        db: Session = SessionLocal()

        try:
            employee = db.query(Employee).filter(Employee.id == employee_id).first()

            if not employee:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

            return employee

        finally:
            db.close()

    employee = await employees_collection.find_one({"id": employee_id})

    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    return {
        "id": employee["id"],
        "name": employee["name"],
        "email": employee["email"],
        "department": employee["department"],
    }

@app.put("/employees/{employee_id}", response_model=EmployeeResponse)
async def update_employee(employee_id: str, employee_data: EmployeeUpdate):
    if get_db_type() == "sql":
        db: Session = SessionLocal()

        try:
            employee = db.query(Employee).filter(Employee.id == employee_id).first()

            if not employee:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

            existing_employee = db.query(Employee).filter(Employee.email == employee_data.email, Employee.id != employee_id).first()

            if existing_employee:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Another employee already uses this email")

            employee.name = employee_data.name
            employee.email = employee_data.email
            employee.department = employee_data.department

            db.commit()
            db.refresh(employee)

            return employee

        finally:
            db.close()

    employee = await employees_collection.find_one({"id": employee_id})

    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    existing_employee = await employees_collection.find_one({
        "email": employee_data.email,
        "id": {"$ne": employee_id},
    })

    if existing_employee:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Another employee already uses this email")

    updated_employee = {
        "id": employee_id,
        "name": employee_data.name,
        "email": employee_data.email,
        "department": employee_data.department,
    }

    await employees_collection.replace_one({"id": employee_id}, updated_employee)

    return updated_employee

@app.patch("/employees/{employee_id}", response_model=EmployeeResponse)
async def patch_employee(employee_id: str, employee_data: EmployeePatch):
    update_data = employee_data.model_dump(exclude_unset=True)

    if get_db_type() == "sql":
        db: Session = SessionLocal()

        try:
            employee = db.query(Employee).filter(Employee.id == employee_id).first()

            if not employee:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

            if "email" in update_data:
                existing_employee = db.query(Employee).filter(Employee.email == update_data["email"], Employee.id != employee_id).first()

                if existing_employee:
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Another employee already uses this email")

            for field, value in update_data.items():
                setattr(employee, field, value)

            db.commit()
            db.refresh(employee)

            return employee

        finally:
            db.close()

    employee = await employees_collection.find_one({"id": employee_id})

    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    if "email" in update_data:
        existing_employee = await employees_collection.find_one({
            "email": update_data["email"],
            "id": {"$ne": employee_id},
        })

        if existing_employee:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Another employee already uses this email")

    if update_data:
        await employees_collection.update_one({"id": employee_id}, {"$set": update_data})

    updated_employee = await employees_collection.find_one({"id": employee_id})

    return {
        "id": updated_employee["id"],
        "name": updated_employee["name"],
        "email": updated_employee["email"],
        "department": updated_employee["department"],
    }

@app.delete("/employees/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(employee_id: str):
    if get_db_type() == "sql":
        db: Session = SessionLocal()

        try:
            employee = db.query(Employee).filter(Employee.id == employee_id).first()

            if not employee:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

            db.delete(employee)
            db.commit()

            return None

        finally:
            db.close()
    result = await employees_collection.delete_one({"id": employee_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    return None