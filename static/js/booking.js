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

        // 加上這行，啟動 TapPay 渲染輸入框！
        initTapPay(booking);

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

// 在 fetchBookingData 成功取得資料，且顯示 booking-content 之後呼叫
function initTapPay(booking) {
    TPDirect.setupSDK(171095, 'app_8h0XFksDdz06gu6k2DxMjHJPtJaVSs5HfFQL3NPCkJqNuAoZQcoXSfxNOygB', 'sandbox');

    let fields = {
        number: { element: '#card-number', placeholder: '**** **** **** ****' },
        expirationDate: { element: '#card-expiration-date', placeholder: 'MM / YY' },
        ccv: { element: '#card-ccv', placeholder: 'CVV' }
    };

    TPDirect.card.setup({
        fields: fields,
        styles: {
            'input': {
                'color': '#666666', // 配合你全域的文字顏色
                'font-size': '16px', // 配合你 input 的字體大小
                'font-family': "'Noto Sans TC', sans-serif" // 配合你全域的字型
            },
            ':focus': {
                'color': 'black'
            },
            '.valid': {
                'color': 'green'
            },
            '.invalid': {
                'color': 'red'
            }
        }
    });

    const submitButton = document.querySelector('#submit-button');
    TPDirect.card.onUpdate(function (update) {
        if (update.canGetPrime) {
            submitButton.removeAttribute('disabled');
        } else {
            submitButton.setAttribute('disabled', true);
        }
    });

    submitButton.addEventListener('click', function(event) {
        event.preventDefault();
        const tappayStatus = TPDirect.card.getTappayFieldsStatus();
        if (tappayStatus.canGetPrime === false) {
            alert('信用卡資訊填寫有誤，請重新檢查');
            return;
        }

        TPDirect.card.getPrime(async function (result) {
            if (result.status !== 0) {
                alert('取得 Prime 失敗: ' + result.msg);
                return;
            }
            
            const prime = result.card.prime;
            
            // 收集畫面上使用者輸入的聯絡資訊與行程資料
            const contactName = document.getElementById("contact-name").value;
            const contactEmail = document.getElementById("contact-email").value;
            const contactPhone = document.getElementById("contact-phone").value;
            const price = parseInt(document.getElementById("confirm-price").textContent);
            
            const requestBody = {
                prime: prime,
                order: {
                    price: price,
                    trip: {
                        attraction: {
                            id: booking.attraction.id,
                            name: booking.attraction.name,
                            address: booking.attraction.address,
                            image: booking.attraction.image
                        },
                        date: booking.date,
                        time: booking.time
                    }
                },
                contact: {
                    name: contactName,
                    email: contactEmail,
                    phone: contactPhone
                }
            };

            try {
                const token = localStorage.getItem("token");
                const response = await fetch("/api/orders", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${token}`
                    },
                    body: JSON.stringify(requestBody)
                });
                
                const resultData = await response.json();
                
                if (resultData.data && resultData.data.payment.status === 0) {
                    // 付款成功，跳轉至 thankyou 頁面並帶上訂單編號
                    window.location.href = `/thankyou?number=${resultData.data.number}`;
                } else {
                    alert(resultData.data ? resultData.data.payment.message : resultData.message);
                }
            } catch (error) {
                console.error("結帳失敗:", error);
                alert("伺服器錯誤，請稍後再試");
            }
        });
    });
}