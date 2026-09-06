"use strict";

const TOKEN_KEY = "meat_accounting_access_token";

const API = {
    me: "/api/v1/auth/me",
    stock: "/api/v1/stock",
    operations: "/api/v1/operations",
};

const elements = {
    currentDate: document.getElementById("current-date"),

    filletStock: document.getElementById("fillet-stock"),
    skinStock: document.getElementById("skin-stock"),

    incoming: document.getElementById("incoming"),
    vertel: document.getElementById("vertel"),
    franchise: document.getElementById("franchise"),
    totalStock: document.getElementById("total-stock"),

    newOperation: document.getElementById("new-operation"),

    loading: document.getElementById("loading"),
    toast: document.getElementById("toast"),
};

/* --------------------------------------------------
   Helpers
-------------------------------------------------- */

function getToken() {
    return localStorage.getItem(TOKEN_KEY);
}

function showLoading() {
    elements.loading?.classList.add("visible");
}

function hideLoading() {
    elements.loading?.classList.remove("visible");
}

let toastTimer = null;

function showToast(message) {
    if (!elements.toast) {
        return;
    }

    clearTimeout(toastTimer);

    elements.toast.textContent = message;
    elements.toast.classList.add("visible");

    toastTimer = setTimeout(() => {
        elements.toast.classList.remove("visible");
    }, 3000);
}

function formatKg(value) {
    if (value === null || value === undefined || value === "") {
        return "—";
    }

    const number = Number(value);

    if (!Number.isFinite(number)) {
        return "—";
    }

    return new Intl.NumberFormat("ru-RU", {
        minimumFractionDigits: 1,
        maximumFractionDigits: 1,
    }).format(number);
}

function formatSignedKg(value) {
    if (value === null || value === undefined || value === "") {
        return "—";
    }

    const number = Number(value);

    if (!Number.isFinite(number)) {
        return "—";
    }

    if (number === 0) {
        return "0";
    }

    const sign = number > 0 ? "+" : "−";

    return `${sign}${formatKg(Math.abs(number))}`;
}

function setText(element, value) {
    if (element) {
        element.textContent = value;
    }
}

function setDate() {
    const today = new Date();

    const date = new Intl.DateTimeFormat("ru-RU", {
        day: "numeric",
        month: "long",
    }).format(today);

    setText(elements.currentDate, date);
}

/* --------------------------------------------------
   API
-------------------------------------------------- */

async function apiFetch(url, options = {}) {
    const token = getToken();

    const headers = {
        Accept: "application/json",
        ...(options.headers || {}),
    };

    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(url, {
        ...options,
        headers,
    });

    if (response.status === 401) {
        localStorage.removeItem(TOKEN_KEY);
        window.location.href = "/";

        throw new Error("Сессия истекла");
    }

    let data = null;

    const contentType = response.headers.get("content-type") || "";

    if (contentType.includes("application/json")) {
        data = await response.json();
    } else {
        data = await response.text();
    }

    if (!response.ok) {
        const message =
            data?.detail ||
            data?.message ||
            "Не удалось выполнить запрос";

        throw new Error(message);
    }

    return data;
}

async function checkAuth() {
    const token = getToken();

    if (!token) {
        window.location.href = "/";
        return false;
    }

    try {
        await apiFetch(API.me);
        return true;
    } catch (error) {
        console.error("Auth error:", error);

        localStorage.removeItem(TOKEN_KEY);
        window.location.href = "/";

        return false;
    }
}

/* --------------------------------------------------
   Stock
-------------------------------------------------- */

function extractStockValue(stock, possibleKeys) {
    if (!stock || typeof stock !== "object") {
        return null;
    }

    for (const key of possibleKeys) {
        if (
            Object.prototype.hasOwnProperty.call(stock, key) &&
            stock[key] !== null &&
            stock[key] !== undefined
        ) {
            return stock[key];
        }
    }

    return null;
}

function renderStock(data) {
    const source = data?.data || data;

    const fillet = extractStockValue(source, [
        "fillet",
        "fillet_stock",
        "fillet_kg",
        "stock_fillet",
    ]);

    const skin = extractStockValue(source, [
        "skin",
        "skin_stock",
        "skin_kg",
        "with_skin",
        "stock_skin",
    ]);

    setText(elements.filletStock, formatKg(fillet));
    setText(elements.skinStock, formatKg(skin));

    const total =
        Number(fillet || 0) +
        Number(skin || 0);

    setText(elements.totalStock, formatKg(total));
}

