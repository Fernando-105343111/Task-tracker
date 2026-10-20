"use strict";

const API_URL = "/api/tasks";

const form = document.getElementById("task-form");
const taskList = document.getElementById("task-list");
const message = document.getElementById("task-message");
const submitButton = form.querySelector('button[type="submit"]');
const cancelButton = document.getElementById("cancel-edit");
const formHeading = document.getElementById("form-heading");

const titleInput = document.getElementById("task-title");
const descriptionInput = document.getElementById("task-description");
const statusInput = document.getElementById("task-status");
const priorityInput = document.getElementById("task-priority");
const dueDateInput = document.getElementById("task-due-date");

let tasks = [];
let loading = false;
let editingTaskId = null;

function showMessage(text, isError = false) {
    message.textContent = text;
    message.style.color = isError ? "#dc2626" : "#475569";
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

function updateFormMode() {
    const editing = editingTaskId !== null;

    formHeading.textContent = editing
        ? "Edit Task"
        : "Create New Task";

    submitButton.textContent = loading
        ? "Please wait..."
        : editing ? "Update Task" : "Create Task";

    cancelButton.hidden = !editing;
}

function setLoading(value) {
    loading = value;

    submitButton.disabled = value;
    cancelButton.disabled = value;

    taskList.querySelectorAll("button").forEach(button => {
        button.disabled = value ||
            (button.dataset.action === "complete" &&
             button.dataset.completed === "true");
    });

    updateFormMode();
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
            detail = data.description ||
                data.error ||
                data.message ||
                "";
        } catch {
            // The server may return a non-JSON error.
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

            <p>
                <strong>Status:</strong>
                <span class="status-badge">
                    ${escapeHTML(task.status)}
                </span>
            </p>

            <p>
                <strong>Priority:</strong>
                ${escapeHTML(task.priority || "Medium")}
            </p>

            <p>
                <strong>Due Date:</strong>
                ${escapeHTML(task.dueDate || "Not set")}
            </p>

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
                    data-completed="${task.status === "Done"}"
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

async function refreshTasks() {
    const latestTasks = await apiRequest(API_URL);

    if (!Array.isArray(latestTasks)) {
        throw new Error("Unexpected task data received.");
    }

    tasks = latestTasks;
    renderTasks();
}

async function loadTasks() {
    if (loading) return;

    setLoading(true);
    showMessage("Loading tasks...");

    try {
        await refreshTasks();
        showMessage("");
    } catch (error) {
        showMessage(
            `Failed to load tasks: ${error.message}`,
            true
        );
    } finally {
        setLoading(false);
    }
}

function resetForm() {
    editingTaskId = null;
    form.reset();
    updateFormMode();
}

function startEditing(task) {
    editingTaskId = task.id;

    titleInput.value = task.title;
    descriptionInput.value = task.description || "";
    statusInput.value = task.status;
    priorityInput.value = task.priority || "Medium";
    dueDateInput.value = task.dueDate || "";

    updateFormMode();

    form.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

    titleInput.focus();
    showMessage("Editing selected task.");
}

cancelButton.addEventListener("click", () => {
    if (loading) return;

    resetForm();
    showMessage("Editing cancelled.");
});

form.addEventListener("submit", async event => {
    event.preventDefault();

    if (loading) return;

    const title = titleInput.value.trim();
    const description = descriptionInput.value;
    const status = statusInput.value;
    const priority = priorityInput.value;
    const dueDate = dueDateInput.value || null;

    if (!title || title.length > 200) {
        showMessage(
            "Title must contain 1–200 characters.",
            true
        );
        return;
    }

    if (description.length > 2000) {
        showMessage(
            "Description cannot exceed 2000 characters.",
            true
        );
        return;
    }

    const taskData = {
        title,
        description,
        status,
        priority,
        dueDate
    };

    const isEditing = editingTaskId !== null;
    const url = isEditing
        ? `${API_URL}/${editingTaskId}`
        : API_URL;

    setLoading(true);

    showMessage(
        isEditing ? "Updating task..." : "Creating task..."
    );

    try {
        await apiRequest(url, {
            method: isEditing ? "PUT" : "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(taskData)
        });

        // Save succeeded. Exit editing mode.
        resetForm();

        try {
            await refreshTasks();
            showMessage(
                isEditing
                    ? "Task updated successfully."
                    : "Task created successfully."
            );
        } catch (refreshError) {
            showMessage(
                "Task saved, but the list could not be refreshed: " +
                refreshError.message,
                true
            );
        }
    } catch (error) {
        showMessage(
            `Unable to save task: ${error.message}`,
            true
        );
    } finally {
        setLoading(false);
    }
});

taskList.addEventListener("click", async event => {
    const button = event.target.closest("button[data-action]");

    if (!button || loading) return;

    const id = Number(button.dataset.id);
    const action = button.dataset.action;

    if (!Number.isInteger(id) || id <= 0) return;

    if (action === "edit") {
        const task = tasks.find(t => t.id === id);

        if (!task) {
            showMessage("Task not found.", true);
            return;
        }

        startEditing(task);
        return;
    }

    if (action === "delete") {
        const confirmed = confirm(
            "Are you sure you want to delete this task?"
        );

        if (!confirmed) return;
    }

    if (action !== "complete" && action !== "delete") {
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
                body: JSON.stringify({
                    status: "Done"
                })
            });
        }

        if (action === "delete") {
            await apiRequest(`${API_URL}/${id}`, {
                method: "DELETE"
            });
        }

        // If the deleted task was being edited,
        // return the form to creation mode.
        if (action === "delete" && editingTaskId === id) {
            resetForm();
        }

        try {
            await refreshTasks();
            showMessage(
                action === "delete"
                    ? "Task deleted successfully."
                    : "Task marked as complete."
            );
        } catch (refreshError) {
            showMessage(
                "Task action succeeded, but refresh failed: " +
                refreshError.message,
                true
            );
        }
    } catch (error) {
        showMessage(
            `Request failed: ${error.message}`,
            true
        );
    } finally {
        setLoading(false);
    }
});

updateFormMode();
loadTasks();