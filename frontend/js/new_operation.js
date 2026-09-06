"use strict";

const TOKEN_KEY = "meat_accounting_access_token";

const API = {
    operations: "/api/v1/operations",
    franchises: "/api/v1/franchises?active_only=true",
};

const token = localStorage.getItem(TOKEN_KEY);

if (!token) {
    window.location.replace("/");
}

const form = document.getElementById("operation-form");

const backButton = document.getElementById("back-button");

const quantityInput = document.getElementById("quantity");
const operationDateInput = document.getElementById("operation-date");

const franchiseField = document.getElementById("franchise-field");
const franchiseSelect = document.getElementById("franchise-id");

const errorElement = document.getElementById("operation-error");

const saveButton = document.getElementById("save-operation");
const saveButtonText = document.getElementById("save-button-text");

let selectedOperationType = "INCOMING";
let selectedMeatType = "FILLET";


/* -------------------------------------------------------
   API
------------------------------------------------------- */

async function apiFetch(url, options = {}) {
    const currentToken = localStorage.getItem(TOKEN_KEY);

    if (!currentToken) {
        window.location.replace("/");
        throw new Error("Нет авторизации");
    }

    const headers = new Headers(options.headers || {});

    headers.set(
        "Authorization",
        `Bearer ${currentToken}`
    );

    headers.set(
        "Accept",
        "application/json"
    );

    if (options.body && !headers.has("Content-Type")) {
        headers.set(
            "Content-Type",
            "application/json"
        );
    }

    const response = await fetch(url, {
        ...options,
        headers,
    });

    if (response.status === 401) {
        localStorage.removeItem(TOKEN_KEY);
        window.location.replace("/");
        throw new Error("Сессия истекла");
    }

    return response;
}


/* -------------------------------------------------------
   Date
------------------------------------------------------- */

function getMoscowTodayISO() {
    const parts = new Intl.DateTimeFormat("en-CA", {
        timeZone: "Europe/Moscow",
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
    }).formatToParts(new Date());

    const values = {};

    for (const part of parts) {
        if (part.type !== "literal") {
            values[part.type] = part.value;
        }
    }

    return `${values.year}-${values.month}-${values.day}`;
}


/* -------------------------------------------------------
   Errors
------------------------------------------------------- */

function showError(message) {
    errorElement.textContent = message;
}

function clearError() {
    errorElement.textContent = "";
}


/* -------------------------------------------------------
   Operation type
------------------------------------------------------- */

function updateOperationTypeButtons() {
    const buttons = document.querySelectorAll(
        "[data-operation-type]"
    );

    buttons.forEach((button) => {
        const isSelected =
            button.dataset.operationType ===
            selectedOperationType;

        button.classList.toggle(
            "selected",
            isSelected
        );
    });
}

async function selectOperationType(type) {
    selectedOperationType = type;

    updateOperationTypeButtons();

    if (type === "FRANCHISE") {
        franchiseField.classList.remove("hidden");

        await loadFranchises();
    } else {
        franchiseField.classList.add("hidden");

        franchiseSelect.value = "";
    }
}


/* -------------------------------------------------------
   Meat type
------------------------------------------------------- */

function updateMeatButtons() {
    const buttons = document.querySelectorAll(
        "[data-meat-type]"
    );

    buttons.forEach((button) => {
        const isSelected =
            button.dataset.meatType ===
            selectedMeatType;

        button.classList.toggle(
            "selected",
            isSelected
        );
    });
}


/* -------------------------------------------------------
   Franchises
------------------------------------------------------- */

async function loadFranchises() {
    franchiseSelect.innerHTML = `
        <option value="">
            Загрузка...
        </option>
    `;

    try {
        const response = await apiFetch(
            API.franchises
        );

        if (!response.ok) {
            throw new Error(
                "Не удалось загрузить список франшиз"
            );
        }

        const franchises = await response.json();

        franchiseSelect.innerHTML = `
            <option value="">
                Выберите франшизу
            </option>
        `;

        if (!Array.isArray(franchises)) {
            throw new Error(
                "Сервер вернул некорректный список франшиз"
            );
        }

        franchises.forEach((franchise) => {
            const option = document.createElement("option");

            option.value = franchise.id;
            option.textContent = franchise.name;

            franchiseSelect.appendChild(option);
        });

        if (franchises.length === 0) {
            franchiseSelect.innerHTML = `
                <option value="">
                    Нет доступных франшиз
                </option>
            `;
        }

    } catch (error) {
        franchiseSelect.innerHTML = `
            <option value="">
                Не удалось загрузить
            </option>
        `;

        showError(
            error.message ||
            "Не удалось загрузить франшизы"
        );
    }
}


