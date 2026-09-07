document.addEventListener("DOMContentLoaded", () => {
    initBookingPage();
});

async function initBookingPage() {
    const token = localStorage.getItem("token");
    
    // 1. 驗證登入狀態 (如果未登入則導回首頁)
    if (!token) {
        window.location.href = "/";
        return;
    }

    try {
        const authRes = await fetch("/api/user/auth", {
            headers: { "Authorization": `Bearer ${token}` }
        });
        const authData = await authRes.json();
        
        if (!authData.data) {
            window.location.href = "/";
            return;
        }

        // 顯示問候語與預填表單
        const userData = authData.data;
        document.getElementById("greeting-title").textContent = `您好，${userData.name}，待預訂的行程如下：`;
        document.getElementById("contact-name").value = userData.name;
        document.getElementById("contact-email").value = userData.email;

        // 2. 獲取預定資料
        fetchBookingData(token);

    } catch (error) {
        console.error("Auth check failed:", error);
        window.location.href = "/";
    }
}

async function fetchBookingData(token) {
    try {
        const response = await fetch("/api/booking", {
            headers: { "Authorization": `Bearer ${token}` }
        });
        const result = await response.json();

        const emptyState = document.getElementById("empty-state");
        const bookingContent = document.getElementById("booking-content");

        // 如果沒有預定資料，渲染「沒有預定行程」畫面
        if (!result.data) {
            emptyState.style.display = "block";
            bookingContent.style.display = "none";
            
            // 將 Footer 拉上來以符合 Figma 畫面
            document.querySelector(".booking-main").style.flex = "0"; 
            document.querySelector(".footer").style.minHeight = "100vh";
            document.querySelector(".footer").style.paddingTop = "40px";
            return;
        }

        // 如果有資料，開始渲染 DOM
        emptyState.style.display = "none";
        bookingContent.style.display = "block";

        const booking = result.data;
        document.getElementById("tour-img").src = booking.attraction.image;
        document.getElementById("tour-name").textContent = `台北一日遊：${booking.attraction.name}`;
        document.getElementById("tour-date").textContent = booking.date;
        
        // 轉換時間顯示 (morning/afternoon)
        const timeText = booking.time === "morning" ? "早上 9 點到下午 2 點" : "下午 2 點到晚上 9 點";
        document.getElementById("tour-time").textContent = timeText;
        
        document.getElementById("tour-price").textContent = booking.price;
        document.getElementById("confirm-price").textContent = booking.price;
        document.getElementById("tour-address").textContent = booking.attraction.address;

        // 3. 綁定刪除按鈕事件
        document.getElementById("delete-btn").addEventListener("click", () => {
            deleteBooking(token);
        });

    } catch (error) {
        console.error("Fetch booking failed:", error);
    }
}

async function deleteBooking(token) {
    try {
        const response = await fetch("/api/booking", {
            method: "DELETE",
            headers: { "Authorization": `Bearer ${token}` }
        });
        const result = await response.json();

        if (result.ok) {
            // 刪除成功後重新整理頁面
            window.location.reload();
        }
    } catch (error) {
        console.error("Delete booking failed:", error);
    }
}