(function () {
  "use strict";

  // ---------- Menu latéral (mobile)
  const toggle = document.getElementById("sidebarToggle");
  const sidebar = document.getElementById("sidebar");
  if (toggle && sidebar) {
    toggle.addEventListener("click", () => sidebar.classList.toggle("open"));
    document.addEventListener("click", (e) => {
      if (sidebar.classList.contains("open") && !sidebar.contains(e.target) && !toggle.contains(e.target)) {
        sidebar.classList.remove("open");
      }
    });
  }

  // ---------- Confirmation avant action
  document.querySelectorAll("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (e) => {
      if (!window.confirm(form.dataset.confirm)) e.preventDefault();
    });
  });

  // ---------- Impression
  document.querySelectorAll("[data-print]").forEach((btn) => {
    btn.addEventListener("click", () => window.print());
  });

  // ---------- Autocomplétion client
  // <input data-client-search data-fill='{"champ_id": "cle_client", ...}' data-client-id="client_id">
  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  document.querySelectorAll("[data-client-search]").forEach((input) => {
    const wrapper = input.closest(".autocomplete");
    const list = document.createElement("div");
    list.className = "autocomplete-list d-none";
    wrapper.appendChild(list);
    const fillMap = JSON.parse(input.dataset.fill || "{}");
    const idField = document.getElementById(input.dataset.clientId);
    const badge = document.getElementById(input.dataset.badge);
    let timer = null;
    let results = [];
    let active = -1;

    function hide() { list.classList.add("d-none"); active = -1; }

    function choose(client) {
      Object.entries(fillMap).forEach(([fieldId, key]) => {
        const el = document.getElementById(fieldId);
        if (el && client[key] !== undefined) {
          el.value = client[key];
          el.dispatchEvent(new Event("change", { bubbles: true }));
        }
      });
      if (idField) idField.value = client.id;
      if (badge) {
        badge.innerHTML = '<i class="bi bi-person-check"></i> Client existant : ' + escapeHtml(client.full_name) +
          ' <button type="button" class="btn btn-link btn-sm p-0 ms-2" data-unlink>Délier</button>';
        badge.classList.remove("d-none");
        badge.querySelector("[data-unlink]").addEventListener("click", () => {
          if (idField) idField.value = "";
          badge.classList.add("d-none");
        });
      }
      input.value = "";
      hide();
    }

    function render() {
      if (!results.length) {
        list.innerHTML = '<div class="p-2 small text-muted">Aucun client trouvé — saisissez ses informations ci-dessous, la fiche sera créée automatiquement.</div>';
      } else {
        list.innerHTML = results.map((c, i) =>
          `<button type="button" data-i="${i}" class="${i === active ? "active" : ""}">
             <strong>${escapeHtml(c.full_name)}</strong><br>
             <small>CIN : ${escapeHtml(c.cin || "—")} · Passeport : ${escapeHtml(c.passport_no || "—")} · Tél : ${escapeHtml(c.phone || "—")}</small>
           </button>`).join("");
        list.querySelectorAll("button").forEach((b) =>
          b.addEventListener("mousedown", (e) => { e.preventDefault(); choose(results[+b.dataset.i]); }));
      }
      list.classList.remove("d-none");
    }

    input.addEventListener("input", () => {
      clearTimeout(timer);
      const q = input.value.trim();
      if (q.length < 2) { hide(); return; }
      timer = setTimeout(async () => {
        try {
          const resp = await fetch(input.dataset.url + "?q=" + encodeURIComponent(q));
          results = await resp.json();
          active = -1;
          render();
        } catch (err) { hide(); }
      }, 220);
    });
    input.addEventListener("keydown", (e) => {
      if (list.classList.contains("d-none") || !results.length) return;
      if (e.key === "ArrowDown") { active = Math.min(active + 1, results.length - 1); render(); e.preventDefault(); }
      else if (e.key === "ArrowUp") { active = Math.max(active - 1, 0); render(); e.preventDefault(); }
      else if (e.key === "Enter" && active >= 0) { choose(results[active]); e.preventDefault(); }
      else if (e.key === "Escape") hide();
    });
    input.addEventListener("blur", () => setTimeout(hide, 150));
  });

  // ---------- Formulaire contrat : véhicule, jours, montants
  const contractForm = document.getElementById("contractForm");
  if (contractForm) {
    const $ = (id) => document.getElementById(id);
    const num = (id) => parseFloat(($(id).value || "0").replace(",", ".")) || 0;
    const money = (v) => v.toLocaleString("fr-FR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    let amountTouched = $("amount").value !== "" && num("amount") !== num("daily_rate") * num("days");
    let daysTouched = false;

    function computeDays() {
      const s = new Date($("start_at").value);
      const e = new Date($("end_at").value);
      if (isNaN(s) || isNaN(e) || e <= s) return null;
      return Math.max(1, Math.ceil((e - s) / 86400000));
    }
    function refresh() {
      if (!daysTouched) {
        const d = computeDays();
        if (d) $("days").value = d;
      }
      if (!amountTouched) {
        $("amount").value = (num("daily_rate") * num("days")).toFixed(2);
      }
      $("remainingDisplay").textContent = money(num("amount") - num("advance"));
      const warn = $("datesWarning");
      const s = new Date($("start_at").value), e = new Date($("end_at").value);
      warn.classList.toggle("d-none", !(e <= s));
    }

    $("vehicle_id").addEventListener("change", (e) => {
      const opt = e.target.selectedOptions[0];
      if (opt && opt.dataset.rate) {
        $("daily_rate").value = opt.dataset.rate;
        if (!$("km_start").value) $("km_start").value = opt.dataset.km || "";
        amountTouched = false;
      }
      refresh();
    });
    ["start_at", "end_at", "daily_rate", "advance"].forEach((id) => $(id).addEventListener("input", refresh));
    $("days").addEventListener("input", () => { daysTouched = true; refresh(); });
    $("amount").addEventListener("input", () => { amountTouched = true; refresh(); });
    $("recalc").addEventListener("click", () => { daysTouched = false; amountTouched = false; refresh(); });
    refresh();
  }

  // ---------- Formulaire engagement : modèle et véhicule
  const engagementForm = document.getElementById("engagementForm");
  if (engagementForm) {
    const tplSelect = document.getElementById("template_id");
    const templates = JSON.parse(document.getElementById("templatesData").textContent);
    document.getElementById("applyTemplate").addEventListener("click", () => {
      const tpl = templates[tplSelect.value];
      if (!tpl) return;
      const body = document.getElementById("body_source");
      if (body.value.trim() && !window.confirm("Remplacer le texte actuel par celui du modèle ?")) return;
      document.getElementById("title").value = tpl.title;
      body.value = tpl.body;
    });
    const vSelect = document.getElementById("vehicle_id");
    vSelect.addEventListener("change", () => {
      const opt = vSelect.selectedOptions[0];
      document.getElementById("vehicle_label").value = opt.dataset.label || "";
      document.getElementById("vehicle_plate").value = opt.dataset.plate || "";
    });
  }

  // ---------- Insertion d'une variable {{ ... }} dans un texte de modèle
  document.querySelectorAll("[data-insert]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const body = document.getElementById(btn.dataset.target);
      const text = "{{ " + btn.dataset.insert + " }}";
      const start = body.selectionStart ?? body.value.length;
      body.value = body.value.slice(0, start) + text + body.value.slice(body.selectionEnd ?? start);
      body.focus();
      body.selectionStart = body.selectionEnd = start + text.length;
    });
  });
})();
