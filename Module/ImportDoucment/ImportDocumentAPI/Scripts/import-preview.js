(function () {
    "use strict";

    var state = { file: null, response: null, tables: [], hot: null };
    var el = {
        input: document.getElementById("fileInput"),
        choose: document.getElementById("chooseFileButton"),
        importButton: document.getElementById("importButton"),
        clear: document.getElementById("clearButton"),
        dropZone: document.getElementById("dropZone"),
        selectedFile: document.getElementById("selectedFile"),
        uploadError: document.getElementById("uploadError"),
        progress: document.getElementById("progress"),
        progressBar: document.getElementById("progressBar"),
        progressText: document.getElementById("progressText"),
        result: document.getElementById("resultSection"),
        resultFile: document.getElementById("resultFileName"),
        resultSheet: document.getElementById("resultSheetName"),
        resultRange: document.getElementById("resultRange"),
        resultRows: document.getElementById("resultRowCount"),
        resultColumns: document.getElementById("resultColumnCount"),
        resultMessage: document.getElementById("resultMessage"),
        saveStatus: document.getElementById("saveStatus"),
        tabs: document.getElementById("sheetTabs"),
        grid: document.getElementById("hotContainer"),
        service: document.getElementById("serviceStatus"),
        serviceText: document.getElementById("serviceStatusText")
    };

    function showMessage(target, text, type) {
        target.textContent = text || "";
        target.className = "message " + (type || "");
        target.hidden = !text;
    }

    function validateFile(file) {
        if (!file) return "Vui lòng chọn file Excel.";
        var name = (file.name || "").toLowerCase();
        if (name.slice(-5) !== ".xlsx" && name.slice(-5) !== ".xlsm") {
            return "Chỉ chấp nhận file .xlsx hoặc .xlsm.";
        }
        if (file.size === 0) return "File Excel rỗng.";
        if (file.size > 50 * 1024 * 1024) return "File Excel vượt giới hạn 50 MB.";
        return "";
    }

    function setFile(file) {
        var error = validateFile(file);
        state.file = error ? null : file;
        showMessage(el.uploadError, error, "error-message");
        el.selectedFile.textContent = file && !error ? file.name + " (" + formatBytes(file.size) + ")" : "Chưa chọn file";
        el.importButton.disabled = !state.file;
        el.clear.disabled = !state.file;
    }

    function formatBytes(size) {
        if (size < 1024) return size + " B";
        if (size < 1024 * 1024) return (size / 1024).toFixed(1) + " KB";
        return (size / (1024 * 1024)).toFixed(1) + " MB";
    }

    function setBusy(busy) {
        el.choose.disabled = busy;
        el.importButton.disabled = busy || !state.file;
        el.clear.disabled = busy || !state.file;
        el.progress.hidden = !busy;
        if (busy) {
            el.progressBar.style.width = "35%";
            el.progressText.textContent = "Đang gửi file tới AI và chờ kết quả...";
        }
    }

    function getTables(response) {
        var tables = [];
        var sheets = response && response.sheets;
        (Array.isArray(sheets) ? sheets : []).forEach(function (sheet, sheetIndex) {
            (Array.isArray(sheet.tables) ? sheet.tables : []).forEach(function (table, tableIndex) {
                tables.push({ sheet: sheet, table: table, sheetIndex: sheetIndex, tableIndex: tableIndex });
            });
        });
        return tables;
    }

    function renderTable(item) {
        var table = item.table || {};
        var data = Array.isArray(table.data) ? table.data : [];
        var cellStyles = Array.isArray(table.cellStyles) ? table.cellStyles : [];
        var styleMap = {};
        cellStyles.forEach(function (style) {
            styleMap[style.row + ":" + style.col] = style;
        });
        if (!data.length) {
            showMessage(el.resultMessage, "AI không trả về dữ liệu để hiển thị.", "error-message");
            return;
        }
        el.resultSheet.textContent = item.sheet.sheetName || "-";
        el.resultRange.textContent = table.sourceRange || "-";
        el.resultRows.textContent = table.valueRowCount || 0;
        el.resultColumns.textContent = table.columnCount || (data[0] ? data[0].length : 0);
        el.grid.innerHTML = "";
        state.hot = new Handsontable(el.grid, {
            data: data,
            rowHeaders: true,
            colHeaders: true,
            mergeCells: Array.isArray(table.mergeCells) ? table.mergeCells : [],
            readOnly: true,
            licenseKey: "non-commercial-and-evaluation",
            stretchH: "none",
            colWidths: Array.isArray(table.columnWidths) ? table.columnWidths : undefined,
            rowHeights: Array.isArray(table.rowHeights) ? table.rowHeights : undefined,
            autoWrapRow: true,
            autoWrapCol: true,
            wordWrap: true,
            width: "100%",
            height: 560,
            manualColumnResize: false,
            manualRowResize: false,
            contextMenu: false,
            fillHandle: false,
            cells: function (row, col) {
                var style = styleMap[row + ":" + col];
                if (!style) return {};
                return {
                    className: style.isHeader ? "excel-header-cell" : "excel-value-cell"
                };
            },
            afterGetColHeader: function (col, th) {
                th.classList.add("readonly-header");
            }
        });
    }

    function renderTabs() {
        el.tabs.innerHTML = "";
        if (state.tables.length <= 1) {
            el.tabs.hidden = true;
            return;
        }
        el.tabs.hidden = false;
        state.tables.forEach(function (item, index) {
            var button = document.createElement("button");
            button.type = "button";
            button.textContent = item.sheet.sheetName + " · Bảng " + (item.tableIndex + 1);
            button.className = index === 0 ? "active" : "";
            button.addEventListener("click", function () {
                Array.prototype.forEach.call(el.tabs.children, function (tab) { tab.classList.remove("active"); });
                button.classList.add("active");
                renderTable(item);
            });
            el.tabs.appendChild(button);
        });
    }

    async function importFile() {
        if (!state.file || el.importButton.disabled) return;
        setBusy(true);
        showMessage(el.uploadError, "", "");
        el.result.hidden = true;
        try {
            var form = new FormData();
            form.append("file", state.file, state.file.name);
            form.append("originalFileName", state.file.name);
            var response = await fetch("/api/import/parse", { method: "POST", body: form });
            var payload = await response.json();
            if (!response.ok || !payload.success) {
                throw new Error(payload.message || payload.detail || "Không thể phân tích file Excel.");
            }
            state.response = payload;
            state.tables = getTables(payload.aiResult || {});
            if (!state.tables.length) throw new Error("AI không phát hiện được bảng trong workbook.");
            el.resultFile.textContent = payload.fileName || state.file.name;
            el.result.hidden = false;
            renderTabs();
            renderTable(state.tables[0]);
            el.saveStatus.textContent = payload.saved
                ? "Đã lưu kết quả vào cơ sở dữ liệu"
                : "Đã nhận kết quả AI";
            showMessage(el.resultMessage, payload.message || "Đã bóc tách và lưu kết quả thành công.", "success-message");
            el.progressBar.style.width = "100%";
        } catch (error) {
            showMessage(el.uploadError, error.message || "Có lỗi khi import file Excel.", "error-message");
        } finally {
            setBusy(false);
            if (el.progress.hidden === false) {
                setTimeout(function () { el.progress.hidden = true; }, 700);
            }
        }
    }

    async function checkService() {
        try {
            var response = await fetch("/api/import/health", { cache: "no-store" });
            var payload = await response.json();
            var ready = response.ok && payload.status === "ready";
            el.service.className = "service-status " + (ready ? "ready" : "offline");
            el.serviceText.textContent = ready ? "AI sẵn sàng" : "AI chưa sẵn sàng";
        } catch (error) {
            el.service.className = "service-status offline";
            el.serviceText.textContent = "Không kết nối được AI";
        }
    }

    el.choose.addEventListener("click", function () { el.input.click(); });
    el.input.addEventListener("change", function () { setFile(el.input.files[0]); el.input.value = ""; });
    el.importButton.addEventListener("click", importFile);
    el.clear.addEventListener("click", function () { setFile(null); });
    ["dragenter", "dragover"].forEach(function (eventName) {
        el.dropZone.addEventListener(eventName, function (event) {
            event.preventDefault();
            el.dropZone.classList.add("dragging");
        });
    });
    ["dragleave", "drop"].forEach(function (eventName) {
        el.dropZone.addEventListener(eventName, function (event) {
            event.preventDefault();
            el.dropZone.classList.remove("dragging");
        });
    });
    el.dropZone.addEventListener("drop", function (event) { setFile(event.dataTransfer.files[0]); });
    el.dropZone.addEventListener("keydown", function (event) {
        if (event.key === "Enter" || event.key === " ") el.input.click();
    });
    checkService();
}());
