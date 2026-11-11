from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    Email: str = Field(min_length=3, max_length=100)
    Password: str


class employeecreate(BaseModel):
    Employee_Id: int
    Employee_Name: str = Field(min_length=1, max_length=100)
    Email: str = Field(min_length=3, max_length=100)
    Phone: str = Field(min_length=3, max_length=20)
    Department: str = Field(min_length=1, max_length=100)
    Designation: str = Field(min_length=1, max_length=100)


class employeeresponse(BaseModel):
    Employee_Id: int
    Employee_Name: str | None = None
    Email: str | None = None
    Phone: str | None = None
    Department: str | None = None
    Designation: str | None = None
    model_config = ConfigDict(from_attributes=True)


class employeecreateresponse(BaseModel):
    message: str
    Employee_Id: int
    Employee_Name: str | None = None
    Email: str | None = None
    Phone: str | None = None
    Department: str | None = None
    Designation: str | None = None
    model_config = ConfigDict(from_attributes=True)


class attendancecreate(BaseModel):
    Employee_Id: int
    Status: Literal["Present", "Absent", "Half Day", "Leave"]


class attendanceresponse(BaseModel):
    Attendance_Id: int
    Employee_Id: int
    Attendance_Date: date
    Status: str
    model_config = ConfigDict(from_attributes=True)


class attendancecreateresponse(BaseModel):
    message: str
    Attendance_Id: int
    Employee_Id: int
    Attendance_Date: date
    Status: str
    model_config = ConfigDict(from_attributes=True)


class leavecreate(BaseModel):
    From_Date: date
    To_Date: date
    Leave_Type: str
    Reason: str
    Status: Literal["Pending", "Approved", "Rejected"] = "Pending"


class leaveresponse(BaseModel):
    Leave_Id: int
    Employee_Id: int
    From_Date: date
    To_Date: date
    Leave_Type: str
    Reason: str
    Status: str
    Reviewed_By: int | None = None
    Reviewed_At: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class leavecreateresponse(BaseModel):
    message: str
    Leave_Id: int
    Employee_Id: int
    From_Date: date
    To_Date: date
    Leave_Type: str
    Reason: str
    Status: str
    Reviewed_By: int | None = None
    Reviewed_At: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class usercreate(BaseModel):
    Employee_Id: int
    Full_Name: str = Field(min_length=1, max_length=100)
    Email: str = Field(min_length=3, max_length=100)
    Phone: str = Field(min_length=3, max_length=20)
    Password: str = Field(min_length=4, max_length=128)
    Department: str = Field(min_length=1, max_length=100)
    Designation: str = Field(min_length=1, max_length=100)
    Manager_Id: int


class userresponse(BaseModel):
    Message: str
    User_Id: int
    Full_Name: str
    Email: str
    Phone: str
    Employee_Id: int
    Department: str
    Designation: str
    Manager_Id: int
    Role_Id: int
    Is_Active: bool
    Created_At: datetime
    model_config = ConfigDict(from_attributes=True)


class rolecreate(BaseModel):
    Role_Name: str = Field(min_length=1, max_length=50)


class roleresponse(BaseModel):
    Role_Id: int
    Role_Name: str
    model_config = ConfigDict(from_attributes=True)


class managercreate(BaseModel):
    Full_Name: str = Field(min_length=1, max_length=100)
    Email: str = Field(min_length=3, max_length=100)
    Phone: str = Field(min_length=3, max_length=20)
    Password: str = Field(min_length=4, max_length=128)


class managerresponse(BaseModel):
    message: str
    User_Id: int
    Full_Name: str
    Email: str
    Phone: str
    Role_Id: int
    Is_Active: bool
    Created_At: datetime
    model_config = ConfigDict(from_attributes=True)


class leaveReview(BaseModel):
    Status: Literal["Approved", "Rejected"]


class PasswordReset(BaseModel):
    Temporary_Password: str
    New_Password: str = Field(min_length=8, max_length=128)


class ManagerListItem(BaseModel):
    User_Id: int
    Full_Name: str
    Email: str | None = None
    Phone: str | None = None
    Is_Active: bool
    Total_Employees: int
    Active_Employees: int
    Inactive_Employees: int
    model_config = ConfigDict(from_attributes=True)


class ManagerProfileResponse(BaseModel):
    User_Id: int
    Full_Name: str
    Email: str | None = None
    Phone: str | None = None
    Role_Name: str
    Is_Active: bool
    Total_Employees: int
    Active_Employees: int
    Inactive_Employees: int
    model_config = ConfigDict(from_attributes=True)


class ManagerEmployeeItem(BaseModel):
    Employee_Id: int
    Employee_Name: str | None = None
    Email: str | None = None
    Phone: str | None = None
    Department: str | None = None
    Designation: str | None = None
    Is_Active: bool
    Manager_Id: int | None = None
    Manager_Name: str | None = None
    model_config = ConfigDict(from_attributes=True)


class EmployeeListItem(BaseModel):
    Employee_Id: int
    Employee_Name: str | None = None
    Email: str | None = None
    Phone: str | None = None
    Department: str | None = None
    Designation: str | None = None
    Manager_Id: int | None = None
    Manager_Name: str | None = None
    User_Id: int | None = None
    Is_Active: bool
    model_config = ConfigDict(from_attributes=True)

