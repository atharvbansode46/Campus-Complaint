/* =========================================================
   CAMPUS COMPLAINT SYSTEM
   Main JavaScript
========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    console.log("Campus Complaint System loaded successfully.");


    /* =====================================================
       COMPLAINT DESCRIPTION CHARACTER COUNTER
    ====================================================== */

    const description = document.getElementById("description");
    const charCount = document.getElementById("charCount");

    if (description && charCount) {

        function updateCharacterCount() {

            charCount.textContent =
                description.value.length;

        }

        description.addEventListener(
            "input",
            updateCharacterCount
        );

        updateCharacterCount();
    }


    /* =====================================================
       COMPLAINT FORM VALIDATION
    ====================================================== */

    const complaintForm =
        document.getElementById("complaintForm");

    if (complaintForm) {

        complaintForm.addEventListener(
            "submit",
            function (event) {

                const title =
                    document.getElementById("title");

                const description =
                    document.getElementById("description");

                const category =
                    document.getElementById("category");

                const confirmation =
                    document.getElementById("confirmation");


                /* Title validation */

                if (
                    !title ||
                    title.value.trim().length < 5
                ) {

                    event.preventDefault();

                    alert(
                        "Please enter a complaint title " +
                        "with at least 5 characters."
                    );

                    if (title) {
                        title.focus();
                    }

                    return;
                }


                /* Description validation */

                if (
                    !description ||
                    description.value.trim().length < 15
                ) {

                    event.preventDefault();

                    alert(
                        "Please provide more details " +
                        "about your complaint."
                    );

                    if (description) {
                        description.focus();
                    }

                    return;
                }


                /* Category validation */

                if (
                    !category ||
                    category.value === ""
                ) {

                    event.preventDefault();

                    alert(
                        "Please select a complaint category."
                    );

                    if (category) {
                        category.focus();
                    }

                    return;
                }


                /* Confirmation validation */

                if (
                    confirmation &&
                    !confirmation.checked
                ) {

                    event.preventDefault();

                    alert(
                        "Please confirm that the " +
                        "information provided is accurate."
                    );

                    confirmation.focus();

                    return;
                }


                /* Final confirmation */

                const confirmed =
                    confirm(
                        "Are you sure you want to submit " +
                        "this complaint?"
                    );

                if (!confirmed) {

                    event.preventDefault();

                    return;
                }


                /* Disable submit button */

                const submitButton =
                    complaintForm.querySelector(
                        'button[type="submit"]'
                    );

                if (submitButton) {

                    submitButton.disabled = true;

                    submitButton.textContent =
                        "Submitting...";
                }

            }
        );
    }


    /* =====================================================
       DELETE / DANGEROUS ACTION CONFIRMATION
    ====================================================== */

    const dangerButtons =
        document.querySelectorAll(
            ".danger-action"
        );

    dangerButtons.forEach(function (button) {

        button.addEventListener(
            "click",
            function (event) {

                const message =
                    button.dataset.confirm ||
                    "Are you sure you want to continue?";

                if (!confirm(message)) {

                    event.preventDefault();

                }

            }
        );

    });


    /* =====================================================
       AUTO HIDE FLASH MESSAGES
    ====================================================== */

    const alerts =
        document.querySelectorAll(
            ".alert"
        );

    alerts.forEach(function (alert) {

        setTimeout(function () {

            alert.style.transition =
                "opacity 0.5s ease";

            alert.style.opacity = "0";

            setTimeout(function () {

                alert.remove();

            }, 500);

        }, 5000);

    });


    /* =====================================================
       SUPPORT BUTTON
    ====================================================== */

    const supportForms =
        document.querySelectorAll(
            ".support-card form"
        );

    supportForms.forEach(function (form) {

        form.addEventListener(
            "submit",
            function (event) {

                const button =
                    form.querySelector(
                        "button"
                    );

                if (!button) {
                    return;
                }


                /* Already supported */

                if (
                    button.textContent
                        .includes("Supported")
                ) {

                    const removeSupport =
                        confirm(
                            "Do you want to remove " +
                            "your support?"
                        );

                    if (!removeSupport) {

                        event.preventDefault();

                    }

                    return;
                }


                /* Add support */

                const confirmed =
                    confirm(
                        "Do you want to support this complaint?"
                    );

                if (!confirmed) {

                    event.preventDefault();

                    return;
                }


                button.disabled = true;

                button.textContent =
                    "Supporting...";

            }
        );

    });


    /* =====================================================
       ADMIN UPDATE FORM
    ====================================================== */

    const adminForms =
        document.querySelectorAll(
            ".admin-update-form"
        );

    adminForms.forEach(function (form) {

        form.addEventListener(
            "submit",
            function (event) {

                const status =
                    form.querySelector(
                        'select[name="status"]'
                    );

                const resolution =
                    form.querySelector(
                        'textarea[name="resolution"]'
                    );


                /* Resolved complaint should have resolution */

                if (
                    status &&
                    status.value === "Resolved" &&
                    resolution &&
                    resolution.value.trim() === ""
                ) {

                    event.preventDefault();

                    alert(
                        "Please add a resolution note " +
                        "before marking the complaint as Resolved."
                    );

                    resolution.focus();

                    return;
                }


                const confirmed =
                    confirm(
                        "Are you sure you want to update " +
                        "this complaint?"
                    );

                if (!confirmed) {

                    event.preventDefault();

                    return;
                }


                const button =
                    form.querySelector(
                        'button[type="submit"]'
                    );

                if (button) {

                    button.disabled = true;

                    button.textContent =
                        "Updating...";

                }

            }
        );

    });

    /* =====================================================
       DASHBOARD COMPLAINT FILTERS AND COLLAPSIBLE DETAILS
    ====================================================== */

    document.querySelectorAll(".complaint-filters").forEach(function (filterBar) {
        const cards = document.querySelectorAll(
            filterBar.dataset.filterTarget + ".complaint-item"
        );
        const buttons = filterBar.querySelectorAll(".filter-button");

        buttons.forEach(function (button) {
            button.addEventListener("click", function () {
                const selected = button.dataset.filter;

                buttons.forEach(function (item) {
                    item.classList.toggle("active", item === button);
                });

                cards.forEach(function (card) {
                    const status = card.dataset.status;
                    const isResolved =
                        status === "Resolved" || status === "Closed";
                    const visible =
                        selected === "all" ||
                        status === selected ||
                        (selected === "pending" && !isResolved) ||
                        (selected === "resolved" && isResolved);

                    card.hidden = !visible;
                });
            });
        });
    });

    document.querySelectorAll(".complaint-toggle").forEach(function (button) {
        button.addEventListener("click", function () {
            const details = button.nextElementSibling;
            const isHidden = details.hidden;

            details.hidden = !isHidden;
            button.setAttribute("aria-expanded", String(isHidden));
            button.textContent = isHidden
                ? "Hide complaint details"
                : "View complaint details";
        });
    });

    /* =====================================================
       ADMIN ANALYTICS AND AI REPORT
    ====================================================== */

    const analyticsMessage =
        document.getElementById("analyticsMessage");

    function showAnalyticsMessage(message, isError) {
        if (!analyticsMessage) {
            return;
        }

        analyticsMessage.textContent = message;
        analyticsMessage.className =
            isError ? "analytics-message error" : "analytics-message";
    }

    function renderBarChart(elementId, items) {
        const chart = document.getElementById(elementId);

        if (!chart) {
            return;
        }

        chart.innerHTML = "";

        if (!items || items.length === 0) {
            chart.textContent = "No complaint data available.";
            return;
        }

        const maximum = Math.max.apply(
            null,
            items.map(function (item) {
                return item.count;
            })
        );

        items.forEach(function (item) {
            const row = document.createElement("div");
            row.className = "bar-row";

            const label = document.createElement("span");
            label.className = "bar-label";
            label.textContent = item.label;

            const track = document.createElement("div");
            track.className = "bar-track";

            const fill = document.createElement("div");
            fill.className = "bar-fill";
            fill.style.width =
                Math.max((item.count / maximum) * 100, 3) + "%";

            const value = document.createElement("span");
            value.className = "bar-value";
            value.textContent = item.count;

            track.appendChild(fill);
            row.appendChild(label);
            row.appendChild(track);
            row.appendChild(value);
            chart.appendChild(row);
        });
    }

    function renderAnalytics(data) {
        const metrics = document.getElementById("analyticsMetrics");

        if (metrics) {
            metrics.innerHTML =
                "<div><strong>" + data.total +
                "</strong><span>Total records</span></div>" +
                "<div><strong>" + data.resolved_total +
                "</strong><span>Resolved or closed</span></div>" +
                "<div><strong>" + data.resolution_rate +
                "%</strong><span>Resolution rate</span></div>" +
                "<div><strong>" + data.average_support +
                "</strong><span>Average support</span></div>";
        }

        renderBarChart("statusChart", data.status);
        renderBarChart("categoryChart", data.category);
        renderBarChart("departmentChart", data.department);
        renderBarChart("priorityChart", data.priority);
        renderBarChart("monthlyChart", data.monthly);
    }

    function loadAnalytics() {
        showAnalyticsMessage("Loading verified analytics...", false);

        fetch("/admin/analytics")
            .then(function (response) {
                return response.json().then(function (data) {
                    if (!response.ok) {
                        throw new Error(data.error || "Unable to load analytics.");
                    }
                    return data;
                });
            })
            .then(function (data) {
                renderAnalytics(data);
                showAnalyticsMessage("Analytics updated from the database.", false);
            })
            .catch(function (error) {
                showAnalyticsMessage(error.message, true);
            });
    }

    const refreshAnalytics =
        document.getElementById("refreshAnalytics");

    if (refreshAnalytics) {
        refreshAnalytics.addEventListener("click", loadAnalytics);
        loadAnalytics();
    }

    const loadAiSummary =
        document.getElementById("loadAiSummary");

    if (loadAiSummary) {
        loadAiSummary.addEventListener("click", function () {
            const summary = document.getElementById("aiSummary");

            loadAiSummary.disabled = true;
            loadAiSummary.textContent = "Generating...";
            showAnalyticsMessage("Sending minimized complaint data to Gemini...", false);

            fetch("/admin/ai-summary", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                }
            })
                .then(function (response) {
                    return response.json().then(function (data) {
                        if (!response.ok) {
                            throw new Error(
                                data.error || "Unable to generate the AI report."
                            );
                        }
                        return data;
                    });
                })
                .then(function (data) {
                    summary.textContent = data.summary;
                    summary.hidden = false;
                    showAnalyticsMessage("AI report generated.", false);
                })
                .catch(function (error) {
                    showAnalyticsMessage(error.message, true);
                })
                .finally(function () {
                    loadAiSummary.disabled = false;
                    loadAiSummary.textContent = "Generate AI Report";
                });
        });
    }


    /* =====================================================
       PREVENT DOUBLE FORM SUBMISSION
    ====================================================== */

    const forms =
        document.querySelectorAll("form");

    forms.forEach(function (form) {

        form.addEventListener(
            "submit",
            function () {

                form.classList.add(
                    "form-submitting"
                );

            }
        );

    });


    /* =====================================================
       MOBILE MENU / NAVBAR
    ====================================================== */

    const navbar =
        document.querySelector(".navbar");

    if (navbar) {

        window.addEventListener(
            "scroll",
            function () {

                if (window.scrollY > 20) {

                    navbar.classList.add(
                        "navbar-scrolled"
                    );

                } else {

                    navbar.classList.remove(
                        "navbar-scrolled"
                    );

                }

            }
        );

    }


    /* =====================================================
       PRIORITY VISUAL WARNING
    ====================================================== */

    const priority =
        document.getElementById("priority");

    if (priority) {

        function updatePriorityWarning() {

            const value =
                priority.value.toLowerCase();


            if (value === "critical") {

                priority.style.borderColor =
                    "#dc2626";

            }

            else if (value === "high") {

                priority.style.borderColor =
                    "#ea580c";

            }

            else if (value === "medium") {

                priority.style.borderColor =
                    "#ca8a04";

            }

            else {

                priority.style.borderColor =
                    "#d1d5db";

            }

        }

        priority.addEventListener(
            "change",
            updatePriorityWarning
        );

        updatePriorityWarning();

    }


    /* =====================================================
       PAGE LOADED
    ====================================================== */

    console.log(
        "All Campus Complaint JavaScript features initialized."
    );

});