"use strict";

// Temporary frontend storage.
// Tasks will be lost when the page is refreshed.
// Replace this with Flask API calls during backend integration.
let tasks = [];
let nextTaskId = 1;
let editingTaskId = null;

const form = document.getElementById("task-form");
const taskList = document.getElementById("task-list");
const message = document.getElementById("task-message");
const submitButton = form.querySelector('button[type="submit"]');

// Prevent task content from being interpreted as HTML.
function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, char => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[char]);
}

function showMessage(text) {
    message.textContent = text;
}

// Update dashboard statistics.
function updateDashboard() {
    document.getElementById("total-tasks").textContent =
        tasks.length;

    document.getElementById("in-progress-tasks").textContent =
        tasks.filter(task => task.status === "In Progress").length;

    document.getElementById("completed-tasks").textContent =
        tasks.filter(task => task.status === "Done").length;
}

// Display all tasks.
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
                <span class="status-badge">
                    ${escapeHTML(task.status)}
                </span>
            </p>
            <p><strong>Priority</strong>:
                ${escapeHTML(task.priority)}</p>
            <p><strong>Due Date</strong>:
                ${escapeHTML(task.dueDate || "Not set")}</p>

            <div class="task-actions">
                <button type="button" data-action="edit"
                    data-id="${task.id}">Edit</button>

                <button type="button" data-action="complete"
                    data-id="${task.id}"
                    ${task.status === "Done" ? "disabled" : ""}>
                    Mark Complete
                </button>

                <button type="button" class="delete-btn"
                    data-action="delete"
                    data-id="${task.id}">Delete</button>
            </div>
        `;

        taskList.appendChild(card);
    });

    updateDashboard();
}

// Create or update a task.
form.addEventListener("submit", event => {
    event.preventDefault();

    const title =
        document.getElementById("task-title").value.trim();

    const description =
        document.getElementById("task-description").value.trim();

    const status =
        document.getElementById("task-status").value;

    const priority =
        document.getElementById("task-priority").value;

    const dueDate =
        document.getElementById("task-due-date").value;

    if (!title) {
        showMessage("Please enter a task title.");
        return;
    }

    const taskData = {
        title,
        description,
        status,
        priority,
        dueDate
    };

    if (editingTaskId !== null) {
        const task = tasks.find(t => t.id === editingTaskId);

        if (task) {
            Object.assign(task, taskData);
            showMessage("Task updated successfully.");
        }

        editingTaskId = null;
        submitButton.textContent = "Create Task";
    } else {
        tasks.push({
            id: nextTaskId++,
            ...taskData
        });

        showMessage("Task created successfully.");
    }

    form.reset();
    renderTasks();
});

// Handle task action buttons.
taskList.addEventListener("click", event => {
    const button = event.target.closest("button[data-action]");
    if (!button) return;

    const id = Number(button.dataset.id);
    const task = tasks.find(t => t.id === id);

    if (!task) return;

    const action = button.dataset.action;

    if (action === "edit") {
        document.getElementById("task-title").value = task.title;
        document.getElementById("task-description").value =
            task.description;
        document.getElementById("task-status").value = task.status;
        document.getElementById("task-priority").value =
            task.priority;
        document.getElementById("task-due-date").value =
            task.dueDate;

        editingTaskId = id;
        submitButton.textContent = "Save Changes";
        form.scrollIntoView({ behavior: "smooth" });

        showMessage("Editing selected task.");
    }

    if (action === "complete") {
        task.status = "Done";
        renderTasks();
        showMessage("Task marked as complete.");
    }

    if (action === "delete") {
        if (!confirm("Are you sure you want to delete this task?")) {
            return;
        }

        tasks = tasks.filter(t => t.id !== id);

        if (editingTaskId === id) {
            editingTaskId = null;
            form.reset();
            submitButton.textContent = "Create Task";
        }

        renderTasks();
        showMessage("Task deleted successfully.");
    }
});

// Initialise the dashboard.
renderTasks();