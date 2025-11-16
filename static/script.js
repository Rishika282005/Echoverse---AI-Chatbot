// ---------- EchoVerse Frontend (FINAL FIXED VERSION) ----------
(() => {
  const API = ""; // same-origin

  const $ = (id) => document.getElementById(id);
  const chatbox = $("chatbox");
  const input = $("userInput");

  const escapeHtml = (s) =>
    String(s).replace(/[&<>"']/g, (m) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      "\"": "&quot;",
      "'": "&#39;",
    }[m]));

  const safe = (v, d = "") => (v == null ? d : v);

  function user(msg) {
    chatbox.insertAdjacentHTML(
      "beforeend",
      `<div class="msg user">${escapeHtml(msg)}</div>`
    );
    chatbox.scrollTop = chatbox.scrollHeight;
  }

  function bot(msg) {
    chatbox.insertAdjacentHTML(
      "beforeend",
      `<div class="msg bot">${escapeHtml(msg)}</div>`
    );
    chatbox.scrollTop = chatbox.scrollHeight;
  }

  function showTyping() {
    chatbox.insertAdjacentHTML(
      "beforeend",
      `<div id="typing" class="msg bot">typing…</div>`
    );
    chatbox.scrollTop = chatbox.scrollHeight;
  }

  function hideTyping() {
    const t = $("typing");
    if (t) t.remove();
  }

  // ---- Theme toggle ----
  (function initTheme() {
    const saved = localStorage.getItem("echoverse_theme") || "dark";
    if (saved === "light") document.body.classList.add("light");

    const btn = $("themeToggle");
    if (btn) {
      btn.onclick = () => {
        document.body.classList.toggle("light");
        localStorage.setItem(
          "echoverse_theme",
          document.body.classList.contains("light") ? "light" : "dark"
        );
        btn.textContent = document.body.classList.contains("light") ? "☀" : "🌙";
      };
      btn.textContent = document.body.classList.contains("light") ? "☀" : "🌙";
    }
  })();

  // ---- Sidebar ----
  $("openSidebarBtn")?.addEventListener("click", () => {
    $("sidebar").classList.add("show");
    $("overlay").classList.add("show");
  });

  $("closeSidebar")?.addEventListener("click", closeSidebar);
  $("overlay")?.addEventListener("click", closeSidebar);

  function closeSidebar() {
    $("sidebar").classList.remove("show");
    $("overlay").classList.remove("show");
  }

  // ---- Sending message ----
  $("sendBtn")?.addEventListener("click", sendMsg);

  input?.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMsg();
    }
  });

  async function sendMsg() {
    const text = (input?.value || "").trim();
    if (!text) return;

    user(text);
    input.value = "";
    showTyping();

    try {
      const res = await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          language: $("langSelect")?.value || "auto",
          mode: $("modeSelect")?.value || "default",
          voice_enabled: $("serverVoiceCheckbox")?.checked || false,
        }),
      });

      const data = await res.json();
      hideTyping();

      if (data.error) {
        bot("⚠ " + data.error);
        return;
      }

      bot(safe(data.reply, ""));

      if (data.audio_url && $("autoSpeakCheckbox")?.checked) {
        try {
          const audio = new Audio(data.audio_url);
          await audio.play().catch(() => {});
        } catch {}
      }
    } catch {
      hideTyping();
      bot("⚠ Network error.");
    }
  }

  // ---- New Chat ----
  $("newChat")?.addEventListener("click", async () => {
    showTyping();
    try {
      await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: "clear" }),
      });

      hideTyping();

      chatbox.innerHTML = `<div class="msg bot">✨ New chat started!</div>`;
      if ($("fileInput")) $("fileInput").value = "";
    } catch {
      hideTyping();
      bot("⚠ Couldn't start new chat.");
    }
  });

  // ---- Export ----
  $("exportData")?.addEventListener("click", async () => {
    try {
      const r = await fetch(`${API}/export-data`);
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "chat_history.json";
      document.body.appendChild(a);
      a.click();
      URL.revokeObjectURL(url);
      a.remove();
      bot("✅ Exported chat history.");
    } catch {
      bot("⚠ Export failed.");
    }
  });

  // ---- Clear All ----
  $("deleteData")?.addEventListener("click", async () => {
    if (!confirm("Clear all chats, docs, images, and reminders?")) return;

    showTyping();
    try {
      await fetch(`${API}/delete-data`, { method: "DELETE" });
      hideTyping();

      chatbox.innerHTML = `<div class="msg bot">🗑 Cleared.</div>`;
      if ($("fileInput")) $("fileInput").value = "";
    } catch {
      hideTyping();
      bot("⚠ Clear failed.");
    }
  });

  // ---- Upload ----
  $("uploadBtn")?.addEventListener("click", () =>
    $("fileInput").click()
  );

  $("fileInput")?.addEventListener("change", async () => {
    const f = $("fileInput").files[0];
    if (!f) return;

    const fd = new FormData();
    fd.append("file", f);

    const endpoint = f.type.startsWith("image")
      ? `${API}/upload-image`
      : `${API}/upload-doc`;

    showTyping();

    try {
      const r = await fetch(endpoint, { method: "POST", body: fd });
      const d = await r.json();
      hideTyping();

      if (d.error) bot("⚠ " + d.error);
      if (d.message) bot(d.message);
      if (d.analysis) bot(d.analysis);
      if (d.ocr_text) bot("OCR processed.");
    } catch {
      hideTyping();
      bot("⚠ Upload failed.");
    }
  });

  // ---- Mic ----
  (function initMic() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    const micBtn = $("micBtn");
    if (!SR || !micBtn) return;

    const rec = new SR();
    rec.lang = "en-IN";

    rec.onresult = (e) => {
      input.value = e.results[0][0].transcript;
      sendMsg();
    };

    micBtn.onclick = () => rec.start();
  })();

  // ---- Dashboard ----
  $("dashboardBtn")?.addEventListener("click", async () => {
    $("dashboardModal").classList.remove("hidden");
    const panel = $("remList");
    panel.textContent = "Loading reminders...";

    try {
      const r = await fetch(`${API}/dashboard`);
      const data = await r.json();

      panel.innerHTML =
        Array.isArray(data) && data.length
          ? data.map((x) => `✅ ${escapeHtml(x.task || "")}`).join("<br>")
          : "No reminders yet";
    } catch {
      panel.textContent = "Error loading reminders.";
    }
  });

  $("closeDash")?.addEventListener("click", () =>
    $("dashboardModal").classList.add("hidden")
  );

  $("addRem")?.addEventListener("click", async () => {
    const v = ($("newReminder")?.value || "").trim();
    if (!v) return;

    try {
      const r = await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: `remind me ${v}` }),
      });

      const d = await r.json();
      bot(d.reply || "Reminder added.");
      $("newReminder").value = "";
    } catch {
      bot("⚠ Could not add reminder.");
    }
  });

  // ---- Toast Host ----
  function ensureToastHost() {
    if ($("toastHost")) return $("toastHost");

    const host = document.createElement("div");
    host.id = "toastHost";
    host.style.position = "fixed";
    host.style.right = "18px";
    host.style.bottom = "18px";
    host.style.display = "grid";
    host.style.gap = "10px";
    host.style.zIndex = "1000";
    document.body.appendChild(host);

    return host;
  }

  function showReminderToast(rem) {
    const host = ensureToastHost();

    const card = document.createElement("div");
    card.style.background = "linear-gradient(135deg,#151826,#0e1222)";
    card.style.border = "1px solid #2a2f45";
    card.style.color = "#e7e9ee";
    card.style.borderRadius = "14px";
    card.style.padding = "12px 14px";
    card.style.minWidth = "260px";
    card.style.boxShadow = "0 8px 24px rgba(0,0,0,.35)";

    const title = document.createElement("div");
    title.style.fontWeight = "600";
    title.textContent = "⏰ Reminder";

    const txt = document.createElement("div");
    txt.style.opacity = ".95";
    txt.style.margin = "6px 0 10px";
    txt.textContent =
      (rem.task || "").replace(/^remind( me)?/i, "").trim() || rem.task;

    const row = document.createElement("div");
    row.style.display = "flex";
    row.style.gap = "8px";
    row.style.justifyContent = "flex-end";

    const snooze = document.createElement("button");
    snooze.textContent = "Snooze 5 min";
    snooze.className = "icon-btn sm";

    const done = document.createElement("button");
    done.textContent = "Done";
    done.className = "icon-btn sm";

    row.append(snooze, done);
    card.append(title, txt, row);
    host.append(card);

    // Snooze
    snooze.onclick = async () => {
      try {
        await fetch(`${API}/reminders-ack`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ id: rem.id, snooze_minutes: 5 }),
        });
      } catch {}
      card.remove();
    };

    // Done
    done.onclick = async () => {
      try {
        await fetch(`${API}/reminders-ack`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ id: rem.id }),
        });
      } catch {}
      card.remove();
    };
  }

  // ---- Poll reminders ----
  async function pollReminders() {
    try {
      const r = await fetch(`${API}/reminders-due`);
      const due = await r.json();

      if (Array.isArray(due) && due.length) {
        for (const rem of due) {
          showReminderToast(rem);

          // mark delivered
          try {
            await fetch(`${API}/reminders-ack`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ id: rem.id }),
            });
          } catch {}
        }
      }
    } catch { }
    finally {
      setTimeout(pollReminders, 15000);
    }
  }

  pollReminders();
})();
