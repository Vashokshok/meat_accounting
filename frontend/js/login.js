"use strict";

const LOGIN_URL = "/api/v1/auth/login";
const ME_URL = "/api/v1/auth/me";
const TOKEN_KEY = "meat_accounting_access_token";

const form = document.getElementById("login-form");
const usernameInput = document.getElementById("username");
const passwordInput = document.getElementById("password");

const errorElement = document.getElementById("login-error");
const button = document.getElementById("login-button");
const buttonText = document.getElementById("login-button-text");
const spinner = document.getElementById("login-spinner");


function showError(message) {
    errorElement.textContent = message;
    errorElement.style.display = "block";
}


function hideError() {
    errorElement.textContent = "";
    errorElement.style.display = "none";
}


function setLoading(loading) {
    button.disabled = loading;

    if (loading) {
        buttonText.textContent = "Вход...";
        spinner.style.display = "inline-block";
    } else {
        buttonText.textContent = "Войти";
        spinner.style.display = "none";
    }
}


form.addEventListener("submit", async function (event) {

    // Самое главное:
    // браузер НЕ должен отправлять форму через GET
    event.preventDefault();

    hideError();

    const username = usernameInput.value.trim();
    const password = passwordInput.value;

    if (!username || !password) {
        showError("Введите логин и пароль");
        return;
    }

    setLoading(true);

    try {

        console.log("Отправляем запрос на:", LOGIN_URL);
        console.log("Логин:", username);

        const response = await fetch(LOGIN_URL, {
            method: "POST",

            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json"
            },

            body: JSON.stringify({
                username: username,
                password: password
            })
        });


        let data;

        try {
            data = await response.json();
        } catch {
            throw new Error(
                `Сервер вернул некорректный ответ (${response.status})`
            );
        }


        console.log("Ответ сервера:", response.status, data);


        if (!response.ok) {
            throw new Error(
                data.detail || `Ошибка входа (${response.status})`
            );
        }


        if (!data.access_token) {
            throw new Error(
                "Сервер не вернул access_token"
            );
        }


        // Сохраняем JWT
        localStorage.setItem(
            TOKEN_KEY,
            data.access_token
        );


        // Проверяем токен
        const meResponse = await fetch(ME_URL, {
            method: "GET",

            headers: {
                "Authorization":
                    `Bearer ${data.access_token}`,

                "Accept": "application/json"
            }
        });


        if (!meResponse.ok) {

            localStorage.removeItem(TOKEN_KEY);

            throw new Error(
                "Токен получен, но авторизация не прошла"
            );
        }


        console.log("Авторизация успешна");


        // Переходим на dashboard
        window.location.replace("/dashboard");

    } catch (error) {

        console.error("Ошибка входа:", error);

        showError(
            error.message || "Не удалось войти"
        );

        setLoading(false);
    }
});