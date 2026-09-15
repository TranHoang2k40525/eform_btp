(function () {
    "use strict";

    var state = {
        workbook: null,
        sheetIndex: 0,
        tableIndex: 0,
        hot: null,
        gridLayout: null,
        busy: false,
        dragDepth: 0
    };

    var elements = {
        file: document.getElementById("file"),
        importButton: document.getElementById("import"),
        emptyImportButton: document.getElementById("emptyImport"),
        confirmButton: document.getElementById("confirm"),
        downloadTemplateButton: document.getElementById("downloadTemplate"),
        serviceStatus: document.getElementById("serviceStatus"),
        statusBar: document.getElementById("statusBar"),
        statusText: document.getElementById("statusText"),
        statusMeta: document.getElementById("statusMeta"),
        fileName: document.getElementById("fileName"),
        sheetCount: document.getElementById("sheetCount"),
        tableCount: document.getElementById("tableCount"),
        valueRowCount: document.getElementById("valueRowCount"),
        sheetTabs: document.getElementById("sheetTabs"),
        tableTabs: document.getElementById("tableTabs"),
        gridHost: document.getElementById("gridHost"),
        hotContainer: document.getElementById("hotContainer"),
        emptyState: document.getElementById("emptyState"),
        loadingState: document.getElementById("loadingState"),
        dropOverlay: document.getElementById("dropOverlay"),
        rangeInfo: document.getElementById("rangeInfo"),
        selectionInfo: document.getElementById("selectionInfo"),
        confidenceBadge: document.getElementById("confidenceBadge"),
        metaSheet: document.getElementById("metaSheet"),
        metaRange: document.getElementById("metaRange"),
        metaHeaders: document.getElementById("metaHeaders"),
        metaSize: document.getElementById("metaSize"),
        metaDuration: document.getElementById("metaDuration"),
        columnCount: document.getElementById("columnCount"),
        hierarchyList: document.getElementById("hierarchyList"),
        noticeList: document.getElementById("noticeList")
    };

    function getValue(object, camelName, pascalName) {
        if (!object) return undefined;
        return object[camelName] !== undefined ? object[camelName] : object[pascalName];
    }

    function setStatus(message, type, meta) {
        elements.statusText.textContent = message;
        elements.statusMeta.textContent = meta || "";
        elements.statusBar.classList.remove("is-error", "is-warning");
        if (type === "error") elements.statusBar.classList.add("is-error");
        if (type === "warning") elements.statusBar.classList.add("is-warning");
    }

    function setServiceState(status, text) {
        elements.serviceStatus.classList.remove("is-ready", "is-error");
        if (status === "ready") elements.serviceStatus.classList.add("is-ready");
        if (status === "error") elements.serviceStatus.classList.add("is-error");
        elements.serviceStatus.lastElementChild.textContent = text;
    }

    function setBusy(busy) {
        state.busy = busy;
        elements.loadingState.hidden = !busy;
        elements.emptyState.hidden = busy || !!state.workbook;
        elements.importButton.disabled = busy;
        elements.emptyImportButton.disabled = busy;
        elements.confirmButton.disabled = busy || !selectedTable();
    }

    function formatNumber(value) {
        return new Intl.NumberFormat("vi-VN").format(Number(value || 0));
    }

    function formatDuration(milliseconds) {
        var value = Number(milliseconds || 0);
        return value < 1000
            ? Math.round(value) + " ms"
            : (value / 1000).toLocaleString("vi-VN", { maximumFractionDigits: 2 }) + " giây";
    }

    function formatBytes(bytes) {
        var value = Number(bytes || 0);
        if (value < 1024) return value + " B";
        if (value < 1024 * 1024) return (value / 1024).toFixed(1) + " KB";
        return (value / (1024 * 1024)).toFixed(1) + " MB";
    }

    function currentSheet() {
        var sheets = state.workbook && Array.isArray(state.workbook.sheets)
            ? state.workbook.sheets
            : [];
        return sheets[state.sheetIndex] || null;
    }

    function selectedTable() {
        var sheet = currentSheet();
        return sheet && Array.isArray(sheet.tables) ? sheet.tables[state.tableIndex] || null : null;
    }

    function firstSheetWithTable(workbook) {
        for (var index = 0; index < workbook.sheets.length; index += 1) {
            if (Array.isArray(workbook.sheets[index].tables) && workbook.sheets[index].tables.length) {
                return index;
            }
        }
        return 0;
    }

    async function checkHealth() {
        try {
            var response = await fetch("/api/import/health", { cache: "no-store" });
            var result = await response.json();
            var status = getValue(result, "status", "Status");
            if (response.ok && status === "ready") {
                var model = getValue(result, "model", "Model") || {};
                setServiceState("ready", model.name ? "Model " + model.name + " sẵn sàng" : "Model sẵn sàng");
                return;
            }
        } catch (error) {
        }
        setServiceState("error", "AI service chưa sẵn sàng");
    }

    function unwrapResponse(result) {
        var success = getValue(result, "success", "Success");
        var message = getValue(result, "message", "Message");
        var payload = getValue(result, "aiResult", "AiResult") || result;
        return { success: success !== false, message: message, payload: payload };
    }

    function readResponseError(result, fallback) {
        if (!result) return fallback;
        var detail = getValue(result, "detail", "Detail");
        var message = getValue(result, "message", "Message");
        if (typeof detail === "string") return detail;
        if (detail) return JSON.stringify(detail);
        return message || fallback;
    }

    async function processFile(file) {
        if (!file || state.busy) return;
        if (!/\.(xlsx|xlsm)$/i.test(file.name)) {
            setStatus("Chỉ chấp nhận file .xlsx hoặc .xlsm.", "error");
            return;
        }
        if (file.size > 50 * 1024 * 1024) {
            setStatus("File Excel vượt giới hạn 50 MB.", "error");
            return;
        }

        state.workbook = null;
        destroyGrid();
        resetPreview();
        setBusy(true);
        setStatus("Đang gửi workbook tới model và đọc cấu trúc bảng.", null, formatBytes(file.size));
        elements.fileName.textContent = file.name;

        var form = new FormData();
        form.append("file", file, file.name);
        form.append("originalFileName", file.name);
        var context = window.eformImportContext || {};
        if (context.userId) form.append("userId", context.userId);
        if (context.documentId) form.append("documentId", context.documentId);

        try {
            var response = await fetch("/api/import/parse", { method: "POST", body: form });
            var responseText = await response.text();
            var result;
            try {
                result = JSON.parse(responseText);
            } catch (parseError) {
                throw new Error("Backend trả dữ liệu không đúng định dạng JSON.");
            }
            if (!response.ok) throw new Error(readResponseError(result, "Không thể đọc workbook."));

            var normalized = unwrapResponse(result);
            if (!normalized.success) throw new Error(normalized.message || "AI chưa phát hiện được vùng bảng.");
            loadWorkbook(normalized.payload);
            setServiceState("ready", "Model đang hoạt động");

            var summary = normalized.payload.summary || {};
            var message = normalized.message || "AI đã tách dữ liệu để xem trước.";
            setStatus(
                message,
                normalized.payload.requiresReview ? "warning" : null,
                formatDuration(normalized.payload.durationMs)
            );
            elements.statusMeta.textContent = formatBytes(summary.uploadBytes) + " | " + formatDuration(normalized.payload.durationMs);
        } catch (error) {
            state.workbook = null;
            resetPreview();
            showEmptyError(error.message || "Không thể đọc workbook.");
            setStatus(error.message || "Không thể đọc workbook.", "error");
        } finally {
            setBusy(false);
            elements.file.value = "";
        }
    }

    function loadWorkbook(workbook) {
        workbook = workbook || {};
        workbook.sheets = Array.isArray(workbook.sheets) ? workbook.sheets : [];
        state.workbook = workbook;
        state.sheetIndex = firstSheetWithTable(workbook);
        state.tableIndex = 0;
        elements.emptyState.hidden = true;
        elements.fileName.textContent = workbook.sourceFile || "Workbook Excel";
        renderWorkbookSummary();
        renderSheetTabs();
        renderTableTabs();
        renderSelectedTable();
    }

    function renderWorkbookSummary() {
        var summary = state.workbook.summary || {};
        elements.sheetCount.textContent = formatNumber(summary.sheetCount || state.workbook.sheets.length);
        elements.tableCount.textContent = formatNumber(summary.tableCount);
        elements.valueRowCount.textContent = formatNumber(summary.valueRowCount);
        elements.metaDuration.textContent = formatDuration(state.workbook.durationMs);
    }

    function makeTab(label, className, active, clickHandler) {
        var button = document.createElement("button");
        button.type = "button";
        button.className = className + (active ? " is-active" : "");
        button.textContent = label;
        button.setAttribute("aria-selected", active ? "true" : "false");
        button.addEventListener("click", clickHandler);
        return button;
    }

    function renderSheetTabs() {
        elements.sheetTabs.textContent = "";
        state.workbook.sheets.forEach(function (sheet, index) {
            var tableTotal = Array.isArray(sheet.tables) ? sheet.tables.length : 0;
            var label = sheet.sheetName + " (" + tableTotal + ")";
            elements.sheetTabs.appendChild(makeTab(label, "sheet-tab", index === state.sheetIndex, function () {
                state.sheetIndex = index;
                state.tableIndex = 0;
                renderSheetTabs();
                renderTableTabs();
                renderSelectedTable();
            }));
        });
    }

    function renderTableTabs() {
        elements.tableTabs.textContent = "";
        var sheet = currentSheet();
        if (!sheet || !Array.isArray(sheet.tables) || sheet.tables.length < 2) return;
        sheet.tables.forEach(function (table, index) {
            var label = "Vùng " + (index + 1) + ": " + table.sourceRange;
            elements.tableTabs.appendChild(makeTab(label, "table-tab", index === state.tableIndex, function () {
                state.tableIndex = index;
                renderTableTabs();
                renderSelectedTable();
            }));
        });
    }

    function renderSelectedTable() {
        var table = selectedTable();
        var sheet = currentSheet();
        if (!table || !sheet) {
            destroyGrid();
            showEmptyError("Sheet này không có vùng bảng được model nhận diện.");
            elements.confirmButton.disabled = true;
            renderInspector(null, sheet);
            return;
        }

        elements.emptyState.hidden = true;
        elements.confirmButton.disabled = false;
        renderGrid(table);
        renderInspector(table, sheet);
    }

    function rangeOrigin(sourceRange) {
        var match = /^([A-Z]+)(\d+):([A-Z]+)(\d+)$/i.exec(sourceRange || "");
        if (!match) return { column: 0, row: 1 };
        var column = 0;
        match[1].toUpperCase().split("").forEach(function (letter) {
            column = column * 26 + letter.charCodeAt(0) - 64;
        });
        return { column: column - 1, row: Number(match[2]) };
    }

    function buildStyleMap(table) {
        var map = {};
        (table.cellStyles || []).forEach(function (style) {
            map[style.row + ":" + style.col] = style;
        });
        return map;
    }

    function buildFormulaMap(table) {
        var map = {};
        (table.formulaCells || []).forEach(function (cell) {
            map[cell.row + ":" + cell.col] = cell.formula;
        });
        return map;
    }

    function normalizedColumnWidths(table, columnTotal) {
        var source = Array.isArray(table.columnWidths) ? table.columnWidths : [];
        var widths = [];
        for (var col = 0; col < columnTotal; col += 1) {
            var width = Number(source[col]);
            widths.push(Number.isFinite(width) && width > 0 ? Math.max(48, Math.min(width, 420)) : 96);
        }
        return widths;
    }

    function normalizedRowHeights(table, rowTotal, headerRows) {
        var source = Array.isArray(table.rowHeights) ? table.rowHeights : [];
        var heights = [];
        for (var row = 0; row < rowTotal; row += 1) {
            var height = Number(source[row]);
            height = Number.isFinite(height) && height > 0 ? height : 28;
            heights.push(row < headerRows ? Math.max(28, Math.min(height, 42)) : Math.max(22, height));
        }
        return heights;
    }

    function sum(values) {
        return values.reduce(function (total, value) { return total + value; }, 0);
    }

    function applyOuterGridSize(contentWidth) {
        var availableWidth = elements.gridHost.parentElement
            ? elements.gridHost.parentElement.clientWidth
            : document.documentElement.clientWidth;
        var fullWidth = Math.max(availableWidth, contentWidth);
        elements.gridHost.classList.add("has-table");
        elements.gridHost.style.width = fullWidth + "px";
        elements.gridHost.style.height = "auto";
        elements.hotContainer.style.width = fullWidth + "px";
        elements.hotContainer.style.height = "auto";
        return fullWidth;
    }

    function renderGrid(table) {
        destroyGrid();
        var origin = rangeOrigin(table.sourceRange);
        var styleMap = buildStyleMap(table);
        var formulaMap = buildFormulaMap(table);
        var columns = table.columns || [];
        var data = (table.data || []).map(function (row) { return row.slice(); });
        var headerRows = Math.max(0, Math.min(Number(table.headerRows || 0), data.length));
        var columnTotal = data.reduce(function (maximum, row) { return Math.max(maximum, row.length); }, columns.length);
        var columnWidths = normalizedColumnWidths(table, columnTotal);
        var rowHeights = normalizedRowHeights(table, data.length, headerRows);
        var columnHeaderHeight = 26;
        var rowHeaderWidth = 52;
        var headerTopOffsets = [];
        var currentTop = columnHeaderHeight;
        for (var headerIndex = 0; headerIndex < headerRows; headerIndex += 1) {
            headerTopOffsets.push(currentTop);
            currentTop += rowHeights[headerIndex];
        }
        var contentWidth = rowHeaderWidth + sum(columnWidths) + 4;
        var fullWidth = applyOuterGridSize(contentWidth);
        state.gridLayout = { contentWidth: contentWidth };

        function renderer(instance, td, row, col, prop, value, cellProperties) {
            Handsontable.renderers.TextRenderer.apply(this, arguments);
            var style = styleMap[row + ":" + col] || {};
            td.style.backgroundColor = "";
            td.style.color = "";
            td.style.fontWeight = "";
            td.style.fontStyle = "";
            td.style.textAlign = "";
            td.style.verticalAlign = "middle";
            td.style.whiteSpace = "normal";
            td.style.wordBreak = "break-word";
            td.style.top = "";
            if (style.fill) td.style.backgroundColor = style.fill;
            if (style.fontColor) td.style.color = style.fontColor;
            if (style.bold) td.style.fontWeight = "700";
            if (style.italic) td.style.fontStyle = "italic";
            if (["left", "center", "right", "justify"].indexOf(style.horizontal) >= 0) {
                td.style.textAlign = style.horizontal;
            }
            if (["top", "center", "bottom"].indexOf(style.vertical) >= 0) {
                td.style.verticalAlign = style.vertical === "center" ? "middle" : style.vertical;
            }
            if (!style.wrapText && row >= headerRows) td.style.whiteSpace = "nowrap";

            if (row < headerRows) {
                var headerText = document.createElement("div");
                headerText.className = "eform-header-text";
                headerText.textContent = value === null || value === undefined ? "" : String(value);
                td.textContent = "";
                td.appendChild(headerText);
                td.style.top = headerTopOffsets[row] + "px";
            }

            var formula = formulaMap[row + ":" + col];
            var path = columns[col] && Array.isArray(columns[col].headerPath)
                ? columns[col].headerPath.join(" > ")
                : "";
            td.title = formula
                ? "Công thức nguồn: " + formula
                : (row < headerRows ? (path || String(value || "")) : path);
        }

        state.hot = new Handsontable(elements.hotContainer, {
            data: data,
            width: fullWidth,
            height: "auto",
            rowHeaders: function (row) { return String(origin.row + row); },
            rowHeaderWidth: rowHeaderWidth,
            colHeaders: function (col) {
                return Handsontable.helper.spreadsheetColumnLabel(origin.column + col);
            },
            columnHeaderHeight: columnHeaderHeight,
            fixedRowsTop: 0,
            fixedRowsBottom: 0,
            mergeCells: table.mergeCells || [],
            colWidths: columnWidths,
            rowHeights: rowHeights,
            cells: function (row, col) {
                return {
                    readOnly: true,
                    renderer: renderer,
                    className: row < Number(table.headerRows || 0) ? "eform-header-cell" : ""
                };
            },
            readOnly: true,
            stretchH: "none",
            autoWrapCol: false,
            autoWrapRow: false,
            manualColumnResize: true,
            manualRowResize: true,
            autoColumnSize: false,
            autoRowSize: false,
            copyPaste: true,
            fillHandle: false,
            contextMenu: false,
            outsideClickDeselects: false,
            fragmentSelection: true,
            renderAllRows: true,
            viewportColumnRenderingOffset: columnTotal,
            viewportRowRenderingOffset: data.length,
            licenseKey: "non-commercial-and-evaluation",
            afterGetColHeader: function (col, th) {
                th.classList.add("eform-sticky-column-header");
            },
            afterGetRowHeader: function (row, th) {
                var isHeader = row >= 0 && row < headerRows;
                th.classList.toggle("eform-sticky-row-header", isHeader);
                th.style.top = isHeader ? headerTopOffsets[row] + "px" : "";
            },
            afterSelectionEnd: function (row, col, row2, col2) {
                var rows = Math.abs(row2 - row) + 1;
                var cols = Math.abs(col2 - col) + 1;
                elements.selectionInfo.textContent = rows + " hàng, " + cols + " cột đang chọn";
            }
        });
        elements.rangeInfo.textContent = "Vùng " + table.sourceRange + " | " + table.headerRows + " dòng tiêu đề";
        elements.selectionInfo.textContent = "Cuộn ngoài trang | Tiêu đề bám khi chạm mép trên";
    }

    function destroyGrid() {
        if (state.hot) {
            state.hot.destroy();
            state.hot = null;
        }
        elements.hotContainer.textContent = "";
        elements.gridHost.classList.remove("has-table");
        elements.gridHost.style.width = "";
        elements.gridHost.style.height = "";
        elements.hotContainer.style.width = "";
        elements.hotContainer.style.height = "";
        state.gridLayout = null;
    }

    function renderInspector(table, sheet) {
        if (!table) {
            elements.metaSheet.textContent = sheet ? sheet.sheetName : "Chưa chọn";
            elements.metaRange.textContent = "Không có vùng bảng";
            elements.metaHeaders.textContent = "0";
            elements.metaSize.textContent = "0 x 0";
            elements.columnCount.textContent = "0 cột";
            elements.confidenceBadge.textContent = "Chưa nhận diện";
            elements.confidenceBadge.className = "confidence-badge is-neutral";
            elements.hierarchyList.innerHTML = '<p class="muted-copy">Không có cấu trúc cột để hiển thị.</p>';
            renderNotices(["Hãy thử workbook khác hoặc bổ sung mẫu tương tự vào dataset."]);
            return;
        }

        var confidence = Number(table.confidence || 0);
        elements.metaSheet.textContent = sheet.sheetName;
        elements.metaRange.textContent = table.sourceRange;
        elements.metaHeaders.textContent = String(table.headerRows || 0);
        elements.metaSize.textContent = (table.rowCount || 0) + " x " + (table.columnCount || 0);
        elements.columnCount.textContent = (table.columnCount || 0) + " cột";
        elements.confidenceBadge.textContent = (confidence * 100).toLocaleString("vi-VN", { maximumFractionDigits: 1 }) + "% tin cậy";
        elements.confidenceBadge.className = "confidence-badge " + (confidence >= .75 ? "is-good" : "is-warning");
        renderHierarchy(table.columns || []);

        var notices = (state.workbook.warnings || []).slice();
        if (confidence < .75) notices.push("Vùng hiện tại có độ tin cậy thấp. Cần kiểm tra kỹ ranh giới bảng.");
        if (Number(table.trimmedFooterRows || 0) > 0) {
            notices.push("Đã loại " + table.trimmedFooterRows + " dòng ghi chú hoặc chữ ký nằm ngoài bảng dữ liệu.");
        }
        notices.push("Tiêu đề nhiều cấp được giữ bằng ô gộp và đường dẫn cột, chưa thực hiện mapping vào biểu đích.");
        renderNotices(notices);
    }

    function renderHierarchy(columns) {
        elements.hierarchyList.textContent = "";
        if (!columns.length) {
            elements.hierarchyList.innerHTML = '<p class="muted-copy">Không có đường dẫn tiêu đề.</p>';
            return;
        }
        columns.forEach(function (column) {
            var node = document.createElement("div");
            node.className = "hierarchy-node";
            var title = document.createElement("strong");
            var code = column.columnCode ? " (" + column.columnCode + ")" : "";
            title.textContent = column.excelColumn + code + ": " + (column.label || "Không có tên");
            var path = document.createElement("div");
            path.className = "hierarchy-path";
            path.textContent = (column.headerPath || []).join(" > ") || "Không có tiêu đề";
            node.appendChild(title);
            node.appendChild(path);
            elements.hierarchyList.appendChild(node);
        });
    }

    function renderNotices(notices) {
        elements.noticeList.textContent = "";
        var values = notices && notices.length ? notices : ["Không có cảnh báo từ model."];
        values.forEach(function (message, index) {
            var item = document.createElement("div");
            item.className = "notice " + (index === 0 && state.workbook && state.workbook.requiresReview ? "is-warning" : "is-info");
            item.textContent = String(message);
            elements.noticeList.appendChild(item);
        });
    }

    function showEmptyError(message) {
        elements.emptyState.hidden = false;
        elements.emptyState.querySelector("h2").textContent = "Chưa thể tạo bản xem trước";
        elements.emptyState.querySelector("p").textContent = message;
    }

    function resetPreview() {
        elements.sheetTabs.textContent = "";
        elements.tableTabs.textContent = "";
        elements.sheetCount.textContent = "0";
        elements.tableCount.textContent = "0";
        elements.valueRowCount.textContent = "0";
        elements.rangeInfo.textContent = "Chưa chọn vùng bảng";
        elements.selectionInfo.textContent = "Dùng thanh cuộn ngoài của trang";
        elements.metaSheet.textContent = "Chưa chọn";
        elements.metaRange.textContent = "Chưa chọn";
        elements.metaHeaders.textContent = "0";
        elements.metaSize.textContent = "0 x 0";
        elements.metaDuration.textContent = "0 ms";
        elements.columnCount.textContent = "0 cột";
        elements.confidenceBadge.textContent = "Chưa có kết quả";
        elements.confidenceBadge.className = "confidence-badge is-neutral";
        elements.hierarchyList.innerHTML = '<p class="muted-copy">Đường dẫn tiêu đề sẽ xuất hiện sau khi model phát hiện bảng.</p>';
        elements.noticeList.innerHTML = '<p class="muted-copy">Chưa có cảnh báo.</p>';
        elements.confirmButton.disabled = true;
    }

    function confirmImport() {
        var table = selectedTable();
        var sheet = currentSheet();
        if (!table || !sheet) return;

        var selected = {
            sourceFile: state.workbook.sourceFile,
            model: state.workbook.model,
            sheetIndex: sheet.sheetIndex,
            sheetName: sheet.sheetName,
            sourceRange: table.sourceRange,
            headerRows: table.headerRows,
            data: state.hot ? state.hot.getData() : table.data,
            mergeCells: table.mergeCells || [],
            columns: table.columns || [],
            formulaCells: table.formulaCells || [],
            confidence: table.confidence
        };
        var detail = { selected: selected, workbook: state.workbook };
        window.dispatchEvent(new CustomEvent("eform:ai-import-confirmed", { detail: detail }));
        if (window.parent && window.parent !== window) {
            window.parent.postMessage({ type: "eform:ai-import-confirmed", payload: detail }, window.location.origin);
        }
        if (window.eformImportContext && typeof window.eformImportContext.onConfirm === "function") {
            window.eformImportContext.onConfirm(detail);
        }
        setStatus("Dữ liệu đã sẵn sàng để giao diện biểu tiếp nhận.", null, sheet.sheetName + " | " + table.sourceRange);
    }

    function openFilePicker() {
        if (!state.busy) elements.file.click();
    }

    function downloadTemplate() {
        var context = window.eformImportContext || {};
        if (context.templateUrl) {
            window.location.assign(context.templateUrl);
            return;
        }
        setStatus("Chưa cấu hình đường dẫn tải template cho màn hình này.", "warning");
    }

    elements.importButton.addEventListener("click", openFilePicker);
    elements.emptyImportButton.addEventListener("click", openFilePicker);
    elements.confirmButton.addEventListener("click", confirmImport);
    elements.downloadTemplateButton.addEventListener("click", downloadTemplate);
    elements.file.addEventListener("change", function (event) {
        processFile(event.target.files && event.target.files[0]);
    });

    ["dragenter", "dragover", "dragleave", "drop"].forEach(function (eventName) {
        document.addEventListener(eventName, function (event) {
            event.preventDefault();
            event.stopPropagation();
        });
    });
    document.addEventListener("dragenter", function () {
        state.dragDepth += 1;
        if (!state.busy) elements.dropOverlay.hidden = false;
    });
    document.addEventListener("dragleave", function () {
        state.dragDepth = Math.max(0, state.dragDepth - 1);
        if (!state.dragDepth) elements.dropOverlay.hidden = true;
    });
    document.addEventListener("drop", function (event) {
        state.dragDepth = 0;
        elements.dropOverlay.hidden = true;
        var file = event.dataTransfer && event.dataTransfer.files && event.dataTransfer.files[0];
        processFile(file);
    });

    var resizeFrame = null;
    window.addEventListener("resize", function () {
        if (!state.hot || !state.gridLayout) return;
        if (resizeFrame) window.cancelAnimationFrame(resizeFrame);
        resizeFrame = window.requestAnimationFrame(function () {
            var width = applyOuterGridSize(state.gridLayout.contentWidth);
            state.hot.updateSettings({ width: width, height: "auto" });
            resizeFrame = null;
        });
    });

    window.EFormAiImportPreview = {
        load: loadWorkbook,
        getWorkbook: function () { return state.workbook; },
        getSelectedTable: selectedTable,
        confirm: confirmImport
    };

    resetPreview();
    checkHealth();
}());
