document.addEventListener("DOMContentLoaded", () => {
    const operationsList =
        document.getElementById("operations-list");

    const loadingState =
        document.getElementById("loading-state");

    const errorState =
        document.getElementById("error-state");

    const emptyState =
        document.getElementById("empty-state");

    const retryButton =
        document.getElementById("retry-button");

    const filterButtons =
        document.querySelectorAll("[data-filter]");

    let currentFilter = "all";

    let operations = [];


    // =========================================================
    // TOKEN
    // =========================================================

    function getToken() {
        return (
            localStorage.getItem("access_token") ||
            sessionStorage.getItem("access_token") ||
            localStorage.getItem("token") ||
            sessionStorage.getItem("token")
        );
    }


    // =========================================================
    // LOAD
    // =========================================================

    async function loadHistory() {
        showLoading();

        const token = getToken();

        if (!token) {
            window.location.href = "/";
            return;
        }

        try {
            const response = await fetch(
                "/api/v1/operations?limit=200",
                {
                    method: "GET",

                    headers: {
                        "Authorization": `Bearer ${token}`,
                        "Content-Type": "application/json"
                    }
                }
            );


            if (response.status === 401) {
                localStorage.removeItem("access_token");
                sessionStorage.removeItem("access_token");
                localStorage.removeItem("token");
                sessionStorage.removeItem("token");

                window.location.href = "/";

                return;
            }


            if (!response.ok) {
                throw new Error(
                    `HTTP ${response.status}`
                );
            }


            const data = await response.json();

            operations = Array.isArray(data.items)
                ? data.items
                : [];


            operations.sort((a, b) => {
                const idA = Number(a.id || 0);
                const idB = Number(b.id || 0);

                return idB - idA;
            });


            render();

        } catch (error) {
            console.error(
                "Ошибка загрузки истории:",
                error
            );

            showError();
        }
    }


    // =========================================================
    // FILTERS
    // =========================================================

    filterButtons.forEach((button) => {
        button.addEventListener("click", () => {

            currentFilter =
                button.dataset.filter || "all";


            filterButtons.forEach((item) => {
                item.classList.remove("active");
            });


            button.classList.add("active");


            render();
        });
    });


    // =========================================================
    // RETRY
    // =========================================================

    if (retryButton) {
        retryButton.addEventListener(
            "click",
            loadHistory
        );
    }


    // =========================================================
    // RENDER
    // =========================================================

    function render() {
        hide(loadingState);
        hide(errorState);

        operationsList.innerHTML = "";


        const filtered =
            getFilteredOperations();


        if (filtered.length === 0) {
            show(emptyState);
            return;
        }


        hide(emptyState);


        const groups =
            groupByDate(filtered);


        Object.entries(groups).forEach(
            ([date, items]) => {

                const group =
                    createDateGroup(
                        date,
                        items
                    );

                operationsList.appendChild(
                    group
                );
            }
        );
    }


    // =========================================================
    // FILTER DATA
    // =========================================================

    function getFilteredOperations() {
        if (currentFilter === "all") {
            return operations;
        }


        return operations.filter(
            (operation) => {

                return (
                    String(operation.type)
                        .toUpperCase() ===
                    currentFilter
                );
            }
        );
    }


    // =========================================================
    // GROUP BY OPERATION DATE
    // =========================================================

    function groupByDate(items) {
        const groups = {};


        items.forEach((operation) => {

            const date =
                operation.operation_date ||
                getCreatedDate(operation) ||
                "unknown";


            if (!groups[date]) {
                groups[date] = [];
            }


            groups[date].push(operation);
        });


        return groups;
    }


    // =========================================================
    // DATE GROUP
    // =========================================================

    function createDateGroup(
        date,
        items
    ) {
        const group =
            document.createElement("div");

        group.className = "date-group";


        const title =
            document.createElement("h2");

        title.className = "date-title";

        title.textContent =
            formatDate(date);


        group.appendChild(title);


        items.forEach((operation) => {

            const card =
                createOperationCard(
                    operation
                );

            group.appendChild(card);
        });


        return group;
    }


    // =========================================================
    // OPERATION CARD
    // =========================================================

    function createOperationCard(
        operation
    ) {
        const card =
            document.createElement("article");

        card.className =
            "operation-card";


        if (
            String(operation.status)
                .toUpperCase() ===
            "CANCELLED"
        ) {
            card.classList.add("cancelled");
        }


        const info =
            document.createElement("div");

        info.className =
            "operation-info";


        const title =
            document.createElement("div");

        title.className =
            "operation-title";

        title.textContent =
            getOperationTitle(operation);


        const meta =
            document.createElement("div");

        meta.className =
            "operation-meta";

        meta.textContent =
            getOperationMeta(operation);


        info.appendChild(title);
        info.appendChild(meta);


        if (operation.comment) {
            const comment =
                document.createElement("div");

            comment.className =
                "operation-comment";

            comment.textContent =
                operation.comment;

            info.appendChild(comment);
        }


        const right =
            document.createElement("div");

        right.className =
            "operation-right";


        const amount =
            document.createElement("div");

        const cancelled =
            String(operation.status)
                .toUpperCase() ===
            "CANCELLED";


        const expense =
            isExpense(operation);


        amount.className =
            "operation-amount";


        if (cancelled) {
            amount.classList.add("cancelled");
        } else if (expense) {
            amount.classList.add("expense");
        } else {
            amount.classList.add("income");
        }


        amount.textContent =
            formatAmount(
                operation.quantity,
                expense
            );


        right.appendChild(amount);


        if (cancelled) {
            const status =
                document.createElement("div");

            status.className =
                "operation-status";

            status.textContent =
                `Отменена • ${formatTime(
                    operation.created_at
                )}`;

            right.appendChild(status);

        } else {

            const time =
                document.createElement("div");

            time.className =
                "operation-status";

            time.textContent =
                `${formatTime(
                    operation.created_at
                )} • ${getUserName(
                    operation
                )}`;

            right.appendChild(time);
        }


        card.appendChild(info);
        card.appendChild(right);


        return card;
    }


    // =========================================================
    // OPERATION TITLE
    // =========================================================

    function getOperationTitle(
        operation
    ) {
        const type =
            String(operation.type)
                .toUpperCase();


        const meat =
            getMeatTitle(
                operation.meat_type
            );


        let title;


        switch (type) {

            case "INCOMING":
                title = "Поступление";
                break;

            case "SPIT":
                title = "Вертель";
                break;

            case "WRITE_OFF":
                title = "Списание";
                break;

            case "CONVECTION":
                title = "Конвектомат";
                break;

            case "FRANCHISE":
                title =
                    operation.franchise_id
                        ? `Франшиза №${operation.franchise_id}`
                        : "Франшиза";
                break;

            default:
                title = "Операция";
        }


        return `${title} • ${meat}`;
    }


    // =========================================================
    // MEAT
    // =========================================================

    function getMeatTitle(
        meatType
    ) {
        switch (
            String(meatType)
                .toUpperCase()
        ) {

            case "FILLET":
                return "Филе";

            case "SKIN":
                return "С кожей";

            default:
                return meatType || "Мясо";
        }
    }


    // =========================================================
    // META
    // =========================================================

    function getOperationMeta(
        operation
    ) {
        const date =
            operation.operation_date ||
            getCreatedDate(operation);


        return formatDateLong(date);
    }


    // =========================================================
    // EXPENSE
    // =========================================================

    function isExpense(
        operation
    ) {
        const type =
            String(operation.type)
                .toUpperCase();


        return [
            "SPIT",
            "WRITE_OFF",
            "CONVECTION",
            "FRANCHISE"
        ].includes(type);
    }


    // =========================================================
    // USER
    // =========================================================

    function getUserName(
        operation
    ) {
        if (
            operation.user &&
            operation.user.username
        ) {
            return operation.user.username;
        }


        if (operation.username) {
            return operation.username;
        }


        if (
            operation.created_by !==
            undefined &&
            operation.created_by !== null
        ) {
            return `ID ${operation.created_by}`;
        }


        return "Пользователь";
    }


    // =========================================================
    // AMOUNT
    // =========================================================

    function formatAmount(
        quantity,
        expense
    ) {
        const number =
            Math.abs(
                Number(quantity) || 0
            );


        const formatted =
            number
                .toFixed(3)
                .replace(/\.?0+$/, "");


        return `${
            expense ? "−" : "+"
        }${formatted} кг`;
    }


    // =========================================================
    // DATE
    // =========================================================

    function getCreatedDate(
        operation
    ) {
        return (
            operation.created_at ||
            operation.createdAt ||
            null
        );
    }


    function formatDate(
        value
    ) {
        if (!value) {
            return "Без даты";
        }


        const date =
            new Date(
                `${value}T00:00:00`
            );


        if (
            Number.isNaN(
                date.getTime()
            )
        ) {
            return value;
        }


        const today =
            new Date();


        if (
            date.getFullYear() ===
                today.getFullYear() &&
            date.getMonth() ===
                today.getMonth() &&
            date.getDate() ===
                today.getDate()
        ) {
            return "Сегодня";
        }


        return date.toLocaleDateString(
            "ru-RU",
            {
                day: "numeric",
                month: "long"
            }
        );
    }


    function formatDateLong(
        value
    ) {
        if (!value) {
            return "";
        }


        const date =
            new Date(
                value.includes("T")
                    ? value
                    : `${value}T00:00:00`
            );


        if (
            Number.isNaN(
                date.getTime()
            )
        ) {
            return "";
        }


        return date.toLocaleDateString(
            "ru-RU",
            {
                day: "numeric",
                month: "long",
                year: "numeric"
            }
        );
    }


    // =========================================================
    // TIME
    // =========================================================

    function formatTime(
        value
    ) {
        if (!value) {
            return "--:--";
        }


        const date =
            new Date(value);


        if (
            Number.isNaN(
                date.getTime()
            )
        ) {
            return "--:--";
        }


        return date.toLocaleTimeString(
            "ru-RU",
            {
                hour: "2-digit",
                minute: "2-digit"
            }
        );
    }


    // =========================================================
    // STATES
    // =========================================================

    function show(element) {
        if (element) {
            element.hidden = false;
        }
    }


    function hide(element) {
        if (element) {
            element.hidden = true;
        }
    }


    function showLoading() {
        show(loadingState);

        hide(errorState);
        hide(emptyState);

        operationsList.innerHTML = "";
    }


    function showError() {
        hide(loadingState);
        hide(emptyState);

        show(errorState);

        operationsList.innerHTML = "";
    }


    // =========================================================
    // START
    // =========================================================

    loadHistory();
});