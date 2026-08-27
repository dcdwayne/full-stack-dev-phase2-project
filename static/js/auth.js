// 1. 定義彈出視窗的 HTML 結構 (使用反引號 ` 包起來，可以換行)
const authModalHTML = `
<div id="auth-modal" class="modal-overlay" style="display: none;">
    <!-- 登入視窗 -->
    <div id="signin-dialog" class="dialog-box">
        <div class="dialog-header-bar"></div>
        <div class="dialog-content">
            <div class="dialog-title">
                <h3>登入會員帳號</h3>
                <button class="close-btn" id="close-signin">&times;</button>
            </div>
            <form id="signin-form">
                <input type="email" id="signin-email" placeholder="輸入電子信箱" required>
                <input type="password" id="signin-password" placeholder="輸入密碼" required>
                <button type="submit" class="submit-btn">登入帳戶</button>
            </form>
            <div id="signin-message" class="message-box"></div>
            <p class="switch-link">還沒有帳戶？<span id="to-signup">點此註冊</span></p>
        </div>
    </div>

    <!-- 註冊視窗 -->
    <div id="signup-dialog" class="dialog-box" style="display: none;">
        <div class="dialog-header-bar"></div>
        <div class="dialog-content">
            <div class="dialog-title">
                <h3>註冊會員帳號</h3>
                <button class="close-btn" id="close-signup">&times;</button>
            </div>
            <form id="signup-form">
                <input type="text" id="signup-name" placeholder="輸入姓名" required>
                <input type="email" id="signup-email" placeholder="輸入電子郵件" required>
                <input type="password" id="signup-password" placeholder="輸入密碼" required>
                <button type="submit" class="submit-btn">註冊新帳戶</button>
            </form>
            <div id="signup-message" class="message-box"></div>
            <p class="switch-link">已經有帳戶了？<span id="to-signin">點此登入</span></p>
        </div>
    </div>
</div>
`;

// 2. 當網頁 DOM 載入完成後，執行以下邏輯
document.addEventListener("DOMContentLoaded", () => {
    
    // 將 HTML 塞進 <body> 的最尾端
    document.body.insertAdjacentHTML('beforeend', authModalHTML);

    // ==========================================
    // 以下是你剛剛寫的 JS 邏輯，完全照搬過來即可！
    // ==========================================
    const authModal = document.getElementById('auth-modal');
    const signinDialog = document.getElementById('signin-dialog');
    const signupDialog = document.getElementById('signup-dialog');
    const navAuthBtn = document.getElementById('nav-auth-btn'); // 確保導覽列有這個 id

    const closeSigninBtn = document.getElementById('close-signin');
    const closeSignupBtn = document.getElementById('close-signup');
    const toSignupBtn = document.getElementById('to-signup');
    const toSigninBtn = document.getElementById('to-signin');

    const signinForm = document.getElementById('signin-form');
    const signupForm = document.getElementById('signup-form');
    const signinMessage = document.getElementById('signin-message');
    const signupMessage = document.getElementById('signup-message');

    function showMessage(element, text, isSuccess) {
        element.textContent = text;
        element.style.color = isSuccess ? '#4E9A06' : '#cc0000'; 
    }

    function resetForms() {
        signinForm.reset();
        signupForm.reset();
        signinMessage.textContent = '';
        signupMessage.textContent = '';
    }

    function openModal() {
        authModal.style.display = 'flex';
        signinDialog.style.display = 'block';
        signupDialog.style.display = 'none';
        resetForms();
    }

    function closeModal() {
        authModal.style.display = 'none';
    }

    toSignupBtn.addEventListener('click', () => {
        signinDialog.style.display = 'none';
        signupDialog.style.display = 'block';
        resetForms();
    });

    toSigninBtn.addEventListener('click', () => {
        signupDialog.style.display = 'none';
        signinDialog.style.display = 'block';
        resetForms();
    });

    closeSigninBtn.addEventListener('click', closeModal);
    closeSignupBtn.addEventListener('click', closeModal);

    authModal.addEventListener('click', (e) => {
        if (e.target === authModal) closeModal();
    });

    signupForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('signup-name').value;
        const email = document.getElementById('signup-email').value;
        const password = document.getElementById('signup-password').value;

        try {
            const response = await fetch('/api/user', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, password })
            });
            const result = await response.json();
            if (response.ok) {
                showMessage(signupMessage, "註冊成功，請登入系統", true);
            } else {
                showMessage(signupMessage, result.detail || "註冊失敗", false);
            }
        } catch (error) {
            showMessage(signupMessage, "伺服器連線錯誤", false);
        }
    });

    signinForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('signin-email').value;
        const password = document.getElementById('signin-password').value;

        try {
            const response = await fetch('/api/user/auth', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            const result = await response.json();
            if (response.ok && result.token) {
                localStorage.setItem('token', result.token);
                window.location.reload();
            } else {
                showMessage(signinMessage, result.detail || "電子郵件或密碼錯誤", false);
            }
        } catch (error) {
            showMessage(signinMessage, "伺服器連線錯誤", false);
        }
    });

    async function checkAuthStatus() {
        const token = localStorage.getItem('token');
        try {
            const response = await fetch('/api/user/auth', {
                method: 'GET',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const result = await response.json();

            if (result.data !== null) {
                navAuthBtn.textContent = '登出系統';
                navAuthBtn.addEventListener('click', () => {
                    localStorage.removeItem('token');
                    window.location.reload();
                });
            } else {
                navAuthBtn.textContent = '登入/註冊';
                navAuthBtn.addEventListener('click', openModal);
            }
        } catch (error) {
            navAuthBtn.textContent = '登入/註冊';
            navAuthBtn.addEventListener('click', openModal);
        }
    }

    // 執行狀態檢查
    checkAuthStatus();
});