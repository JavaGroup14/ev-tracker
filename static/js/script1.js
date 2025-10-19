let selectedRole = null;

        document.addEventListener('DOMContentLoaded', function() {
            initializeApp();
        });

        function initializeApp() {
            setupRoleSelection();
            setupLoginForm();
            setupGmailLogin();
            setupLogoutButtons();
            setupAuthExtras();
            hideAllDashboards();
            
            const loginPage = document.getElementById('loginPage');
            loginPage.classList.remove('hidden');

            const userInfo = localStorage.getItem('evTrackerUser');
            if (userInfo) {
                const user = JSON.parse(userInfo);
                navigateToDashboard(user.role);
            }
        }

        function setupRoleSelection() {
            const roleButtons = document.querySelectorAll('.role-btn');
            roleButtons.forEach(button => {
                button.addEventListener('click', function() {
                    roleButtons.forEach(btn => btn.classList.remove('active'));
                    this.classList.add('active');
                    selectedRole = this.dataset.role;
                    document.getElementById('loginBtn').disabled = false;
                    document.getElementById('gmailLoginBtn').disabled = false;
                    clearFieldError('roleError');
                });
            });
        }
        
        function setupLoginForm() {
            const loginForm = document.getElementById('loginForm');
            const loginBtn = document.getElementById('loginBtn');
            const usernameInput = document.getElementById('username');
            const passwordInput = document.getElementById('password');

            loginBtn.disabled = true;

            usernameInput.addEventListener('input', () => {
                clearFieldError('usernameError');
                hideError();
            });
            passwordInput.addEventListener('input', () => {
                clearFieldError('passwordError');
                hideError();
            });

            loginForm.addEventListener('submit', function(e) {
                e.preventDefault();
                hideError();
                clearFieldError('roleError');
                clearFieldError('usernameError');
                clearFieldError('passwordError');

                if (!selectedRole) {
                    setFieldError('roleError', 'Please select a role first.');
                    document.querySelectorAll('.role-btn')[0]?.focus();
                    return;
                }

                const username = usernameInput.value.trim();
                const password = passwordInput.value.trim();

                if (!username) {
                    setFieldError('usernameError', 'Please enter your email/username.');
                    usernameInput.focus();
                    return;
                }
                
                if (!isEmailValidForRole(username, selectedRole)) {
                    setFieldError('usernameError', `Email must end with @${selectedRole}.nitw.ac.in`);
                    usernameInput.focus();
                    return;
                }
                
                if (!password) {
                    setFieldError('passwordError', 'Please enter your password.');
                    passwordInput.focus();
                    return;
                }
                
                if (password.length < 6) {
                    setFieldError('passwordError', 'Password must be at least 6 characters.');
                    passwordInput.focus();
                    return;
                }

                performLogin(username, password, selectedRole);
            });
        }
        
        function setupGmailLogin() {
            const gmailLoginBtn = document.getElementById('gmailLoginBtn');
            gmailLoginBtn.disabled = true;

            gmailLoginBtn.addEventListener('click', async function () {
                if (!selectedRole) {
                    setFieldError('roleError', 'Please select a role first.');
                    return;
                }

                hideError();
                gmailLoginBtn.disabled = true;
                document.getElementById('gmailLoginBtnText').textContent = 'Connecting...';

                // This is a simplified simulation of OAuth flow for demonstration
                // A real implementation would require a proper backend and OAuth client setup
                setTimeout(() => {
                    const simulatedPayload = {
                        name: 'Gmail User',
                        email: `user@${selectedRole}.nitw.ac.in`,
                        picture: 'https://placehold.co/100x100'
                    };

                    if (!isEmailValidForRole(simulatedPayload.email, selectedRole)) {
                        showError(`Gmail email must end with @${selectedRole}.nitw.ac.in`);
                        resetGmailButton();
                        return;
                    }
                    
                    const userInfo = { name: simulatedPayload.name, email: simulatedPayload.email, picture: simulatedPayload.picture, role: selectedRole };
                    localStorage.setItem('evTrackerUser', JSON.stringify(userInfo));
                    navigateToDashboard(selectedRole);
                    resetGmailButton();

                }, 1500);
            });
        }

        function setupLogoutButtons() {
            document.querySelectorAll('.logout-btn').forEach(btn => btn.addEventListener('click', logout));
        }

        function setupAuthExtras() {
            document.getElementById('registerLink')?.addEventListener('click', (e) => { e.preventDefault(); showModal('registerModal'); });
            document.getElementById('forgotPasswordLink')?.addEventListener('click', (e) => { e.preventDefault(); showModal('forgotModal'); });
            
            document.querySelectorAll('[data-close]').forEach(btn => {
                btn.addEventListener('click', () => hideModal(btn.dataset.close));
            });
            
            document.querySelectorAll('.modal-overlay').forEach(modal => {
                modal.addEventListener('click', (e) => {
                    if (e.target === modal) modal.classList.add('hidden');
                });
            });

            document.getElementById('registerForm')?.addEventListener('submit', (e) => { e.preventDefault(); handleRegister(); });
            document.getElementById('forgotForm')?.addEventListener('submit', (e) => { e.preventDefault(); handleForgotPassword(); });
        }

        function performLogin(username, password, role) {
            const loginBtn = document.getElementById('loginBtn');
            const loginBtnText = document.getElementById('loginBtnText');

            loginBtn.disabled = true;
            loginBtnText.innerHTML = `<i class="fas fa-spinner fa-spin mr-2"></i>Logging in...`;

            setTimeout(() => {
                const userInfo = { username, role, loginMethod: 'regular' };
                localStorage.setItem('evTrackerUser', JSON.stringify(userInfo));
                navigateToDashboard(role);
                loginBtn.disabled = false;
                loginBtnText.textContent = 'Login';
            }, 1000);
        }
        
        function navigateToDashboard(role) {
            hideLoginPage();
            hideAllDashboards();

            const dashboardId = `${role}Dashboard`;
            const dashboard = document.getElementById(dashboardId);
            if (dashboard) {
                dashboard.classList.remove('hidden');
            } else {
                showError('Invalid role or dashboard not found.');
                showLoginPage();
            }
        }

        function logout() {
            localStorage.removeItem('evTrackerUser');
            document.getElementById('username').value = '';
            document.getElementById('password').value = '';
            selectedRole = null;
            document.querySelectorAll('.role-btn').forEach(btn => btn.classList.remove('active'));
            document.getElementById('loginBtn').disabled = true;
            document.getElementById('gmailLoginBtn').disabled = true;
            hideAllDashboards();
            showLoginPage();
            hideError();
        }

        // Helper functions for UI state
        function showLoginPage() { 
            const page = document.getElementById('loginPage');
            page.classList.remove('hidden');
            setTimeout(() => page.style.opacity = 1, 50);
        }
        function hideLoginPage() { 
            const page = document.getElementById('loginPage');
            page.style.opacity = 0;
            setTimeout(() => page.classList.add('hidden'), 500);
        }
        function showStudentDashboard() { document.getElementById('studentDashboard').classList.remove('hidden'); }
        function showDriverDashboard() { document.getElementById('driverDashboard').classList.remove('hidden'); }
        function showAdminDashboard() { document.getElementById('adminDashboard').classList.remove('hidden'); }
        function hideAllDashboards() {
            document.getElementById('studentDashboard').classList.add('hidden');
            document.getElementById('driverDashboard').classList.add('hidden');
            document.getElementById('adminDashboard').classList.add('hidden');
        }

        // Modal and Error handling
        function showModal(id) {
            const el = document.getElementById(id);
            if(el) {
                el.classList.remove('hidden');
                setTimeout(() => el.classList.remove('opacity-0'), 10);
            }
        }
        function hideModal(id) {
            const el = document.getElementById(id);
            if(el) {
                el.classList.add('opacity-0');
                setTimeout(() => el.classList.add('hidden'), 300);
            }
        }
        function setFieldError(id, message) {
            const el = document.getElementById(id);
            if (el) {
                el.textContent = message;
                el.classList.remove('hidden');
            }
        }
        function clearFieldError(id) {
            const el = document.getElementById(id);
            if (el) {
                el.textContent = '';
                el.classList.add('hidden');
            }
        }
        function showError(msg) {
            const errorEl = document.getElementById('errorMessage');
            document.getElementById('errorText').textContent = msg;
            errorEl.classList.remove('hidden');
        }
        function hideError() {
            document.getElementById('errorMessage').classList.add('hidden');
        }
        function resetGmailButton() {
            const gmailLoginBtn = document.getElementById('gmailLoginBtn');
            gmailLoginBtn.disabled = false;
            document.getElementById('gmailLoginBtnText').textContent = 'Continue with Gmail';
        }
        function isEmailValidForRole(email, role) {
            const domains = {
                student: /@student\.nitw\.ac\.in$/i,
                driver: /@driver\.nitw\.ac\.in$/i,
                admin: /@admin\.nitw\.ac\.in$/i
            };
            return domains[role] ? domains[role].test(email) : false;
        }

        // Dummy registration/forgot password handlers
        function handleRegister() {
            const msgEl = document.getElementById('registerMessage');
            showMessage(msgEl, 'Account created successfully! Redirecting...', true);
            setTimeout(() => {
                hideModal('registerModal');
                navigateToDashboard(document.getElementById('regRole').value);
            }, 1500);
        }
        function handleForgotPassword() {
            const msgEl = document.getElementById('forgotMessage');
            showMessage(msgEl, 'A password reset link has been sent (simulated).', true);
            setTimeout(() => hideModal('forgotModal'), 2000);
        }
        function showMessage(el, text, isSuccess) {
            if (!el) return;
            el.textContent = text;
            el.className = `p-3 text-sm rounded-md ${isSuccess ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`;
            el.classList.remove('hidden');
        }