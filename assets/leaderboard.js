(function () {
  const LEADERBOARD_TABLE = String.raw`
| Entry Name                       | MotifBench Score | Date (month/year) | Contact Name                  | Additional Information                 | Contact Email                             | Estimated compute time (per scaffold) | Metadata                            |                         Project Link                         |
| -------------------------------- | ---------------- | ----------------- | ----------------------------- | -------------------------------------- | ----------------------------------------- | ------------------------------------- | ----------------------------------- | :----------------------------------------------------------: |
| **RFD4-Proteina (unindexed)** | **60.36 ± 0.87 (medium-thinking)**<br>**60.21 ± 0.57 (high-thinking)**<br>**58.64 ± 1.21 (low-thinking)** | 11/2026 | Lorenz Kleiter, Lukas Gerstung | https://github.com/Jetzu/RFD4-MotifBench | lorenz.kleiter@tum.de, lukas.gerstung@tum.de | ~8 s (NVIDIA RTX A5000 / RTX 4090) (medium-thinking)<br>~7.6 s (NVIDIA L40S) (high-thinking)<br>~3.9 s (NVIDIA L40S) (low-thinking) | [Zenodo archive](https://zenodo.org/records/23942848/files/MBR4_RFD4_unindexed_thinking_medium_MotifBench_submission.zip?download=1) (medium-thinking)<br>[Zenodo archive](https://zenodo.org/records/23942848/files/MBR4_RFD4_unindexed_thinking_high_MotifBench_submission.zip?download=1) (high-thinking)<br>[Zenodo archive](https://zenodo.org/records/23942848/files/MBR4_RFD4_unindexed_thinking_low_MotifBench_submission.zip?download=1) (low-thinking) | [Paper](https://github.com/RosettaCommons/RFD4-Proteina/blob/main/website/assets/paper/RFD4-Proteina.pdf) \| [Codebase](https://github.com/RosettaCommons/RFD4-Proteina) |
| **RFD4-Proteina (indexed)** | **55.28 ± 0.16 (high-thinking)**<br>**55.06 ± 1.35 (medium-thinking)**<br>**53.95 ± 1.00 (low-thinking)** | 11/2026 | Lorenz Kleiter, Lukas Gerstung | https://github.com/Jetzu/RFD4-MotifBench | lorenz.kleiter@tum.de, lukas.gerstung@tum.de | ~7.5 s (NVIDIA L40S) (high-thinking)<br>~8 s (NVIDIA RTX A5000 / RTX 4090) (medium-thinking)<br>~4.0 s (NVIDIA L40S) (low-thinking) | [Zenodo archive](https://zenodo.org/records/23942848/files/MBR4_RFD4_indexed_thinking_high_MotifBench_submission.zip?download=1) (high-thinking)<br>[Zenodo archive](https://zenodo.org/records/23942848/files/MBR4_RFD4_indexed_thinking_medium_MotifBench_submission.zip?download=1) (medium-thinking)<br>[Zenodo archive](https://zenodo.org/records/23942848/files/MBR4_RFD4_indexed_thinking_low_MotifBench_submission.zip?download=1) (low-thinking) | [Paper](https://github.com/RosettaCommons/RFD4-Proteina/blob/main/website/assets/paper/RFD4-Proteina.pdf) \| [Codebase](https://github.com/RosettaCommons/RFD4-Proteina) |
| **RFdiffusion3 (indexed)** | 43.52 ($\pm$ 1.35) | 08/2026 | Lorenz Kleiter, Brian Trippe | [readme](assets/extra_info/RFdiffusion3.md) | lorenz.kleiter@tum.de, btrippe@stanford.edu | ~12.2s (Various GPU types) | https://zenodo.org/records/22112445 | [Paper](https://www.biorxiv.org/content/10.1101/2025.09.18.676967v2) \| [Codebase](https://github.com/RosettaCommons/foundry) |
| **Protpardelle-1c (cc91-large)** | 33.81            | 04/2026           | Tianyu Lu, Jessica Jiaxin Lin | NA                                     | tianyulu@stanford.edu, linjj@stanford.edu | ~3s (NVIDIA A100)                     | https://zenodo.org/records/19828416 | [Paper](https://www.biorxiv.org/content/10.1101/2025.08.18.670959v2) \| [Codebase](https://github.com/ProteinDesignLab/protpardelle-1c/tree/main) |
| **RFdiffusion3 (unindexed)** | 31.84 ($\pm$ 0.56) | 08/2026 | Lorenz Kleiter | [GitHub repo](https://github.com/lorenzkleiter/RFD3-Unindexed-MotifBench) | lorenz.kleiter@tum.de | ~3s (NVIDIA A100) | https://zenodo.org/records/22648416 | [Paper](https://www.biorxiv.org/content/10.1101/2025.09.18.676967v2) \| [Codebase](https://github.com/RosettaCommons/foundry) |
| **Genie3**                       | 31.14 ($\pm$ 0.70) | 07/2026           | Genie3 team                   | [readme](assets/extra_info/Genie3.md) | yl4599@columbia.edu                       | ~10s (NVIDIA A100)                    | https://zenodo.org/records/21131140 | [Paper](https://www.biorxiv.org/content/10.64898/2026.05.01.722168v1) \| [Codebase](https://github.com/aqlaboratory/genie3) |
| **La-Proteina**                  | 29.75 ($\pm$ 0.51) | 07/2026           | Genie3 team                   | [readme](assets/extra_info/La-Proteina.md) | yl4599@columbia.edu                       | ~7s (NVIDIA A100)                     | https://zenodo.org/records/21272894 | [Paper](https://openreview.net/pdf?id=RDerF20JYT) \| [Codebase](https://github.com/NVIDIA-BioNeMo/la-proteina/) |
| **ODesign-rigid**                | 29.39            | 11/2025           | ODesign team                  | NA                                     | odesign@lglab.ac.cn                       | ~5.2s (NVIDIA GeForce 4090D)          | https://zenodo.org/records/19201706 | [Paper](https://arxiv.org/abs/2510.22304) \| [Codebase](https://github.com/The-Institute-for-AI-Molecular-Design/ODesign) |
| **Protpardelle-1c**              | 27.83            | 07/2025           | Tianyu Lu                     | NA                                     | tianyulu@stanford.edu                     | ~3s (NVIDIA A100)                     | https://zenodo.org/records/15612060 | [Paper](https://www.biorxiv.org/content/10.1101/2025.08.18.670959v2) \| [Codebase](https://github.com/ProteinDesignLab/protpardelle-1c/tree/main) |
| **Proteina**                     | 25.46            | 11/2025           | ODesign team, Zhuoqi Zheng    | NA                                     | odesign@lglab.ac.cn, h2knight@sjtu.edu.cn | ~15s (NVIDIA A6000)                   | https://zenodo.org/records/19204034 | [Paper](https://arxiv.org/abs/2503.00710) \| [Codebase](https://github.com/NVIDIA-Digital-Bio/proteina/) |
| **ODesign-flex**                 | 25.01            | 11/2025           | ODesign team                  | NA                                     | odesign@lglab.ac.cn                       | ~5.2s (NVIDIA GeForce 4090D)          | https://zenodo.org/records/19201872 | [Paper](https://arxiv.org/abs/2510.22304) \| [Codebase](https://github.com/The-Institute-for-AI-Molecular-Design/ODesign) |
| **RFdiffusion**                  | 21.95            | 02/2025           | Brian Trippe                  | NA                                     | btrippe@stanford.edu                      | ~ 37.2s (Various GPU types)           | https://zenodo.org/records/16718874 | [Paper](https://www.nature.com/articles/s41586-023-06415-8) \| [Codebase](https://github.com/RosettaCommons/RFdiffusion) |
| **RFdiffusionAA**                | 20.99            | 11/2025           | ODesign team                  | NA                                     | odesign@lglab.ac.cn                       | ~ 6.5min (NVIDIA GeForce 4090D)       | https://zenodo.org/records/19202010 | [Paper](https://www.science.org/doi/10.1126/science.adl2528) \| [Codebase](https://github.com/baker-laboratory/rf_diffusion_all_atom) |
| **Genie2**                       | 20.83            | 07/2025           | Yeqing Lin, Brian Trippe      | NA                                     | yl4599@columbia.edu; btrippe@stanford.edu | ~48s (NVIDIA A6000)                   | https://zenodo.org/records/20394938 | [Paper](https://arxiv.org/abs/2405.15489) \| [Codebase](https://github.com/aqlaboratory/genie2) |
| **FrameFlow**                    | 18.71 ($\pm$ 0.42 ) | 07/2026           | Genie3 team                   | [readme](assets/extra_info/FrameFlow.md) | yl4599@columbia.edu                       | 2~3s (NVIDIA A100)                    | https://zenodo.org/records/21273108 | [Paper](https://openreview.net/forum?id=fa1ne8xDGn) \| [Codebase](https://github.com/microsoft/protein-frame-flow) |
| **GPDL**                         | 15.94            | 08/2025           | Bo Zhang                      | NA                                     | b-zhang23@mails.tsinghua.edu.cn           | ~30min (NVIDIA GeForce 4090)          | https://zenodo.org/records/16719965 | [Paper](https://www.sciencedirect.com/science/article/pii/S0141813025089986?via%3Dihub) \| [Codebase](https://github.com/sirius777coder/GPDL) |
| **ESM3**                         | 11.38            | 05/2025           | Wei Deng                      | NA                                     | yaowei@stanford.edu                       | ~14.4s (Various GPU types)            | https://zenodo.org/records/16545975 | [Paper](https://www.science.org/doi/10.1126/science.ads0018) \| [Codebase](https://github.com/evolutionaryscale/esm) |
`.trim();

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
      .replace(/\$\\pm\$/g, "+/-")
      .replace(/\*\*(.*?)\*\*/g, "$1")
      .replace(/\[(.*?)\]\((.*?)\)/g, "$1")
      .trim();
  }

  function markdownLinkToHtml(value) {
    const normalized = value
      .replaceAll("\\|", "|")
      .replace(/\$\\pm\$/g, "+/-")
      .replace(/\*\*(.*?)\*\*/g, "$1");
    let html = "";
    let cursor = 0;
    const linkPattern = /\[([^\]]+)\]\(([^)]+)\)/g;
    for (const match of normalized.matchAll(linkPattern)) {
      html += textWithAutoLinks(normalized.slice(cursor, match.index));
      html += `<a href="${escapeHtml(normalizeLinkUrl(match[2]))}" target="_blank" rel="noopener noreferrer">${escapeHtml(match[1])}</a>`;
      cursor = match.index + match[0].length;
    }
    html += textWithAutoLinks(normalized.slice(cursor));
    return html.trim();
  }

  function normalizeLinkUrl(url) {
    if (url.startsWith("assets/extra_info/")) {
      return `https://github.com/blt2114/MotifBench/blob/main/${url}`;
    }
    return url;
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

  function parseMarkdownTable(tableLines) {
    const headers = splitMarkdownRow(tableLines[0]);
    return tableLines.slice(2).map((line) => {
      const cells = splitMarkdownRow(line);
      const row = {};
      headers.forEach((header, index) => {
        const raw = cells[index] || "";
        const parts = raw.split(/<br\s*\/?>/i).map((part) => {
          const text = stripMarkdown(part);
          return { text, html: markdownLinkToHtml(part), number: parseScoreMean(text) };
        });
        row[header] = {
          raw,
          text: parts.map((part) => part.text).join("\n"),
          html: parts.map((part) => part.html).join("<br>"),
          number: parts[0].number,
          parts,
        };
      });
      const count = row["MotifBench Score"]?.parts.length || 1;
      for (const header of headers) {
        const expectedCounts = ["Estimated compute time (per scaffold)", "Metadata"].includes(header) ?
          [count] : [1, count];
        if (!expectedCounts.includes(row[header].parts.length)) {
          throw new Error(`Mismatched sub-rows in ${row["Entry Name"]?.text}: ${header}`);
        }
      }
      return row;
    });
  }

  function parseScoreMean(value) {
    const match = String(value).match(/-?\d+(?:\.\d+)?/);
    return match ? Number.parseFloat(match[0]) : null;
  }

  function renderSummary(rows) {
    const scores = scoreEntries(rows).map((entry) => entry.score);
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

  function scoreEntries(rows) {
    return rows.flatMap((row) => (row["MotifBench Score"]?.parts || []).map((part) => {
      const label = part.text.match(/\([^)]+-thinking\)/)?.[0];
      const name = row["Entry Name"]?.text || "Unnamed";
      return { name: label ? `${name} ${label}` : name, score: part.number };
    })).filter((entry) => Number.isFinite(entry.score)).sort((a, b) => b.score - a.score);
  }

  function renderChart(rows) {
    const chart = document.getElementById("score-chart");
    const entries = scoreEntries(rows);
    const maxScore = entries[0]?.score || 1;

    chart.innerHTML = entries
      .map(({ name, score }, index) => {
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
          .map((row) => {
            const count = row["MotifBench Score"]?.parts.length || 1;
            return Array.from({ length: count }, (_, index) => `
              <tr>
                ${headers.map((header) => {
                  const parts = row[header].parts;
                  if (index > 0 && parts.length === 1) return "";
                  const rowspan = parts.length === 1 && count > 1 ? ` rowspan="${count}"` : "";
                  const className = header === "Entry Name" ? ' class="entry-name"' :
                    header === "MotifBench Score" ? ' class="entry-score"' : "";
                  return `<td${className}${rowspan}>${(parts[index] || parts[0]).html}</td>`;
                }).join("")}
              </tr>
            `).join("");
          })
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
      const rows = parseMarkdownTable(LEADERBOARD_TABLE.split(/\r?\n/));
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
    LEADERBOARD_TABLE,
    markdownLinkToHtml,
    normalizeLinkUrl,
    parseMarkdownTable,
    parseScoreMean,
    splitMarkdownRow,
    stripMarkdown,
    textWithAutoLinks,
  };

  document.addEventListener("DOMContentLoaded", loadLeaderboard);
})();
