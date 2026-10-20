const { defineConfig, devices } = require("@playwright/test");

const isCI = Boolean(process.env.CI);

module.exports = defineConfig({
    testDir: "./tests/e2e",

    timeout: 30000,

    expect: {
        timeout: 5000
    },

    fullyParallel: false,

    forbidOnly: isCI,

    retries: isCI ? 2 : 0,

    workers: isCI ? 1 : undefined,

    use: {
        baseURL:
            process.env.PLAYWRIGHT_BASE_URL ||
            "http://localhost:8080",

        headless: true,

        trace: "retain-on-failure",

        screenshot: "only-on-failure"
    },

    projects: [
        {
            name: "chromium",
            use: { ...devices["Desktop Chrome"] }
        }
    ],

    reporter: [
        ["list"],
        ["html", { open: "never" }]
    ]
});