async function loadStock() {
    try {
        const data = await apiFetch(API.stock);

        renderStock(data);

        return data;
    } catch (error) {
        console.error("Stock error:", error);

        setText(elements.filletStock, "—");
        setText(elements.skinStock, "—");
        setText(elements.totalStock, "—");

        showToast("Не удалось загрузить остатки");

        return null;
    }
}

/* --------------------------------------------------
   Operations
-------------------------------------------------- */

function getOperationType(operation) {
    if (!operation || typeof operation !== "object") {
        return "";
    }

    return String(
        operation.operation_type ??
        operation.type ??
        operation.operation ??
        operation.kind ??
        ""
    ).toLowerCase().trim();
}

function getOperationAmount(operation) {
    if (!operation || typeof operation !== "object") {
        return 0;
    }

    return Number(
        operation.quantity ??
        operation.amount ??
        operation.weight ??
        operation.kg ??
        operation.value ??
        0
    );
}

function isToday(value) {
    if (!value) {
        return false;
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return false;
    }

    const now = new Date();

    return (
        date.getFullYear() === now.getFullYear() &&
        date.getMonth() === now.getMonth() &&
        date.getDate() === now.getDate()
    );
}

function getOperationsArray(data) {
    if (Array.isArray(data)) {
        return data;
    }

    if (Array.isArray(data?.items)) {
        return data.items;
    }

    if (Array.isArray(data?.operations)) {
        return data.operations;
    }

    if (Array.isArray(data?.data)) {
        return data.data;
    }

    return [];
}

/*
 * Backend использует:
 *
 * INCOMING  — поступление
 * SPIT      — вертель
 * WRITE_OFF — списание
 * CONVECTION — конвекция
 * FRANCHISE — франшиза
 *
 * Здесь отображаем:
 * поступление -> плюс
 * вертель     -> минус
 * франшиза    -> минус
 */
function renderOperations(data) {
    const operations = getOperationsArray(data);

    let incoming = 0;
    let vertel = 0;
    let franchise = 0;

    for (const operation of operations) {
        const operationDate =
            operation.date ??
            operation.created_at ??
            operation.createdAt ??
            operation.operation_date;

        /*
         * Показываем операции только за сегодня.
         * Если даты нет — считаем запись актуальной.
         */
        if (operationDate && !isToday(operationDate)) {
            continue;
        }

        const type = getOperationType(operation);
        const amount = Math.abs(getOperationAmount(operation));

        /*
         * ПОСТУПЛЕНИЕ
         */
        if (
            type === "incoming" ||
            type === "income" ||
            type === "arrival" ||
            type === "receipt" ||
            type.includes("приход")
        ) {
            incoming += amount;
            continue;
        }

        /*
         * ВЕРТЕЛЬ
         *
         * Backend: SPIT
         */
        if (
            type === "spit" ||
            type === "vertel" ||
            type === "vertel" ||
            type.includes("верт")
        ) {
            vertel -= amount;
            continue;
        }

        /*
         * ФРАНШИЗА
         */
        if (
            type === "franchise" ||
            type.includes("франш")
        ) {
            franchise -= amount;
            continue;
        }
    }

    setText(
        elements.incoming,
        formatSignedKg(incoming)
    );

    setText(
        elements.vertel,
        formatSignedKg(vertel)
    );

    setText(
        elements.franchise,
        formatSignedKg(franchise)
    );
}

async function loadOperations() {
    try {
        const data = await apiFetch(API.operations);

        renderOperations(data);

        return data;
    } catch (error) {
        console.error("Operations error:", error);

        setText(elements.incoming, "—");
        setText(elements.vertel, "—");
        setText(elements.franchise, "—");

        return null;
    }
}

/* --------------------------------------------------
   New operation
-------------------------------------------------- */

function setupNewOperationButton() {
    elements.newOperation?.addEventListener("click", () => {
        window.location.href = "/new-operation";
    });
}

/* --------------------------------------------------
   Navigation
-------------------------------------------------- */

function setupNavigation() {
    const historyLink = document.getElementById("history-link");
    const reportsLink = document.getElementById("reports-link");

    historyLink?.addEventListener("click", (event) => {
        event.preventDefault();

        showToast("Раздел «История» пока не подключён");
    });

    reportsLink?.addEventListener("click", (event) => {
        event.preventDefault();

        showToast("Раздел «Отчёты» пока не подключён");
    });
}

/* --------------------------------------------------
   Init
-------------------------------------------------- */

async function initDashboard() {
    setDate();

    const authenticated = await checkAuth();

    if (!authenticated) {
        return;
    }

    showLoading();

    try {
        await Promise.all([
            loadStock(),
            loadOperations(),
        ]);
    } finally {
        hideLoading();
    }
}

setupNewOperationButton();
setupNavigation();
initDashboard();