"use strict";

const TOKEN_KEY = "meat_accounting_access_token";

const API = {
    me: "/api/v1/auth/me",
    reports: "/api/v1/reports",
};

let reportState = {
    period: "month",
    dateFrom: null,
    dateTo: null,
};

const elements = {
    reportDate: document.getElementById("report-date"),
    reportRows: document.getElementById("report-rows"),
    reportPeriod: document.getElementById("report-period"),
    monthPicker: document.getElementById("month-picker"),
    reportMonth: document.getElementById("report-month"),
    dayPicker: document.getElementById("day-picker"),
    reportDay: document.getElementById("report-day"),
    excelButton: document.getElementById("excel-button"),
    lastUpdate: document.getElementById("last-update"),
    toast: document.getElementById("toast"),
};

function getToken() {
    return localStorage.getItem(TOKEN_KEY);
}

function setText(element, value) {
    if (!element) return;
    element.textContent = value;
}

function formatKg(value) {
    if (value === null || value === undefined || value === "") {
        return "?";
    }

    const number = Number(value);
    if (!Number.isFinite(number)) {
        return "?";
    }

    return new Intl.NumberFormat("ru-RU", {
        maximumFractionDigits: 3,
    }).format(number);
}

function formatDate(value) {
    const [year, month, day] = value.split("-").map(Number);
    return new Intl.DateTimeFormat("ru-RU", {
        day: "numeric",
        month: "short",
        year: "numeric",
        timeZone: "UTC",
    }).format(new Date(Date.UTC(year, month - 1, day)));
}

function formatRange(dateFrom, dateTo) {
    if (dateFrom === dateTo) {
        return formatDate(dateFrom);
    }

    return `${formatDate(dateFrom)} — ${formatDate(dateTo)}`;
}

let toastTimer = null;

function showToast(message) {
    if (!elements.toast) return;

    clearTimeout(toastTimer);
    elements.toast.textContent = message;
    elements.toast.classList.add("visible");

    toastTimer = setTimeout(() => {
        elements.toast.classList.remove("visible");
    }, 3000);
}

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
        throw new Error("?????? ???????");
    }

    let data = null;
    const contentType = response.headers.get("content-type") || "";

    if (contentType.includes("application/json")) {
        data = await response.json();
    } else {
        data = await response.text();
    }

    if (!response.ok) {
        const message = data?.detail || data?.message || "?? ??????? ????????? ??????";
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

function buildReportUrl(period, dateFrom = null, dateTo = null) {
    const params = new URLSearchParams({ period });

    if (dateFrom) {
        params.set("date_from", dateFrom);
    }

    if (dateTo) {
        params.set("date_to", dateTo);
    }

    return `${API.reports}?${params.toString()}`;
}

function buildExportUrl() {
    const params = new URLSearchParams({ period: reportState.period });

    if (reportState.dateFrom) {
        params.set("date_from", reportState.dateFrom);
    }

    if (reportState.dateTo) {
        params.set("date_to", reportState.dateTo);
    }

    return `/api/v1/exports/excel?${params.toString()}`;
}

function renderReport(report) {
    const rows = Array.isArray(report?.items) ? report.items : [];
    const meatNames = {
        FILLET: "Филе",
        SKIN: "С кожей",
    };

    elements.reportRows.replaceChildren();
    for (const item of rows) {
        const row = document.createElement("tr");
        const values = [
            meatNames[item.meat_type] || item.meat_type,
            item.opening,
            item.incoming,
            item.spit,
            item.write_off,
            item.convection,
            item.franchise,
            item.closing,
        ];

        for (const value of values) {
            const cell = document.createElement("td");
            cell.textContent =
                typeof value === "number" ? formatKg(value) : value;
            row.appendChild(cell);
        }

        elements.reportRows.appendChild(row);
    }

    if (rows.length === 0) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");
        cell.colSpan = 8;
        cell.textContent = "За выбранный период операций нет";
        row.appendChild(cell);
        elements.reportRows.appendChild(row);
    }

    reportState = {
        period: "custom",
        dateFrom: report.date_from,
        dateTo: report.date_to,
    };

    setText(elements.reportDate, formatRange(report.date_from, report.date_to));
    elements.reportMonth.value = report.date_from.slice(0, 7);
    if (report.date_from === report.date_to) {
        elements.reportDay.value = report.date_from;
    }

    const now = new Date();
    const updateLabel = new Intl.DateTimeFormat("ru-RU", {
        day: "numeric",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
    }).format(now);

    setText(elements.lastUpdate, `Обновлено: ${updateLabel}`);
}

