// static/app.js

// 定义刷新日志函数
async function refreshLog() {
    const logTextArea = document.getElementById("logTextArea");

    try {
        const response = await fetch("/api/get_log");
        const logContent = await response.text();
        logTextArea.value = logContent;

        // 滚动到文本区域底部
        logTextArea.scrollTop = logTextArea.scrollHeight;
    } catch (error) {
        console.error("Error fetching log:", error);
        logTextArea.value = "Error fetching log.";
    }
}

// 初次加载页面时刷新日志并滚动到底部
window.addEventListener("load", () => {
    refreshLog();
});

// 刷新按钮点击时刷新日志
async function onRefreshButtonClick() {
    await refreshLog();
}

// Initial log refresh on page load
refreshLog();