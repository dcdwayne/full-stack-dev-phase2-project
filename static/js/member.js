document.addEventListener("DOMContentLoaded", () => {
    // 1. 動態設定 MCP Host URL (根據當前網域自動生成)
    const protocol = window.location.protocol;
    const host = window.location.host;
    const mcpHostUrl = `${protocol}//${host}/mcp/`;
    document.getElementById("mcp-host-url").textContent = mcpHostUrl;

    // 2. 檢查登入狀態與獲取會員資料 (包含是否已有 Token)
    checkAuthStatus();

    // 3. 綁定按鈕事件
    document.getElementById("generate-token-btn").addEventListener("click", generateMcpToken);
    document.getElementById("logout-btn").addEventListener("click", handleLogout);
});

// --- 呼叫後端 API 的邏輯 ---

async function checkAuthStatus() {
    try {
        // 從 localStorage 抓取你的登入 Token (請確認你的 key 是不是 'token')
        const token = localStorage.getItem("token"); 

        const response = await fetch("/api/user/auth", {
            method: "GET",
            headers: {
                // 將 Token 放在 Header 中帶給後端
                "Authorization": `Bearer ${token}` 
            }
        });
        
        const data = await response.json();

        // 這裡的 data.data 是依照作業規格的常見格式，
        // 如果你的 API 回傳的 JSON 沒有包著 "data" 這一層 (例如直接是 data.name)，
        // 請把下面的 data.data 改成 data
        if (data.data) { 
            document.getElementById("member-name").textContent = data.data.name;
            
            if (data.data.mcp_token) {
                document.getElementById("mcp-token").textContent = data.data.mcp_token;
            }
        } else {
            // 如果驗證失敗才導回首頁
            window.location.href = "/";
        }
    } catch (error) {
        console.error("驗證狀態錯誤:", error);
    }
}

async function generateMcpToken() {
    try {
        const btn = document.getElementById("generate-token-btn");
        btn.disabled = true;
        btn.textContent = "產生中...";

        // 1. 從 localStorage 抓取你的登入 Token
        const token = localStorage.getItem("token"); 

        const response = await fetch("/api/mcp/token", {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                // 2. 將 Token 放在 Header 中帶給後端 (這是解決 403 的關鍵)
                "Authorization": `Bearer ${token}` 
            }
        });
        
        const data = await response.json();

        if (response.ok && data.token) {
            // 成功取得新 Token，更新畫面
            document.getElementById("mcp-token").textContent = data.token;
            alert("金鑰已成功產生/更新！");
        } else {
            alert(data.message || "產生金鑰失敗，請稍後再試。");
        }
    } catch (error) {
        console.error("產生金鑰錯誤:", error);
        alert("伺服器連線錯誤");
    } finally {
        const btn = document.getElementById("generate-token-btn");
        btn.disabled = false;
        btn.textContent = "產生 / 更新金鑰";
    }
}

// 注意：這個函式不需要使用 async/await，因為它只處理前端的 localStorage
function handleLogout() {
    // 1. 清除儲存在前端的 Token
    localStorage.removeItem("token");
    
    // 2. 導回首頁
    window.location.href = "/";
}