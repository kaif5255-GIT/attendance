
// Auto-detect local development server vs deployed API
const API_URL = (
    window.location.protocol === "http:" ||
    window.location.protocol === "https:"
)
    ? window.location.origin
    : "http://127.0.0.1:8000";

// Login form submission and role-based redirect
document.getElementById("loginForm").addEventListener("submit", async function (event) {
    event.preventDefault();
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const message = document.getElementById("message");
    try {
        const loginResponse = await fetch(`${API_URL}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ Email: email, Password: password })
        });
        const loginData = await loginResponse.json();
        if (!loginResponse.ok) {
            message.textContent = loginData.detail || "Login failed";
            return;
        }
        localStorage.setItem("access_token", loginData.access_token);
        localStorage.setItem("refresh_token", loginData.refresh_token);
        if (loginData.must_change_password) {
            window.location.href = "index.html?reset-password=true";
            return;
        }
        const userResponse = await fetch(`${API_URL}/auth/me`, {
            headers: { "Authorization": `Bearer ${loginData.access_token}` }
        });
        const userData = await userResponse.json();
        if (!userResponse.ok) {
            if (userResponse.status === 403) {
                window.location.href = "index.html?reset-password=true";
                return;
            }

            message.textContent = "Unable to retrieve user details";
            return;
        }
        const role = userData.Role_Name.toLowerCase();
        if (role === "admin") {
            window.location.href = "index.html?dashboard=admin";
        } else if (role === "manager") {
            window.location.href = "index.html?dashboard=manager";
        } else if (role === "employee") {
            window.location.href = "index.html?dashboard=employee";
        } else {
            message.textContent = "Unknown user role";
        }
    } catch (error) {
        message.textContent = "Cannot connect to the server. Check whether FastAPI is running.";
        console.error(error);
    }
});






// Switch visible dashboard view based on user role and query parameters
async function showDashboard() {
    const token = localStorage.getItem("access_token");
    const registerButton = document.getElementById("registerButton");

    if (registerButton) {
        registerButton.hidden = !!token;
    }

    const params = new URLSearchParams(window.location.search);
    const requestedDashboard = params.get("dashboard");

    if (params.get("reset-password") === "true") {
        document.getElementById("loginSection").hidden = true;
        document.getElementById("resetPasswordSection").hidden = false;
        return;
    }

    if (!token) {
        document.getElementById("loginSection").hidden = false;
        document.getElementById("adminDashboard").hidden = true;
        document.getElementById("managerDashboard").hidden = true;
        document.getElementById("employeeDashboard").hidden = true;
        return;
    }

    try {
        const response = await fetch(`${API_URL}/auth/me`, {
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        if (!response.ok) {
            if (response.status === 403) {
                window.location.href = "index.html?reset-password=true";
                return;
            }

            const refreshed = await refreshAccessToken();
            if (refreshed) {
                return showDashboard();
            }

            localStorage.removeItem("access_token");
            localStorage.removeItem("refresh_token");

            document.getElementById("loginSection").hidden = false;
            document.getElementById("adminDashboard").hidden = true;
            document.getElementById("managerDashboard").hidden = true;
            document.getElementById("employeeDashboard").hidden = true;
            return;
        }

        const user = await response.json();
        const actualRole = user.Role_Name.toLowerCase();

        if (actualRole === "admin") {
            loadManagers();
        }

        const rolePages = {
            admin: "admin",
            manager: "manager",
            employee: "employee"
        };

        if (!rolePages[actualRole]) {
            throw new Error("Unknown user role");
        }

        if (requestedDashboard !== actualRole) {
            window.location.replace(
                `index.html?dashboard=${rolePages[actualRole]}`
            );
            return;
        }

        document.getElementById("loginSection").hidden = true;
        document.getElementById("adminDashboard").hidden =
            actualRole !== "admin";
        document.getElementById("managerDashboard").hidden =
            actualRole !== "manager";
        document.getElementById("employeeDashboard").hidden =
            actualRole !== "employee";

    } catch (error) {
        console.error(error);

        document.getElementById("loginSection").hidden = false;
        document.getElementById("adminDashboard").hidden = true;
        document.getElementById("managerDashboard").hidden = true;
        document.getElementById("employeeDashboard").hidden = true;
    }
}



function backToDashboard() {
    const params = new URLSearchParams(window.location.search);
    const dashboard = params.get("dashboard");

    document.getElementById("adminDashboard").hidden = dashboard !== "admin";
    document.getElementById("managerDashboard").hidden = dashboard !== "manager";
    document.getElementById("employeeDashboard").hidden = dashboard !== "employee";
}





async function logout() {
    const token = localStorage.getItem("access_token");

    try {
        if (token) {
            await fetch(`${API_URL}/auth/logout`, {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            });
        }
    } catch (error) {
        console.error("Logout API request failed:", error);
    } finally {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.replace("index.html");
    }
}



document.getElementById("managerForm").addEventListener("submit", async function (event) {
    event.preventDefault();

    const message = document.getElementById("managerMessage");
    const token = localStorage.getItem("access_token");

    const managerData = {
        Full_Name: document.getElementById("managerName").value,
        Email: document.getElementById("managerEmail").value,
        Phone: document.getElementById("managerPhone").value,
        Password: document.getElementById("managerPassword").value
    };

    try {
        const response = await fetch(`${API_URL}/Admin/managers`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify(managerData)
        });

        const data = await response.json();

        if (!response.ok) {
            message.textContent = data.detail || "Failed to create manager";
            return;
        }

        message.textContent = data.message;
        document.getElementById("managerForm").reset();
        loadManagers();

    } catch (error) {
        console.error(error);
        message.textContent = "Unable to connect to the server";
    }
});


document.getElementById("registerEmployeeForm").addEventListener("submit", async event => {
    event.preventDefault();

    const message = document.getElementById("registerEmployeeMessage");

    const employeeData = {
        Employee_Id: Number(document.getElementById("registerEmployeeId").value),
        Full_Name: document.getElementById("registerEmployeeName").value,
        Email: document.getElementById("registerEmployeeEmail").value,
        Phone: document.getElementById("registerEmployeePhone").value,
        Password: document.getElementById("registerEmployeePassword").value,
        Manager_Id: Number(document.getElementById("registerEmployeeManager").value),
        Department: document.getElementById("registerEmployeeDepartment").value,
        Designation: document.getElementById("registerEmployeeDesignation").value
    };

    try {
        const response = await fetch(`${API_URL}/auth/register-employee`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${localStorage.getItem("access_token")}`
            },
            body: JSON.stringify(employeeData)
        });

        const data = await response.json();

        if (!response.ok) {
            message.textContent = data.detail || "Employee registration failed";
            return;
        }

        message.textContent = "Employee registered successfully!";
        event.target.reset();

    } catch (error) {
        console.error(error);
        message.textContent = "Unable to connect to the server";
    }
});

