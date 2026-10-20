const { test, expect } = require("@playwright/test");

test("Task Tracker application loads successfully", async ({ page }) => {
    await page.goto("/");

    await expect(
        page.getByRole("heading", { name: "Task Tracker" })
    ).toBeVisible();

    await expect(
        page.locator("#task-form")
    ).toBeVisible();

    await expect(
        page.locator("#task-list")
    ).toBeVisible();
});

test("Complete task management workflow", async ({ page, request }) => {
    const uniqueId = Date.now();
    const title = `E2E Task ${uniqueId}`;
    const updatedTitle = `Updated E2E Task ${uniqueId}`;

    let taskId = null;
    let taskCreated = false;

    // Automatically accept the delete confirmation.
    page.on("dialog", dialog => dialog.accept());

    try {
        // 1. Open the application.
        await page.goto("/");

        // 2. Create a task.
        await page.locator("#task-title").fill(title);
        await page.locator("#task-description")
            .fill("Created by Playwright");

        await page.locator("#task-status")
            .selectOption("To Do");

        await page.locator("#task-priority")
            .selectOption("High");

        await page.locator("#task-due-date")
            .fill("2026-12-20");

        await page.getByRole("button", {
            name: "Create Task"
        }).click();

        // 3. Verify the task appears.
        const taskCard = page.locator(".task-card")
            .filter({ hasText: title });

        await expect(taskCard).toBeVisible();
        await expect(taskCard).toContainText("High");
        await expect(taskCard).toContainText("2026-12-20");

        // Identify the created task for safe cleanup.
        taskId = await taskCard
            .locator('[data-action="delete"]')
            .getAttribute("data-id");

            taskCreated = true;
            
        // 4. Edit the task.
        await taskCard.getByRole("button", {
            name: "Edit Task"
        }).click();

        await page.locator("#task-title")
            .fill(updatedTitle);

        await page.locator("#task-description")
            .fill("Updated by Playwright");

        await page.getByRole("button", {
            name: "Update Task"
        }).click();

        // Verify the edited information.
        const updatedCard = page.locator(".task-card")
            .filter({ hasText: updatedTitle });

        await expect(updatedCard).toBeVisible();
        await expect(updatedCard)
            .toContainText("Updated by Playwright");

        // 5. Mark the task complete.
        await updatedCard.getByRole("button", {
            name: "Mark Complete"
        }).click();

        await expect(updatedCard).toContainText("Done");

        // 6. Delete the task.
        await updatedCard.getByRole("button", {
            name: "Delete"
        }).click();

        // 7. Verify the task is removed.
        await expect(updatedCard).toHaveCount(0);

        // Successfully deleted.
        taskId = null;

    } finally {
    if (taskCreated && taskId === null) {
        try {
            const response = await request.get("/api/tasks");

            if (response.ok()) {
                const allTasks = await response.json();

                const createdTask = allTasks.find(
                    task => task.title === title ||
                            task.title === updatedTitle
                );

                if (createdTask) {
                    taskId = createdTask.id;
                }
            }
        } catch (error) {
            console.error("Could not find test task:", error);
        }
    }

    if (taskId !== null) {
        const response = await request.delete(
            `/api/tasks/${taskId}`
        );

        if (!response.ok() && response.status() !== 404) {
            console.error(
                `Cleanup failed: HTTP ${response.status()}`
            );
        }
    }
}
});