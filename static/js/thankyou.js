document.addEventListener("DOMContentLoaded", () => {
    initThankyouPage();
});

async function initThankyouPage() {
    const token = localStorage.getItem("token");
    
    // 1. 驗證是否有 Token (未登入則導回首頁)
    if (!token) {
        window.location.href = "/";
        return;
    }

    try {
        // 2. 向後端驗證 Token 的有效性
        const authRes = await fetch("/api/user/auth", {
            headers: { "Authorization": `Bearer ${token}` }
        });
        const authData = await authRes.json();
        
        // 如果 Token 無效或已過期，導回首頁
        if (!authData.data) {
            window.location.href = "/";
            return;
        }

        // 3. 驗證通過，執行原本渲染訂單編號的邏輯
        renderOrderNumber();

    } catch (error) {
        console.error("Auth check failed:", error);
        window.location.href = "/";
    }
}

function renderOrderNumber() {
    // 透過 URLSearchParams 解析網址列中的 query parameter
    // 針對網址如：/thankyou?number=20260907101912262799-54
    const urlParams = new URLSearchParams(window.location.search);
    const orderNumber = urlParams.get('number');
    
    // 取得 HTML 中的渲染容器
    const orderNumberElement = document.getElementById('order-number');

    // 判斷是否成功取得編號並顯示
    if (orderNumber) {
        orderNumberElement.textContent = orderNumber;
    } else {
        orderNumberElement.textContent = "無法取得訂單編號，請重新確認";
        orderNumberElement.style.color = "red";
    }
}