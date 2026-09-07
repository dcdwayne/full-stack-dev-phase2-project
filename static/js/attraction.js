// ==========================================
// 1. 解析網址取得 attractionId
// ==========================================
// 假設網址是 /attraction/10，pathname 會是 "/attraction/10"
const pathname = window.location.pathname; 
const urlParts = pathname.split('/'); 
const attractionId = urlParts[urlParts.length - 1]; // 取得最後一段的 ID

// ==========================================
// 2. DOM 元素選取
// ==========================================
// 文字資訊區
const titleEl = document.getElementById('attraction-title');
const categoryEl = document.getElementById('attraction-category');
const mrtEl = document.getElementById('attraction-mrt');
const descEl = document.getElementById('attraction-description');
const addressEl = document.getElementById('attraction-address');
const transportEl = document.getElementById('attraction-transport');

// 輪播圖與圖片區
const trackEl = document.getElementById('carousel-track');
const dotsEl = document.getElementById('carousel-dots');
const prevBtn = document.getElementById('prev-btn');
const nextBtn = document.getElementById('next-btn');

// 全域變數儲存圖片與當前索引
let imagesList = [];
let currentImgIndex = 0;

// ==========================================
// 3. 頁面載入時 Fetch 資料並渲染
// ==========================================
window.addEventListener('DOMContentLoaded', () => {
  fetchAttractionData();
  setupPriceToggle();
});

async function fetchAttractionData() {
  try {
    // 呼叫你的後端 API
    const response = await fetch(`/api/attraction/${attractionId}`);
    const result = await response.json();
    const data = result.data; // 依照你的 API 格式，通常資料包在 data 裡面

    // ---- A. 渲染純文字資訊 ----
    titleEl.textContent = data.name;
    categoryEl.textContent = data.category;
    // 有些景點可能沒有捷運站，可以做個簡單的判斷
    mrtEl.textContent = data.mrt ? data.mrt : '無鄰近捷運站'; 
    descEl.textContent = data.description;
    addressEl.textContent = data.address;
    transportEl.textContent = data.transport;

    // ---- B. 渲染圖片與輪播指示器 ----
    imagesList = data.images; 
    renderCarousel(imagesList);

  } catch (error) {
    console.error('取得景點資料失敗:', error);
  }
}

// ==========================================
// 4. 金額切換邏輯 (上半天 2000 / 下半天 2500)
// ==========================================
function setupPriceToggle() {
  const radioInputs = document.querySelectorAll('input[name="time"]');
  const priceText = document.getElementById('price-text');

  radioInputs.forEach(radio => {
    radio.addEventListener('change', (e) => {
      // 根據選中的值來改變文字
      if (e.target.value === 'morning') {
        priceText.textContent = '新台幣 2000 元';
      } else {
        priceText.textContent = '新台幣 2500 元';
      }
    });
  });
}

// ==========================================
// 5. 渲染輪播圖與橫向指示條
// ==========================================
function renderCarousel(images) {
  trackEl.innerHTML = '';
  dotsEl.innerHTML = '';

  images.forEach((imgUrl, index) => {
    // 建立圖片
    const img = document.createElement('img');
    img.src = imgUrl;
    img.className = 'carousel-img';
    if (index === 0) img.classList.add('active');
    trackEl.appendChild(img);

    // 建立橫向指示線段 (均分寬度)
    const bar = document.createElement('div');
    bar.className = 'indicator-bar';
    if (index === 0) bar.classList.add('active');

    // 點擊線段切換至該圖
    bar.addEventListener('click', () => {
      changeImage(index);
    });
    dotsEl.appendChild(bar);
  });
}

// ==========================================
// 6.切換圖片與指示條狀態 (上一張 / 下一張)
// ==========================================
function changeImage(newIndex) {
  const allImgs = document.querySelectorAll('.carousel-img');
  const allBars = document.querySelectorAll('.indicator-bar');

  // 移除舊的 active
  allImgs[currentImgIndex].classList.remove('active');
  allBars[currentImgIndex].classList.remove('active');

  // 更新 index
  currentImgIndex = newIndex;

  // 加上新的 active
  allImgs[currentImgIndex].classList.add('active');
  allBars[currentImgIndex].classList.add('active');
}

// 綁定左右按鈕點擊事件
prevBtn.addEventListener('click', () => {
  // 如果是第一張，按上一張就跳到最後一張；否則就 -1
  const newIndex = currentImgIndex === 0 ? imagesList.length - 1 : currentImgIndex - 1;
  changeImage(newIndex);
});

nextBtn.addEventListener('click', () => {
  // 如果是最後一張，按下一張就跳回第一張；否則就 +1
  const newIndex = currentImgIndex === imagesList.length - 1 ? 0 : currentImgIndex + 1;
  changeImage(newIndex);
});

// ==========================================
// Part 5-4: 建立新的預定行程 (開始預約行程按鈕)
// ==========================================
document.addEventListener("DOMContentLoaded", () => {
    const bookingForm = document.getElementById("booking-form");
    
    if (bookingForm) {
        bookingForm.addEventListener("submit", async (e) => {
            e.preventDefault(); 
            
            const token = localStorage.getItem("token");
            
            // 1. 若沒有 Token，觸發右上角登入按鈕來開啟彈窗
            if (!token) {
                const authBtn = document.getElementById('nav-auth-btn');
                if (authBtn) authBtn.click();
                return;
            }

            // 2. 準備要送到後端的資料
            const pathParts = window.location.pathname.split('/');
            const attractionId = parseInt(pathParts[pathParts.length - 1]);
            
            const date = document.getElementById("booking-date").value;
            const timeElement = document.querySelector('input[name="time"]:checked');
            const time = timeElement ? timeElement.value : "morning";
            const price = time === "morning" ? 2000 : 2500;

            const bookingData = {
                attractionId: attractionId,
                date: date,
                time: time,
                price: price
            };

            // 3. 呼叫建立預定行程 API
            try {
                const response = await fetch("/api/booking", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${token}`
                    },
                    body: JSON.stringify(bookingData)
                });
                
                // Token 過期或未登入防呆
                if (response.status === 403) {
                    localStorage.removeItem("token");
                    const authBtn = document.getElementById('nav-auth-btn');
                    if (authBtn) authBtn.click();
                    return;
                }

                const result = await response.json();

                // 4. 預定成功，導向購物籃頁面
                if (result.ok) {
                    window.location.href = "/booking";
                } else {
                    alert(result.message || "預約失敗，請稍後再試");
                }

            } catch (error) {
                console.error("預約行程發生錯誤:", error);
                alert("伺服器連線錯誤，請稍後再試");
            }
        });
    }
});