function monthBounds(value) {
    const match = /^(\d{4})-(\d{2})$/.exec(value);
    if (!match) {
        throw new Error("Выберите месяц");
    }

    const year = Number(match[1]);
    const month = Number(match[2]);
    if (month < 1 || month > 12) {
        throw new Error("Выберите корректный месяц");
    }

    const lastDay = new Date(Date.UTC(year, month, 0)).getUTCDate();
    return {
        dateFrom: `${match[1]}-${match[2]}-01`,
        dateTo: `${match[1]}-${match[2]}-${String(lastDay).padStart(2, "0")}`,
    };
}

function currentDate() {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, "0");
    const day = String(now.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
}

async function loadReport(period = "month", dateFrom = null, dateTo = null) {
    reportState = { period, dateFrom, dateTo };
    try {
        const url = buildReportUrl(period, dateFrom, dateTo);
        const data = await apiFetch(url);
        renderReport(data);
        return data;
    } catch (error) {
        console.error("Report error:", error);
        showToast(error.message || "Не удалось загрузить отчёт");
        setText(elements.lastUpdate, "Не удалось обновить отчёт");
        return null;
    }
}

async function downloadExcel() {
    const token = getToken();

    if (!token) {
        window.location.href = "/";
        return;
    }

    try {
        const response = await fetch(buildExportUrl(), {
            method: "GET",
            headers: {
                Authorization: `Bearer ${token}`,
                Accept: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            },
        });

        if (response.status === 401) {
            localStorage.removeItem(TOKEN_KEY);
            window.location.href = "/";
            return;
        }

        if (!response.ok) {
            const payload = await response.json().catch(() => null);
            throw new Error(payload?.detail || "Не удалось скачать Excel");
        }

        const blob = await response.blob();
        const contentDisposition = response.headers.get("content-disposition") || "";
        const match = contentDisposition.match(/filename\s*=\s*"?([^";]+)"?/i);

        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = match ? match[1] : "meat_report.xlsx";
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);
    } catch (error) {
        console.error("Excel export error:", error);
        showToast(error.message || "Не удалось скачать Excel");
    }
}

function setupExcelButton() {
    elements.excelButton?.addEventListener("click", downloadExcel);
}

function setupMonthPicker() {
    elements.reportMonth?.addEventListener("change", async () => {
        try {
            const { dateFrom, dateTo } = monthBounds(elements.reportMonth.value);
            await loadReport("custom", dateFrom, dateTo);
        } catch (error) {
            showToast(error.message);
        }
    });
}

function setupPeriodPicker() {
    elements.reportPeriod?.addEventListener("change", async () => {
        const isMonth = elements.reportPeriod.value === "month";
        elements.monthPicker.hidden = !isMonth;
        elements.dayPicker.hidden = isMonth;

        try {
            if (isMonth) {
                const { dateFrom, dateTo } = monthBounds(elements.reportMonth.value);
                await loadReport("custom", dateFrom, dateTo);
            } else {
                if (!elements.reportDay.value) {
                    elements.reportDay.value = currentDate();
                }
                const date = elements.reportDay.value;
                await loadReport("custom", date, date);
            }
        } catch (error) {
            showToast(error.message);
        }
    });

    elements.reportDay?.addEventListener("change", async () => {
        if (!elements.reportDay.value) {
            showToast("Выберите дату");
            return;
        }
        await loadReport("custom", elements.reportDay.value, elements.reportDay.value);
    });
}

async function initReports() {
    const authenticated = await checkAuth();
    if (!authenticated) return;

    setupMonthPicker();
    setupPeriodPicker();
    setupExcelButton();
    await loadReport("month");
}

initReports();