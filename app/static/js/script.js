"use strict";

const API_URL = "/api/tasks";

const form = document.getElementById("task-form");
const taskList = document.getElementById("task-list");
const message = document.getElementById("task-message");
const submitButton = form.querySelector('button[type="submit"]');

let tasks = [];
let loading = false;
let editingTaskId = null;

function showMessage(text) {
    message.textContent = text;
    message.setAttribute("role", "status");
}

function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, char => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[char]);
}

function setLoading(value) {
    loading = value;
    submitButton.disabled = value;
    submitButton.textContent = value
        ? "Please wait..."
        : editingTaskId !== null
        ? "Update Task"
        : "Create Task";

    taskList.querySelectorAll("button").forEach(button => {
        button.disabled = value;
    });
}

async function apiRequest(url, options = {}) {
    let response;

    try {
        response = await fetch(url, options);
    } catch {
        throw new Error(
            "Cannot connect to the server. Please check your connection."
        );
    }

    if (!response.ok) {
        let detail = "";

        try {
            const data = await response.json();
            detail = data.description || data.error || "";
        } catch {
            // The server may return an HTML error page.
        }

        throw new Error(
            detail || `Server error (${response.status})`
        );
    }

    if (response.status === 204) {
        return null;
    }

    return response.json();
}

function updateDashboard() {
    document.getElementById("total-tasks").textContent =
        tasks.length;

    document.getElementById("in-progress-tasks").textContent =
        tasks.filter(t => t.status === "In Progress").length;

    document.getElementById("completed-tasks").textContent =
        tasks.filter(t => t.status === "Done").length;
}

function renderTasks() {
    taskList.innerHTML = "";

    if (tasks.length === 0) {
        taskList.innerHTML = "<p>No tasks available.</p>";
        updateDashboard();
        return;
    }

    tasks.forEach(task => {
        const card = document.createElement("article");
        card.className = "task-card";

        card.innerHTML = `
            <h3>${escapeHTML(task.title)}</h3>
            <p>${escapeHTML(task.description)}</p>
            <p><strong>Status:</strong>
                ${escapeHTML(task.status)}</p>

            <div class="task-actions">

                <button type="button"
                data-action="edit"
                data-id="${task.id}"
                class="edit-btn">
                Edit Task
                </button>

                <button type="button"
                    data-action="complete"
                    data-id="${task.id}"
                    ${task.status === "Done" ? "disabled" : ""}>
                    Mark Complete
                </button>

                <button type="button"
                    data-action="delete"
                    data-id="${task.id}"
                    class="delete-btn">
                    Delete
                </button>
            </div>
        `;

        taskList.appendChild(card);
    });

    updateDashboard();
}

async function loadTasks() {
    if (loading) return;

    setLoading(true);
    showMessage("Loading tasks...");

    try {
        tasks = await apiRequest(API_URL);
        renderTasks();
        showMessage("");
    } catch (error) {
        tasks = [];
        renderTasks();
        showMessage(`Failed to load tasks: ${error.message}`);
    } finally {
        setLoading(false);
    }
}

form.addEventListener("submit", async event => {
    event.preventDefault();
    if (loading) return;

    const title =
        document.getElementById("task-title").value.trim();

    const description =
        document.getElementById("task-description").value;

    const status =
        document.getElementById("task-status").value;

    if (!title || title.length > 200) {
        showMessage("Title must contain 1–200 characters.");
        return;
    }

    if (description.length > 2000) {
        showMessage("Description cannot exceed 2000 characters.");
        return;
    }

    setLoading(true);
    showMessage("Creating task...");

    try {
        await apiRequest(API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                title,
                description,
                status
            })
        });

        form.reset();
        tasks = await apiRequest(API_URL);
        renderTasks();
        showMessage("Task created successfully.");
    } catch (error) {
        showMessage(`Unable to complete request: ${error.message}`);
    } finally {
        setLoading(false);
    }
});

taskList.addEventListener("click", async event => {
    const button = event.target.closest("button[data-action]");
    if (!button || loading) return;

    const id = Number(button.dataset.id);
    const action = button.dataset.action;

    if (!Number.isInteger(id)) return;

    if (action === "edit") {
    const task = tasks.find(t => t.id === id);

    if (!task) {
        showMessage("Task not found.");
        return;
    }

    editingTaskId = id;

    document.getElementById("task-title").value =
        task.title;

    document.getElementById("task-description").value =
        task.description || "";

    document.getElementById("task-status").value =
        task.status;

    submitButton.textContent = "Update Task";

    form.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

    showMessage("Edit the task details and click Update Task.");
    return;
    }

    if (action === "delete" &&
        !confirm("Are you sure you want to delete this task?")) {
        return;
    }

    setLoading(true);
    showMessage("Processing request...");

    try {
        if (action === "complete") {
            await apiRequest(`${API_URL}/${id}`, {
                method: "PATCH",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ status: "Done" })
            });
        } else if (action === "delete") {
            await apiRequest(`${API_URL}/${id}`, {
                method: "DELETE"
            });
        } else {
            return;
        }

        tasks = await apiRequest(API_URL);
        renderTasks();

        showMessage(
            action === "delete"
                ? "Task deleted successfully."
                : "Task marked as complete."
        );
    } catch (error) {
        showMessage(`Request failed: ${error.message}`);
    } finally {
        setLoading(false);
    }
});

loadTasks();