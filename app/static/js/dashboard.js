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
