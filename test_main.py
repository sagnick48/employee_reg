from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert "message" in response.json()
    assert "db_type" in response.json()


def test_get_current_database():
    response = client.get("/db-switch")

    assert response.status_code == 200
    assert response.json()["db_type"] in ["sql", "nosql"]


def test_switch_database_to_sql():
    response = client.post("/db-switch?db_type=sql")

    assert response.status_code == 200
    assert response.json()["db_type"] == "sql"


def test_switch_database_to_nosql():
    response = client.post("/db-switch?db_type=nosql")

    assert response.status_code == 200
    assert response.json()["db_type"] == "nosql"


def test_switch_database_invalid():
    response = client.post("/db-switch?db_type=invalid")

    assert response.status_code == 400


def test_create_employee():
    # Use SQL database for this simple test
    client.post("/db-switch?db_type=sql")

    employee = {
        "name": "John Doe",
        "email": "john@example.com",
        "department": "IT",
    }

    response = client.post("/employees", json=employee)

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "John Doe"
    assert data["email"] == "john@example.com"
    assert data["department"] == "IT"
    assert "id" in data


def test_get_employees():
    client.post("/db-switch?db_type=sql")

    response = client.get("/employees")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_employee_not_found():
    client.post("/db-switch?db_type=sql")

    response = client.get("/employees/non-existing-id")

    assert response.status_code == 404


def test_update_employee_not_found():
    client.post("/db-switch?db_type=sql")

    employee = {
        "name": "Updated Name",
        "email": "updated@example.com",
        "department": "HR",
    }

    response = client.put("/employees/non-existing-id", json=employee)

    assert response.status_code == 404


def test_patch_employee_not_found():
    client.post("/db-switch?db_type=sql")

    response = client.patch(
        "/employees/non-existing-id",
        json={"name": "Updated Name"},
    )

    assert response.status_code == 404


def test_delete_employee_not_found():
    client.post("/db-switch?db_type=sql")

    response = client.delete("/employees/non-existing-id")

    assert response.status_code == 404
