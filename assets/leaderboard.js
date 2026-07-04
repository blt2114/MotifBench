(function () {
  const README_URL = "../readme.md";
  const TABLE_HEADERS = ["Entry Name", "MotifBench Score"];

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function stripMarkdown(value) {
    return value
      .replaceAll("\\|", "|")
      .replace(/\*\*(.*?)\*\*/g, "$1")
      .replace(/\[(.*?)\]\((.*?)\)/g, "$1")
      .trim();
  }

  function markdownLinkToHtml(value) {
    const normalized = value.replaceAll("\\|", "|").replace(/\*\*(.*?)\*\*/g, "$1");
    let html = "";
    let cursor = 0;
    const linkPattern = /\[([^\]]+)\]\(([^)]+)\)/g;
    for (const match of normalized.matchAll(linkPattern)) {
      html += textWithAutoLinks(normalized.slice(cursor, match.index));
      html += `<a href="${escapeHtml(match[2])}" target="_blank" rel="noopener noreferrer">${escapeHtml(match[1])}</a>`;
      cursor = match.index + match[0].length;
    }
    html += textWithAutoLinks(normalized.slice(cursor));
    return html.trim();
  }

  function textWithAutoLinks(value) {
    const urlPattern = /https?:\/\/[^\s|]+/g;
    let html = "";
    let cursor = 0;
    for (const match of value.matchAll(urlPattern)) {
      html += escapeHtml(value.slice(cursor, match.index));
      html += `<a href="${escapeHtml(match[0])}" target="_blank" rel="noopener noreferrer">${escapeHtml(match[0])}</a>`;
      cursor = match.index + match[0].length;
    }
    html += escapeHtml(value.slice(cursor));
    return html;
  }

  function splitMarkdownRow(line) {
    const placeholder = "\u0000PIPE\u0000";
    return line
      .trim()
      .replaceAll("\\|", placeholder)
      .replace(/^\|/, "")
      .replace(/\|$/, "")
      .split("|")
      .map((cell) => cell.replaceAll(placeholder, "\\|").trim());
  }

  function extractLeaderboardTable(markdown) {
    const lines = markdown.split(/\r?\n/);
    const start = lines.findIndex((line) => /^#\s+Leaderboard\s*$/.test(line.trim()));
    const searchFrom = start === -1 ? 0 : start;
    const tableStart = lines.findIndex((line, index) => {
      if (index < searchFrom) return false;
      if (!line.trim().startsWith("|")) return false;
      return TABLE_HEADERS.every((header) => line.includes(header));
    });

    if (tableStart === -1) {
      throw new Error("Could not find the leaderboard table in readme.md.");
    }

    const tableLines = [];
    for (let index = tableStart; index < lines.length; index += 1) {
      const line = lines[index].trim();
      if (!line.startsWith("|")) break;
      tableLines.push(line);
    }

    if (tableLines.length < 3) {
      throw new Error("The leaderboard table is missing rows.");
    }
    return tableLines;
  }

  function parseMarkdownTable(tableLines) {
    const headers = splitMarkdownRow(tableLines[0]);
    return tableLines.slice(2).map((line) => {
      const cells = splitMarkdownRow(line);
      const row = {};
      headers.forEach((header, index) => {
        const raw = cells[index] || "";
        const text = stripMarkdown(raw);
        const number = Number.parseFloat(text);
        row[header] = {
          raw,
          text,
          html: markdownLinkToHtml(raw),
          number: Number.isFinite(number) ? number : null,
        };
      });
      return row;
    });
  }

  function renderSummary(rows) {
    const scores = rows.map((row) => row["MotifBench Score"]?.number).filter(Number.isFinite);
    document.getElementById("entry-count").textContent = rows.length;
    document.getElementById("top-score").textContent = scores.length ? Math.max(...scores).toFixed(2) : "--";
    document.getElementById("latest-date").textContent = latestDate(rows);
  }

  function latestDate(rows) {
    const dates = rows
      .map((row) => row["Date (month/year)"]?.text)
      .map((value) => {
        const match = /^(\d{2})\/(\d{4})$/.exec(value || "");
        return match ? { label: value, sort: Number(match[2]) * 100 + Number(match[1]) } : null;
      })
      .filter(Boolean)
      .sort((a, b) => b.sort - a.sort);
    return dates[0]?.label || "--";
  }

  function renderChart(rows) {
    const chart = document.getElementById("score-chart");
    const scores = rows.map((row) => row["MotifBench Score"]?.number).filter(Number.isFinite);
    const maxScore = scores.length ? Math.max(...scores) : 1;

    chart.innerHTML = rows
      .map((row, index) => {
        const name = row["Entry Name"]?.text || "Unnamed";
        const score = row["MotifBench Score"]?.number || 0;
        const percent = Math.max(3, (score / maxScore) * 100);
        return `
          <article class="score-row">
            <div class="rank">${index + 1}</div>
            <div class="score-main">
              <div class="score-meta">
                <strong>${escapeHtml(name)}</strong>
                <span>${score.toFixed(2)}</span>
              </div>
              <div class="trace" aria-label="${escapeHtml(name)} score ${score.toFixed(2)}">
                <span style="width: ${percent}%"></span>
              </div>
            </div>
          </article>
        `;
      })
      .join("");
  }

  function renderTable(rows) {
    const table = document.getElementById("leaderboard-table");
    if (!rows.length) {
      table.innerHTML = "";
      return;
    }

    const headers = Object.keys(rows[0]);
    table.innerHTML = `
      <thead>
        <tr>${headers.map((header) => `<th scope="col">${escapeHtml(header)}</th>`).join("")}</tr>
      </thead>
      <tbody>
        ${rows
          .map((row) => `
            <tr>
              ${headers.map((header) => `<td>${row[header].html}</td>`).join("")}
            </tr>
          `)
          .join("")}
      </tbody>
    `;
  }

  function setStatus(message, type) {
    const status = document.getElementById("status");
    status.textContent = message;
    status.className = type ? `status ${type}` : "status";
  }

  async function loadLeaderboard() {
    try {
      const response = await fetch(`${README_URL}?cache=${Date.now()}`);
      if (!response.ok) throw new Error(`Could not fetch readme.md: ${response.status}`);
      const markdown = await response.text();
      const rows = parseMarkdownTable(extractLeaderboardTable(markdown));
      renderSummary(rows);
      renderChart(rows);
      renderTable(rows);
      setStatus("", "");
    } catch (error) {
      setStatus(error.message, "error");
      document.getElementById("score-chart").innerHTML = "";
      document.getElementById("leaderboard-table").innerHTML = "";
    }
  }

  window.MotifBenchLeaderboard = {
    extractLeaderboardTable,
    markdownLinkToHtml,
    parseMarkdownTable,
    splitMarkdownRow,
    stripMarkdown,
    textWithAutoLinks,
  };

  document.addEventListener("DOMContentLoaded", loadLeaderboard);
})();