/* -------------------------------------------------------
   Backend error
------------------------------------------------------- */

async function getErrorMessage(response) {
    try {
        const data = await response.json();

        if (typeof data.detail === "string") {
            return data.detail;
        }

        if (Array.isArray(data.detail)) {
            return data.detail
                .map((item) => {
                    if (typeof item === "string") {
                        return item;
                    }

                    if (item.msg) {
                        return item.msg;
                    }

                    return "Ошибка проверки данных";
                })
                .join("; ");
        }

        return `Ошибка сервера (${response.status})`;

    } catch {
        return `Ошибка сервера (${response.status})`;
    }
}


/* -------------------------------------------------------
   Loading
------------------------------------------------------- */

function setSaving(value) {
    saveButton.disabled = value;
    saveButton.classList.toggle(
        "loading",
        value
    );

    saveButtonText.textContent =
        value
            ? "Сохранение..."
            : "Сохранить";
}


/* -------------------------------------------------------
   Submit
------------------------------------------------------- */

async function submitOperation(event) {
    event.preventDefault();

    clearError();

    const quantityText =
        quantityInput.value.trim().replace(",", ".");

    const quantity = Number(quantityText);

    const operationDate =
        operationDateInput.value;

    if (!Number.isFinite(quantity) || quantity <= 0) {
        showError(
            "Введите количество больше нуля"
        );

        quantityInput.focus();
        return;
    }

    if (!operationDate) {
        showError(
            "Выберите дату операции"
        );

        operationDateInput.focus();
        return;
    }

    if (
        selectedOperationType === "FRANCHISE" &&
        !franchiseSelect.value
    ) {
        showError(
            "Выберите франшизу"
        );

        franchiseSelect.focus();
        return;
    }

    const payload = {
        type: selectedOperationType,
        meat_type: selectedMeatType,
        quantity: quantity,
        operation_date: operationDate,
    };

    /*
     * ВАЖНО:
     * franchise_id отправляем только для FRANCHISE.
     *
     * Backend специально запрещает franchise_id
     * для остальных типов операций.
     */
    if (selectedOperationType === "FRANCHISE") {
        payload.franchise_id =
            Number(franchiseSelect.value);
    }

    setSaving(true);

    try {
        console.log(
            "Создаём операцию:",
            payload
        );

        const response = await apiFetch(
            API.operations,
            {
                method: "POST",
                body: JSON.stringify(payload),
            }
        );

        if (!response.ok) {
            const message =
                await getErrorMessage(response);

            throw new Error(message);
        }

        const operation =
            await response.json();

        console.log(
            "Операция создана:",
            operation
        );

        /*
         * Возвращаемся на Dashboard.
         * Параметр created нужен, чтобы показать
         * пользователю сообщение "Операция сохранена".
         */
        window.location.replace(
            "/dashboard?created=1"
        );

    } catch (error) {
        console.error(
            "Ошибка создания операции:",
            error
        );

        showError(
            error.message ||
            "Не удалось сохранить операцию"
        );

        setSaving(false);
    }
}


/* -------------------------------------------------------
   Events
------------------------------------------------------- */

document
    .querySelectorAll("[data-operation-type]")
    .forEach((button) => {

        button.addEventListener(
            "click",
            async () => {

                clearError();

                await selectOperationType(
                    button.dataset.operationType
                );
            }
        );
    });


document
    .querySelectorAll("[data-meat-type]")
    .forEach((button) => {

        button.addEventListener(
            "click",
            () => {

                clearError();

                selectedMeatType =
                    button.dataset.meatType;

                updateMeatButtons();
            }
        );
    });


form.addEventListener(
    "submit",
    submitOperation
);


backButton.addEventListener(
    "click",
    () => {
        window.location.href =
            "/dashboard";
    }
);


/* -------------------------------------------------------
   Init
------------------------------------------------------- */

operationDateInput.value =
    getMoscowTodayISO();

updateOperationTypeButtons();
updateMeatButtons();