async function loadEmployees() {
    const token = localStorage.getItem("access_token");
    const dashboard = new URLSearchParams(window.location.search)
        .get("dashboard");

    const listId = dashboard === "manager"
        ? "managerEmployeeList"
        : "employeeList";

    const employeeList = document.getElementById(listId);
    employeeList.hidden = false;
    employeeList.textContent = "Loading employees...";

    try {
        const response = await fetch(`${API_URL}/employees`, {
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        const data = await response.json();

        if (!response.ok) {
            employeeList.textContent =
                data.detail || "Unable to load employees";
            return;
        }

        employeeList.replaceChildren();

        if (!Array.isArray(data) || data.length === 0) {
            employeeList.textContent = "No employees found";
            return;
        }

        data.forEach(employee => {
            const item = document.createElement("p");

            item.textContent =
                `ID: ${employee.Employee_Id} | ` +
                `Name: ${employee.Employee_Name} | ` +
                `Department: ${employee.Department} | ` +
                `Designation: ${employee.Designation}` +
                (employee.Is_Active === false ? " (Inactive)" : "");

            employeeList.appendChild(item);

            if (listId === "employeeList") {
                const deactivateButton = document.createElement("button");
                deactivateButton.textContent = employee.Is_Active === false ? "Deactivated" : "Deactivate";
                deactivateButton.type = "button";
                if (employee.Is_Active === false) {
                    deactivateButton.disabled = true;
                    deactivateButton.style.opacity = "0.5";
                }

                deactivateButton.addEventListener("click", function (event) {
                    event.preventDefault();
                    event.stopPropagation();
                    deactivateEmployee(employee.Employee_Id);
                });

                item.appendChild(deactivateButton);
            }
        });

    } catch (error) {
        console.error(error);
        employeeList.textContent = "Unable to connect to the server";
    }
}
async function deactivateEmployee(employeeId) {
    console.log("Deactivate clicked:", employeeId);
    if (!confirm(`Are you sure you want to deactivate Employee ${employeeId}?`)) {
        return;
    }

    const message = document.getElementById("deactivateEmployeeMessage");

    try {
        const result = await apiRequest(
            `/employees/${employeeId}/deactivate`,
            { method: "PUT" }
        );
        console.log("Deactivation response:", result);

        if (message) {
            message.textContent = result.message;
        }

        alert(result.message);
        await loadEmployees();

    } catch (error) {
        if (message) {
            message.textContent = error.message;
        }

        alert(error.message);
    }
}

async function loadPendingLeaves() {
    const token = localStorage.getItem("access_token");
    const list = document.getElementById("pendingLeaveList");
    list.hidden = false;

    list.textContent = "Loading pending leave requests...";

    try {
        const response = await fetch(
            `${API_URL}/managers/leave-requests`,
            {
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            }
        );

        const data = await response.json();

        if (!response.ok) {
            list.textContent = data.detail || "Unable to load leave requests";
            return;
        }

        list.replaceChildren();

        if (!Array.isArray(data) || data.length === 0) {
            list.textContent = "No pending leave requests found";
            return;
        }

        data.forEach(leave => {
            const card = document.createElement("div");
            card.className = "leave-card";

            const details = document.createElement("p");
            details.textContent =
                `Leave ID: ${leave.Leave_Id} | ` +
                `Employee ID: ${leave.Employee_Id} | ` +
                `From: ${leave.From_Date} | ` +
                `To: ${leave.To_Date} | ` +
                `Type: ${leave.Leave_Type} | ` +
                `Reason: ${leave.Reason} | ` +
                `Status: ${leave.Status}`;

            const approveButton = document.createElement("button");
            approveButton.textContent = "Approve";
            approveButton.onclick = () => reviewLeave(leave.Leave_Id, "Approved");

            const rejectButton = document.createElement("button");
            rejectButton.textContent = "Reject";
            rejectButton.onclick = () => reviewLeave(leave.Leave_Id, "Rejected");

            card.append(details, approveButton, rejectButton);
            list.appendChild(card);
        });

    } catch (error) {
        console.error(error);
        list.textContent = "Unable to connect to the server";
    }
}

async function reviewLeave(leaveId, status) {
    const token = localStorage.getItem("access_token");

    try {
        const response = await fetch(
            `${API_URL}/managers/leave-requests/${leaveId}/review`,
            {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({ Status: status })
            }
        );

        const data = await response.json();

        if (!response.ok) {
            alert(data.detail || "Unable to review leave request");
            return;
        }

        alert(data.message);
        loadPendingLeaves();

    } catch (error) {
        console.error(error);
        alert("Unable to connect to the server");
    }
}

async function loadMyProfile(containerId = "myProfile") {
    const token = localStorage.getItem("access_token");
    const profile = document.getElementById(containerId);

    profile.hidden = false;
    profile.textContent = "Loading profile...";

    try {
        const response = await fetch(`${API_URL}/auth/me`, {
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        const data = await response.json();
        if (!response.ok) {
            if (response.status === 401) {
                profile.textContent =
                    "Access token expired. Please refresh your session.";
            } else {
                profile.textContent = data.detail || "Unable to load profile";
            }
            return;
        }

        profile.replaceChildren();

        const fields = [
            ["User ID", data.User_Id],
            ["Full Name", data.Full_Name],
            ["Email", data.Email],
            ["Phone", data.Phone],
            ["Role", data.Role_Name]
        ];

        if (data.Employee_Id) fields.push(["Employee ID", data.Employee_Id]);
        if (data.Department) fields.push(["Department", data.Department]);
        if (data.Designation) fields.push(["Designation", data.Designation]);

        fields.forEach(([label, value]) => {
            const paragraph = document.createElement("p");
            paragraph.textContent = `${label}: ${value ?? "Not provided"}`;
            profile.appendChild(paragraph);
        });

    } catch (error) {
        console.error(error);
        profile.textContent = "Unable to connect to the server";
    }
}

function closeSection(sectionId) {
    document.getElementById(sectionId).hidden = true;
}

async function loadMyAttendance() {
    const token = localStorage.getItem("access_token");
    const container = document.getElementById("myAttendance");

    container.textContent = "Loading attendance...";
    container.hidden = false;
    try {
        const response = await fetch(`${API_URL}/attendance`, {
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        const data = await response.json();

        if (!response.ok) {
            container.textContent = data.detail || "Unable to load attendance";
            return;
        }

        container.replaceChildren();

        if (data.length === 0) {
            container.textContent = "No attendance records found";
            return;
        }

        data.forEach(record => {
            const item = document.createElement("p");
            item.textContent =
                `Date: ${record.Attendance_Date} | Status: ${record.Status}`;
            container.appendChild(item);
        });

    } catch (error) {
        console.error(error);
        container.textContent = "Unable to connect to the server";
    }
}


async function loadMyLeaves() {
    const token = localStorage.getItem("access_token");
    const container = document.getElementById("myLeaves");

    container.hidden = false;
    container.textContent = "Loading leave records...";

    try {
        const response = await fetch(`${API_URL}/leaves`, {
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        const data = await response.json();

        if (!response.ok) {
            container.textContent =
                data.detail || "Unable to load leave records";
            return;
        }

        container.replaceChildren();

        if (data.length === 0) {
            container.textContent = "No leave records found";
            return;
        }

        data.forEach(leave => {
            const card = document.createElement("div");
            card.className = "leave-card";

            const details = document.createElement("p");
            details.textContent =
                `Leave ID: ${leave.Leave_Id} | ` +
                `From: ${leave.From_Date} | ` +
                `To: ${leave.To_Date} | ` +
                `Type: ${leave.Leave_Type} | ` +
                `Reason: ${leave.Reason} | ` +
                `Status: ${leave.Status}`;

            card.appendChild(details);

            if (leave.Status === "Pending") {
                const updateButton = document.createElement("button");
                updateButton.textContent = "Update";
                updateButton.onclick = () => updateMyLeave(leave);

                const deleteButton = document.createElement("button");
                deleteButton.textContent = "Delete";
                deleteButton.onclick = () => deleteMyLeave(leave);

                card.append(updateButton, deleteButton);
            }

            container.appendChild(card);
        });

    } catch (error) {
        console.error(error);
        container.textContent = "Unable to connect to the server";
    }
}

document.getElementById("leaveForm").addEventListener("submit", async function (event) {
    event.preventDefault();

    const token = localStorage.getItem("access_token");
    const message = document.getElementById("leaveMessage");

    const leaveData = {
        From_Date: document.getElementById("fromDate").value,
        To_Date: document.getElementById("toDate").value,
        Leave_Type: document.getElementById("leaveType").value,
        Reason: document.getElementById("leaveReason").value
    };

    if (leaveData.To_Date < leaveData.From_Date) {
        message.textContent = "To date cannot be earlier than from date";
        return;
    }

    try {
        const response = await fetch(`${API_URL}/leaves`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify(leaveData)
        });

        const data = await response.json();

        if (!response.ok) {
            message.textContent = data.detail || "Failed to apply for leave";
            return;
        }

        message.textContent = data.message || "Leave request submitted successfully";
        document.getElementById("leaveForm").reset();

        loadMyLeaves();

    } catch (error) {
        console.error(error);
        message.textContent = "Unable to connect to the server";
    }
});





async function apiRequest(url, options = {}) {
    const token = localStorage.getItem("access_token");

    const response = await fetch(`${API_URL}${url}`, {
        ...options,
        headers: {
            ...(options.body ? { "Content-Type": "application/json" } : {}),
            "Authorization": `Bearer ${token}`,
            ...options.headers
        }
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || "Request failed");
    }

    return data;
}


async function getEmployeeById(role) {
    const idInput = document.getElementById(
        role === "admin" ? "adminEmployeeId" : "managerEmployeeId"
    );
    const container = document.getElementById(
        role === "admin" ? "adminEmployeeDetails" : "managerEmployeeDetails"
    );

    const id = idInput.value.trim();

    if (!id) {
        container.hidden = false;
        container.textContent = "Enter an employee ID";
        return;
    }

    container.hidden = false;
    container.textContent = "Loading...";

    try {
        const employee = await apiRequest(`/employee/${encodeURIComponent(id)}`);
        container.replaceChildren();

        [
            ["Employee ID", employee.Employee_Id],
            ["Name", employee.Employee_Name],
            ["Email", employee.Email],
            ["Phone", employee.Phone],
            ["Department", employee.Department],
            ["Designation", employee.Designation]
        ].forEach(([label, value]) => {
            const p = document.createElement("p");
            p.textContent = `${label}: ${value ?? "Not provided"}`;
            container.appendChild(p);
        });
    } catch (error) {
        container.textContent = error.message;
    }
}


async function loadAllAttendance() {
    const dashboard = new URLSearchParams(location.search).get("dashboard");
    const container = document.getElementById(
        dashboard === "manager" ? "managerAttendanceList" : "adminAttendanceList"
    );

    container.hidden = false;
    container.textContent = "Loading attendance...";

    try {
        const records = await apiRequest("/attendance");
        container.replaceChildren();

        if (!Array.isArray(records) || records.length === 0) {
            container.textContent = "No attendance records found";
            return;
        }

        records.forEach(record => {
            const p = document.createElement("p");
            p.textContent =
                `Employee ID: ${record.Employee_Id} | ` +
                `Date: ${record.Attendance_Date} | Status: ${record.Status}`;
            container.appendChild(p);
        });
    } catch (error) {
        container.textContent = error.message;
    }
}


async function getAttendanceByEmployeeId(role) {
    const idInput = document.getElementById(
        role === "admin" ? "adminAttendanceEmployeeId" : "managerAttendanceEmployeeId"
    );
    const container = document.getElementById(
        role === "admin" ? "adminEmployeeAttendance" : "managerEmployeeAttendance"
    );

    const id = idInput.value.trim();

    if (!id) {
        container.hidden = false;
        container.textContent = "Enter an employee ID";
        return;
    }

    container.hidden = false;
    container.textContent = "Loading attendance...";

    try {
        const records = await apiRequest(
            `/attendance/employee/${encodeURIComponent(id)}`
        );

        container.replaceChildren();

        if (!Array.isArray(records) || records.length === 0) {
            container.textContent = "No attendance records found for this employee";
            return;
        }

        records.forEach(record => {
            const p = document.createElement("p");
            p.textContent =
                `Attendance ID: ${record.Attendance_Id} | ` +
                `Date: ${record.Attendance_Date} | Status: ${record.Status}`;
            container.appendChild(p);
        });
    } catch (error) {
        container.textContent = error.message;
    }
}


document.getElementById("updateEmployeeForm").addEventListener("submit", async event => {
    event.preventDefault();

    const message = document.getElementById("updateEmployeeMessage");
    const id = document.getElementById("updateEmployeeId").value;

    const employeeData = {
        Employee_Id: Number(id),
        Employee_Name: document.getElementById("updateEmployeeName").value,
        Email: document.getElementById("updateEmployeeEmail").value,
        Phone: document.getElementById("updateEmployeePhone").value,
        Department: document.getElementById("updateEmployeeDepartment").value,
        Designation: document.getElementById("updateEmployeeDesignation").value
    };

    try {
        const result = await apiRequest(`/employees/${encodeURIComponent(id)}`, {
            method: "PUT",
            body: JSON.stringify(employeeData)
        });

        message.textContent = result.message || "Employee updated successfully";
        event.target.reset();
    } catch (error) {
        message.textContent = error.message;
    }
});


async function deleteEmployee() {
    const id = document.getElementById("deleteEmployeeId").value;
    const message = document.getElementById("deleteEmployeeMessage");

    if (!id) {
        message.textContent = "Enter an employee ID";
        return;
    }

    if (!confirm(`Delete employee ${id}?`)) return;

    try {
        const result = await apiRequest(`/employees/${encodeURIComponent(id)}`, {
            method: "DELETE"
        });

        message.textContent = result.message || "Employee deleted successfully";
        document.getElementById("deleteEmployeeId").value = "";
    } catch (error) {
        message.textContent = error.message;
    }
}


document.getElementById("markAttendanceForm")?.addEventListener("submit", async event => {
    event.preventDefault();

    const message = document.getElementById("markAttendanceMessage");
    const attendanceData = {
        Employee_Id: Number(document.getElementById("markAttendanceEmployeeId").value),
        Status: document.getElementById("markAttendanceStatus").value
    };

    try {
        const result = await apiRequest("/attendance", {
            method: "POST",
            body: JSON.stringify(attendanceData)
        });

        message.textContent = result.message || "Attendance marked successfully";
        event.target.reset();
    } catch (error) {
        message.textContent = error.message;
    }
});


document.getElementById("updateAttendanceForm")?.addEventListener("submit", async event => {
    event.preventDefault();

    const message = document.getElementById("updateAttendanceMessage");
    const id = document.getElementById("updateAttendanceEmployeeId").value;
    const attendanceData = {
        Employee_Id: Number(id),
        Status: document.getElementById("updateAttendanceStatus").value
    };

    try {
        const result = await apiRequest(`/attendance/${encodeURIComponent(id)}`, {
            method: "PUT",
            body: JSON.stringify(attendanceData)
        });

        message.textContent = result.message || "Attendance updated successfully";
        event.target.reset();
    } catch (error) {
        message.textContent = error.message;
    }
});


document.getElementById("deleteAttendanceForm")?.addEventListener("submit", async event => {
    event.preventDefault();

    const message = document.getElementById("deleteAttendanceMessage");
    const id = document.getElementById("deleteAttendanceEmployeeId").value;
    const date = document.getElementById("deleteAttendanceDate").value;

    if (!confirm(`Delete attendance for employee ${id} on ${date}?`)) return;

    try {
        const result = await apiRequest(
            `/attendance/${encodeURIComponent(id)}/${encodeURIComponent(date)}`,
            { method: "DELETE" }
        );

        message.textContent = result.message || "Attendance deleted successfully";
        event.target.reset();
    } catch (error) {
        message.textContent = error.message;
    }
});


async function loadAllLeaves() {
    const container = document.getElementById("adminLeaveList");
    container.hidden = false;
    container.textContent = "Loading leave records...";

    try {
        const records = await apiRequest("/leaves");
        container.replaceChildren();

        if (!Array.isArray(records) || records.length === 0) {
            container.textContent = "No leave records found";
            return;
        }

        records.forEach(leave => {
            const p = document.createElement("p");
            p.textContent =
                `Leave ID: ${leave.Leave_Id} | ` +
                `Employee ID: ${leave.Employee_Id} | ` +
                `From: ${leave.From_Date} | To: ${leave.To_Date} | ` +
                `Type: ${leave.Leave_Type} | Reason: ${leave.Reason} | ` +
                `Status: ${leave.Status}`;
            container.appendChild(p);
        });
    } catch (error) {
        container.textContent = error.message;
    }
}

function backToLogin() {
    document.querySelectorAll(".dashboard").forEach(dashboard => {
        dashboard.hidden = true;
    });

    const resetSec = document.getElementById("resetPasswordSection");
    if (resetSec) resetSec.hidden = true;

    document.getElementById("loginForm").reset();
    document.getElementById("message").textContent = "";

    document.getElementById("loginForm").parentElement.hidden = false;
    window.history.replaceState({}, document.title, window.location.pathname);
}


document.addEventListener("DOMContentLoaded", async () => {
    const token = localStorage.getItem("access_token");

    if (token) {
        await showDashboard();
    }
});


async function updateMyLeave(leave) {
    const container = document.getElementById("myLeaves");

    container.replaceChildren();

    const form = document.createElement("form");
    form.innerHTML = `
        <h4>Update Leave Request</h4>

        <label>From Date</label>
        <input type="date" id="editFromDate" required>

        <label>To Date</label>
        <input type="date" id="editToDate" required>

        <label>Leave Type</label>
        <input type="text" id="editLeaveType" required>

        <label>Reason</label>
        <textarea id="editReason" required></textarea>

        <button type="submit">Save Changes</button>
        <button type="button" id="cancelEdit">Cancel</button>
    `;

    container.appendChild(form);

    form.querySelector("#editFromDate").value = leave.From_Date;
    form.querySelector("#editToDate").value = leave.To_Date;
    form.querySelector("#editLeaveType").value = leave.Leave_Type;
    form.querySelector("#editReason").value = leave.Reason;

    form.querySelector("#cancelEdit").onclick = loadMyLeaves;

    form.onsubmit = async function (event) {
        event.preventDefault();

        const fromDate = form.querySelector("#editFromDate").value;
        const toDate = form.querySelector("#editToDate").value;

        if (toDate < fromDate) {
            alert("To Date cannot be earlier than From Date.");
            return;
        }

        try {
            const response = await fetch(
                `${API_URL}/leaves/employee/${leave.Employee_Id}/${leave.Leave_Id}`,
                {
                    method: "PUT",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${localStorage.getItem("access_token")}`
                    },
                    body: JSON.stringify({
                        From_Date: fromDate,
                        To_Date: toDate,
                        Leave_Type: form.querySelector("#editLeaveType").value,
                        Reason: form.querySelector("#editReason").value
                    })
                }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "Unable to update leave request.");
            }

            alert(data.message || "Leave request updated successfully.");
            await loadMyLeaves();

        } catch (error) {
            alert(error.message || "Unable to connect to the server.");
        }
    };
}


async function deleteMyLeave(leave) {
    if (leave.Status !== "Pending") {
        alert("Only pending leave requests can be deleted.");
        return;
    }

    if (!confirm("Are you sure you want to delete this leave request?")) {
        return;
    }

    try {
        const token = localStorage.getItem("access_token");

        const response = await fetch(
            `${API_URL}/leaves/employee/${leave.Employee_Id}/${leave.Leave_Id}`,
            {
                method: "DELETE",
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Unable to delete leave request.");
        }

        alert(data.message || "Leave request deleted successfully.");
        await loadMyLeaves();

    } catch (error) {
        alert(error.message || "Unable to connect to the server.");
    }
}


async function loadManagers() {
    const managerSelect = document.getElementById("registerEmployeeManager");

    managerSelect.innerHTML = '<option value="">Loading managers...</option>';

    try {
        const response = await fetch(`${API_URL}/managers`, {
            headers: {
                "Authorization": `Bearer ${localStorage.getItem("access_token")}`
            }
        });

        const managers = await response.json();

        if (!response.ok) {
            throw new Error(managers.detail || "Unable to load managers");
        }

        managerSelect.innerHTML = '<option value="">Select Manager</option>';

        managers.forEach(manager => {
            const option = document.createElement("option");
            option.value = manager.User_Id;
            option.textContent = manager.Full_Name;
            managerSelect.appendChild(option);
        });

        if (managers.length === 0) {
            managerSelect.innerHTML = '<option value="">No managers available</option>';
        }

    } catch (error) {
        console.error(error);
        managerSelect.innerHTML = '<option value="">Unable to load managers</option>';
    }
}


// Silently refresh expired access token using the stored refresh token
async function refreshAccessToken() {
    const refreshToken = localStorage.getItem("refresh_token");

    if (!refreshToken) {
        endSession("Refresh token expired. Please log in again.");
        return false;
    }

    try {
        const response = await fetch(
            `${API_URL}/auth/refresh?refresh_token=${encodeURIComponent(refreshToken)}`,
            { method: "POST" }
        );

        const data = await response.json();

        if (!response.ok) {
            const message = data.detail || "Session expired. Please log in again.";

            endSession(message);
            return false;
        }

        if (!data.access_token) {
            endSession("Session expired. Please log in again.");
            return false;
        }

        localStorage.setItem("access_token", data.access_token);

        const refreshMsg = `Session active (refreshed at ${new Date().toLocaleTimeString()})`;
        ["adminSessionMessage", "managerSessionMessage", "employeeSessionMessage"].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.textContent = refreshMsg;
        });
        return true;

    } catch (error) {
        console.error("Token refresh failed:", error);
        alert("Unable to connect to the server.");
        return false;
    }
}

function endSession(message) {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");

    alert(message);
    window.location.replace("index.html");
}


document.getElementById("deactivateEmployeeForm")?.addEventListener("submit", function (event) {
    event.preventDefault();

    const employeeId = Number(
        document.getElementById("deactivateEmployeeId").value
    );

    deactivateEmployee(employeeId);
});


document.getElementById("resetPasswordForm").addEventListener("submit", async function (event) {
    event.preventDefault();

    const temporaryPassword = document.getElementById("temporaryPassword").value;
    const newPassword = document.getElementById("newPassword").value;
    const message = document.getElementById("resetPasswordMessage");

    try {
        const response = await fetch(`${API_URL}/auth/reset-password`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${localStorage.getItem("access_token")}`
            },
            body: JSON.stringify({
                Temporary_Password: temporaryPassword,
                New_Password: newPassword
            })
        });

        const data = await response.json();

        if (!response.ok) {
            message.textContent = data.detail || "Password reset failed";
            return;
        }

        message.textContent = "Password reset successfully. Please log in again.";

        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");

        setTimeout(() => {
            window.location.href = "index.html";
        }, 1500);

    } catch (error) {
        message.textContent = "Cannot connect to the server.";
    }
});



/* ================= UI ENHANCEMENT LAYER (visual only) ================= */

// 1) Sidebar tab switching
document.querySelectorAll(".side button").forEach(btn => {
    btn.addEventListener("click", () => {
        const dash = btn.closest(".dashboard");
        dash.querySelectorAll(".side button").forEach(b => b.classList.toggle("on", b === btn));
        dash.querySelectorAll(".panel").forEach(p => p.classList.toggle("on", p.id === btn.dataset.panel));
        window.scrollTo({ top: 0, behavior: "smooth" });
    });
});

// 2) Toast notifications for every status message
const toastBox = document.getElementById("toasts");
function showToast(text, kind) {
    const t = document.createElement("div");
    t.className = "toast " + kind;
    t.textContent = text;
    toastBox.appendChild(t);
    setTimeout(() => t.remove(), 4500);
}
document.querySelectorAll("p.msg").forEach(el => {
    new MutationObserver(() => {
        const text = el.textContent.trim();
        if (!text) return;
        const bad = /fail|unable|cannot|invalid|error|not |expired|enter|earlier/i.test(text);
        showToast(text, bad ? "bad" : "ok");
    }).observe(el, { childList: true, characterData: true, subtree: true });
});

// 3) Turn "Key: value | Key: value" lines into styled data cards
function prettify(container) {
    if (container.dataset.busy) return;
    container.dataset.busy = "1";
    container.querySelectorAll(":scope > p, :scope > .leave-card > p").forEach(p => {
        const first = p.firstChild;
        const raw = first && first.nodeType === 3 ? first.textContent : "";
        if (!raw.includes(":")) return;
        const extra = [...p.querySelectorAll("button")];
        const row = document.createElement("div");
        row.className = "item";
        raw.split(/\s\|\s/).forEach(part => {
            const i = part.indexOf(":");
            if (i < 0) return;
            const label = part.slice(0, i).trim();
            const value = part.slice(i + 1).trim();
            const f = document.createElement("div");
            f.className = "f" + (label === "Status" ? " status" : "");
            const small = document.createElement("small");
            small.textContent = label;
            const span = document.createElement("span");
            span.textContent = value;
            if (label === "Status") span.className = value.split(" ")[0];
            f.append(small, span);
            row.appendChild(f);
        });
        row.append(...extra);
        p.replaceWith(row);
    });
    setTimeout(() => delete container.dataset.busy, 0);
}
document.querySelectorAll(".out").forEach(el => {
    new MutationObserver(() => prettify(el)).observe(el, { childList: true, subtree: true });
});

// 4) 3D tilt on login cards (mouse only, skipped for reduced motion)
if (!matchMedia("(prefers-reduced-motion: reduce)").matches) {
    document.querySelectorAll(".tilt").forEach(card => {
        card.addEventListener("pointermove", e => {
            if (e.pointerType !== "mouse") return;
            const r = card.getBoundingClientRect();
            const x = (e.clientX - r.left) / r.width - 0.5;
            const y = (e.clientY - r.top) / r.height - 0.5;
            card.style.transform = `perspective(900px) rotateY(${x * 10}deg) rotateX(${-y * 10}deg)`;
        });
        card.addEventListener("pointerleave", () => card.style.transform = "");
    });
}
