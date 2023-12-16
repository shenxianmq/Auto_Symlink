// static/app.js

async function refreshLog() {
    const logTextArea = document.getElementById("logTextArea");

    try {
        const response = await fetch("/api/get_log");
        const logContent = await response.text();
        logTextArea.value = logContent;
    } catch (error) {
        console.error("Error fetching log:", error);
        logTextArea.value = "Error fetching log.";
    }
}

// Initial log refresh on page load
refreshLog();
