(() => {
  const initializeChart = (dataId, chartId, statusId) => {
    const chartDataElement = document.getElementById(dataId);
    const chartElement = document.getElementById(chartId);
    const chartStatus = document.getElementById(statusId);
    if (!chartDataElement || !chartElement || !chartStatus) return;

    if (!window.Plotly) {
      chartStatus.textContent =
        "The interactive chart could not load. Check your connection to the Plotly.js CDN and refresh.";
    } else {
      const chartJson = chartDataElement.textContent ?? "";

      if (chartJson.length > 0) {
        try {
          const figure = JSON.parse(chartJson);
          window.Plotly
            .newPlot(chartElement, figure.data, figure.layout, {
              responsive: true,
              displaylogo: false,
              modeBarButtonsToRemove: ["lasso2d", "select2d"],
            })
            .then(() => {
              chartStatus.textContent = "";
              chartStatus.hidden = true;
              if (typeof ResizeObserver !== "undefined") {
                const chartResizeObserver = new ResizeObserver(() => {
                  window.Plotly.Plots.resize(chartElement);
                });
                chartResizeObserver.observe(chartElement.parentElement ?? chartElement);
              }
            })
            .catch((error) => {
              console.error("Could not render the market trend chart.", error);
              chartStatus.textContent =
                "The interactive chart could not be rendered. Refresh the page to try again.";
            });
        } catch (error) {
          console.error("Could not read the market trend chart data.", error);
          chartStatus.textContent =
            "The interactive chart data could not be read. Refresh the page to try again.";
        }
      } else {
        chartStatus.textContent =
          "The interactive chart has no demo data. Refresh the page to try again.";
      }
    }
  };

  initializeChart("trend-chart-data", "market-trend-chart", "chart-status");
  initializeChart(
    "competitor-chart-data",
    "competitor-share-chart",
    "competitor-chart-status",
  );

  const importWorkspace = document.getElementById("data-import-workspace");
  if (importWorkspace) {
    const uploadForm = document.getElementById("csv-upload-form");
    const fileInput = document.getElementById("csv-file");
    const dropZone = document.getElementById("csv-drop-zone");
    const selectedFile = document.getElementById("selected-file");
    const validateButton = document.getElementById("validate-csv");
    const importButton = document.getElementById("import-csv");
    const resetButton = document.getElementById("reset-import");
    const status = document.getElementById("import-status");
    const results = document.getElementById("import-results");
    const stats = document.getElementById("import-stats");
    const columnsContainer = document.getElementById("detected-columns");
    const errorsContainer = document.getElementById("import-errors");
    const errorsList = document.getElementById("import-error-list");
    const previewTitle = document.getElementById("preview-title");
    const previewCaption = document.getElementById("preview-caption");
    const previewHead = document.getElementById("preview-head");
    const previewBody = document.getElementById("preview-body");
    const maxBytes = Number(importWorkspace.dataset.maxBytes);
    const storageKey = "marketscope:data-import:current";
    let stagedImport;

    const setImportStatus = (message, state = "info") => {
      status.textContent = message;
      status.className = `import-status is-${state}`;
    };

    const clearTable = () => {
      previewHead.replaceChildren();
      previewBody.replaceChildren();
    };

    const renderPreview = (records, columns, title) => {
      clearTable();
      previewTitle.textContent = title;
      previewCaption.textContent = records.length
        ? `Showing ${Math.min(records.length, 20)} of ${records.length} valid rows.`
        : "There are no valid rows to preview.";
      if (columns.length === 0) return;

      const headerRow = document.createElement("tr");
      columns.forEach((column) => {
        const cell = document.createElement("th");
        cell.scope = "col";
        cell.textContent = column;
        headerRow.append(cell);
      });
      previewHead.append(headerRow);

      records.slice(0, 20).forEach((record) => {
        const row = document.createElement("tr");
        columns.forEach((column) => {
          const cell = document.createElement("td");
          cell.textContent = String(record[column] ?? "");
          row.append(cell);
        });
        previewBody.append(row);
      });
    };

    const renderValidation = (payload) => {
      results.hidden = false;
      stats.replaceChildren();
      [
        ["Total rows", payload.total_rows],
        ["Valid rows", payload.valid_rows],
        ["Invalid rows", payload.invalid_rows],
      ].forEach(([label, value]) => {
        const item = document.createElement("div");
        item.className = "import-stat";
        const name = document.createElement("span");
        name.textContent = label;
        const count = document.createElement("strong");
        count.textContent = String(value);
        item.append(name, count);
        stats.append(item);
      });

      columnsContainer.replaceChildren();
      payload.columns.forEach((column) => {
        const tag = document.createElement("code");
        tag.textContent = column;
        columnsContainer.append(tag);
      });

      errorsList.replaceChildren();
      payload.errors.forEach((message) => {
        const item = document.createElement("li");
        item.textContent = message;
        errorsList.append(item);
      });
      if (payload.errors_truncated) {
        const item = document.createElement("li");
        item.textContent = "Additional row errors were omitted; fix these and validate again.";
        errorsList.append(item);
      }
      errorsContainer.hidden = payload.errors.length === 0;
      renderPreview(payload.preview, payload.columns, "Valid-row preview");
    };

    const showStoredImport = () => {
      try {
        const stored = sessionStorage.getItem(storageKey);
        if (!stored) return;
        const imported = JSON.parse(stored);
        if (!Array.isArray(imported.records) || !Array.isArray(imported.columns)) {
          sessionStorage.removeItem(storageKey);
          return;
        }
        stagedImport = imported;
        renderValidation({
          total_rows: imported.total_rows,
          valid_rows: imported.records.length,
          invalid_rows: imported.invalid_rows,
          columns: imported.columns,
          errors: imported.errors,
          errors_truncated: imported.errors_truncated,
          preview: imported.records,
        });
        importButton.disabled = true;
        setImportStatus(
          `${imported.records.length} valid rows are imported in this browser tab. Other dashboard pages still use demo data.`,
          "success",
        );
      } catch (error) {
        console.error("Could not restore the tab's imported CSV state.", error);
        setImportStatus("The previous tab import could not be restored. Validate the CSV again.", "error");
      }
    };

    fileInput.addEventListener("change", () => {
      const file = fileInput.files[0];
      selectedFile.textContent = file
        ? `${file.name} (${(file.size / 1024).toFixed(1)} KB)`
        : "No file selected";
      stagedImport = null;
      importButton.disabled = true;
      results.hidden = true;
      setImportStatus(file ? "Ready to validate the selected CSV." : "Choose a CSV file to begin.");
    });

    dropZone.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        fileInput.click();
      }
    });
    ["dragenter", "dragover"].forEach((eventName) => {
      dropZone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropZone.classList.add("is-dragging");
      });
    });
    ["dragleave", "drop"].forEach((eventName) => {
      dropZone.addEventListener(eventName, (event) => {
        event.preventDefault();
        dropZone.classList.remove("is-dragging");
      });
    });
    dropZone.addEventListener("drop", (event) => {
      const [file] = event.dataTransfer.files;
      if (!file) return;
      const transfer = new DataTransfer();
      transfer.items.add(file);
      fileInput.files = transfer.files;
      fileInput.dispatchEvent(new Event("change", { bubbles: true }));
    });

    uploadForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const file = fileInput.files[0];
      if (!file) {
        setImportStatus("Select a CSV file before validating.", "error");
        return;
      }
      if (!file.name.toLocaleLowerCase().endsWith(".csv")) {
        setImportStatus("Choose a file with the .csv extension.", "error");
        return;
      }
      if (file.size > maxBytes) {
        setImportStatus("The selected file exceeds the 2 MB upload limit.", "error");
        return;
      }

      validateButton.disabled = true;
      importButton.disabled = true;
      setImportStatus("Uploading and validating CSV…", "loading");
      try {
        const response = await fetch(uploadForm.action, {
          method: "POST",
          body: new FormData(uploadForm),
        });
        const payload = await response.json();
        if (payload.columns && payload.total_rows !== undefined) renderValidation(payload);
        if (!response.ok || !payload.ok) {
          stagedImport = null;
          setImportStatus(payload.message || "The CSV could not be validated.", "error");
          return;
        }

        stagedImport = payload;
        importButton.disabled = payload.valid_rows === 0;
        const summary = `${payload.valid_rows} valid and ${payload.invalid_rows} invalid rows.`;
        setImportStatus(
          payload.invalid_rows
            ? `${summary} You can import valid rows; fix invalid rows and upload again if needed.`
            : `${summary} The file is ready to import.`,
          payload.invalid_rows ? "warning" : "success",
        );
      } catch (error) {
        console.error("CSV upload or validation failed.", error);
        stagedImport = null;
        setImportStatus("The upload failed. Check your connection and try again.", "error");
      } finally {
        validateButton.disabled = false;
      }
    });

    importButton.addEventListener("click", () => {
      if (!stagedImport || stagedImport.valid_records.length === 0) return;
      const imported = {
        records: stagedImport.valid_records,
        columns: stagedImport.columns,
        total_rows: stagedImport.total_rows,
        invalid_rows: stagedImport.invalid_rows,
        errors: stagedImport.errors,
        errors_truncated: stagedImport.errors_truncated,
      };
      try {
        sessionStorage.setItem(storageKey, JSON.stringify(imported));
        renderValidation({
          ...imported,
          valid_rows: imported.records.length,
          preview: imported.records,
        });
        importButton.disabled = true;
        setImportStatus(
          `${imported.records.length} valid rows imported in this browser tab only. Other dashboard pages continue to use synthetic demo data.`,
          "success",
        );
      } catch (error) {
        console.error("Could not store the imported CSV in this browser tab.", error);
        setImportStatus("Import could not be saved in this tab. Reset the workspace or use a smaller CSV.", "error");
      }
    });

    resetButton.addEventListener("click", () => {
      uploadForm.reset();
      selectedFile.textContent = "No file selected";
      stagedImport = null;
      importButton.disabled = true;
      results.hidden = true;
      stats.replaceChildren();
      columnsContainer.replaceChildren();
      errorsList.replaceChildren();
      errorsContainer.hidden = true;
      clearTable();
      try {
        sessionStorage.removeItem(storageKey);
        setImportStatus("Import workspace reset. Choose a CSV file to begin.", "info");
      } catch (error) {
        console.error("Could not reset the tab's imported CSV state.", error);
        setImportStatus("The import was cleared from the page, but browser tab storage could not be reset.", "error");
      }
    });

    showStoredImport();
  }

  const searchInput = document.getElementById("dashboard-search");
  const searchableItems = document.querySelectorAll("[data-search-item]");
  const emptyMessage = document.getElementById("search-empty");

  if (searchInput && emptyMessage) {
    searchInput.addEventListener("input", () => {
      const query = searchInput.value.trim().toLocaleLowerCase();
      let visibleItems = 0;

      searchableItems.forEach((item) => {
        const matches = item.textContent.toLocaleLowerCase().includes(query);
        item.hidden = !matches;
        if (matches) visibleItems += 1;
      });

      emptyMessage.hidden = visibleItems > 0;
    });

    document.addEventListener("keydown", (event) => {
      if (
        event.key === "/" &&
        !event.ctrlKey &&
        !event.metaKey &&
        !["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)
      ) {
        event.preventDefault();
        searchInput.focus();
      }
    });
  }

  const menuToggle = document.getElementById("menu-toggle");
  const sidebar = document.getElementById("sidebar");

  if (menuToggle && sidebar) {
    const navigationLinks = sidebar.querySelectorAll("a.nav-link");

    const setActiveNavigation = (activeLink) => {
      navigationLinks.forEach((link) => {
        const isActive = link === activeLink;
        link.classList.toggle("is-active", isActive);
        if (isActive) {
          link.setAttribute("aria-current", "page");
        } else {
          link.removeAttribute("aria-current");
        }
      });
    };

    menuToggle.addEventListener("click", () => {
      const isOpen = sidebar.classList.toggle("is-open");
      menuToggle.setAttribute("aria-expanded", String(isOpen));
    });

    navigationLinks.forEach((link) => {
      link.addEventListener("click", () => {
        setActiveNavigation(link);
        sidebar.classList.remove("is-open");
        menuToggle.setAttribute("aria-expanded", "false");
      });
    });
  }
})();
