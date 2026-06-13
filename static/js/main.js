/* ============================================================
   Relocation & Housing Concierge — JS v2
   ============================================================ */

// ---- NAVBAR: scroll glass effect + active link ----
const navbar = document.getElementById("navbar");
window.addEventListener("scroll", () => {
  navbar?.classList.toggle("scrolled", window.scrollY > 40);
}, { passive: true });

document.addEventListener("DOMContentLoaded", () => {
  // Active nav link
  const path = window.location.pathname;
  document.querySelectorAll(".navbar-nav .nav-link").forEach(l => {
    if (l.getAttribute("href") === path) l.classList.add("active");
  });

  // Mobile toggle
  document.querySelector(".navbar-toggle")?.addEventListener("click", () => {
    document.querySelector(".navbar-nav")?.classList.toggle("open");
  });

  initReveal();
  initTabs();
  initChecklistItems();
  initRangeSliders();
  initScoreRings();
});

// ---- SCROLL REVEAL ----
function initReveal() {
  const obs = new IntersectionObserver((entries) => {
    entries.forEach((e, i) => {
      if (e.isIntersecting) {
        setTimeout(() => e.target.classList.add("visible"), i * 60);
        obs.unobserve(e.target);
      }
    });
  }, { threshold: 0.08 });
  document.querySelectorAll(".reveal").forEach(el => obs.observe(el));
}

// ---- SVG SCORE RING ----
function initScoreRings() {
  document.querySelectorAll(".score-fill[data-score]").forEach(path => {
    const score = parseInt(path.dataset.score);
    const r = 46;
    const circ = 2 * Math.PI * r;
    const offset = circ - (score / 100) * circ;
    path.style.strokeDasharray = circ;
    path.style.strokeDashoffset = circ;
    setTimeout(() => { path.style.strokeDashoffset = offset; }, 200);
  });
}

// ---- TABS ----
function initTabs() {
  document.querySelectorAll(".tab-pills").forEach(nav => {
    const btns = nav.querySelectorAll(".tab-pill");
    btns.forEach(btn => {
      btn.addEventListener("click", () => {
        btns.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        const id = btn.dataset.tab;
        const wrap = nav.closest(".tab-container") || document;
        wrap.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));
        wrap.querySelector(`#${id}`)?.classList.add("active");
      });
    });
    btns[0]?.click();
  });
}

// ---- CHECKLIST ----
function initChecklistItems() {
  document.querySelectorAll(".checklist-item").forEach(item => {
    item.addEventListener("click", () => {
      const id = item.dataset.id;
      const wasCompleted = item.classList.contains("completed");
      item.classList.toggle("completed");
      const box = item.querySelector(".check-box");
      if (box) box.textContent = wasCompleted ? "" : "✓";
      if (id) {
        fetch("/api/checklist/update", {
          method:"POST",
          headers:{"Content-Type":"application/json"},
          body:JSON.stringify({ id, status: wasCompleted ? "pending" : "completed" })
        }).catch(console.error);
      }
      updateChecklistProgress();
    });
  });
  updateChecklistProgress();
}

function updateChecklistProgress() {
  const items = document.querySelectorAll(".checklist-item");
  const done  = document.querySelectorAll(".checklist-item.completed").length;
  const pct   = items.length ? Math.round((done / items.length) * 100) : 0;
  const fill  = document.querySelector(".progress-fill");
  const lbl   = document.querySelector(".progress-label");
  if (fill) fill.style.width = pct + "%";
  if (lbl)  lbl.textContent = `${done} of ${items.length} completed (${pct}%)`;
}

// ---- RANGE SLIDERS ----
function initRangeSliders() {
  document.querySelectorAll("input[type='range']").forEach(s => {
    const upd = () => {
      const pct = ((s.value - s.min) / (s.max - s.min)) * 100;
      s.style.setProperty("--fill", pct + "%");
      const el = document.querySelector(s.dataset.display);
      if (el) el.textContent = (s.dataset.prefix || "") + parseInt(s.value).toLocaleString() + (s.dataset.suffix || "");
    };
    upd();
    s.addEventListener("input", upd);
  });
}

// ---- HOUSING FILTER ----
window.filterHousing = async function () {
  const budget      = document.getElementById("budget_filter")?.value || 200000;
  const family_size = document.getElementById("family_filter")?.value || 1;
  const community   = document.getElementById("community_filter")?.value || "any";
  const prop_type   = document.getElementById("type_filter")?.value || "any";
  const container   = document.getElementById("filtered_results");
  if (!container) return;

  container.innerHTML = `<div style="text-align:center;padding:3rem;color:var(--text-light);grid-column:1/-1;">
    <div style="font-size:2rem;margin-bottom:.75rem;animation:spin 1s linear infinite;display:inline-block;">⟳</div>
    <div>Finding best matches…</div></div>`;

  try {
    const r = await fetch(`/api/housing/filter?budget=${budget}&family_size=${family_size}&community=${community}&property_type=${prop_type}`);
    const data = await r.json();
    if (!data.length) { container.innerHTML = `<div style="text-align:center;padding:3rem;color:var(--text-light);grid-column:1/-1;">No properties found — try adjusting filters.</div>`; return; }
    container.innerHTML = data.map(h => propCardHTML(h)).join("");
  } catch(e) { container.innerHTML = `<div style="text-align:center;padding:2rem;color:var(--danger);grid-column:1/-1;">Error loading results.</div>`; }
};

function propCardHTML(h) {
  const icon = h.property_type === "Villa" ? "🏡" : "🏢";
  const amenities = (h.amenities || "").split(",").slice(0,3).join(" · ");
  return `<div class="prop-card">
    <div class="prop-img">
      ${icon}<div class="prop-img-overlay"></div>
      <span class="prop-type-badge">${h.property_type}</span>
      <div class="prop-fav">♡</div>
    </div>
    <div class="prop-body">
      <div class="prop-community">${h.community}</div>
      <div class="prop-subtitle">${h.bedrooms} Bedroom · ${(h.size_sqft||0).toLocaleString()} sqft</div>
      <div class="prop-price">AED ${(h.rent_annual||0).toLocaleString()}<span style="font-size:.65rem;font-weight:500;color:var(--text-light)">/yr</span></div>
      <div class="prop-price-sub">≈ AED ${(h.rent_monthly||0).toLocaleString()} / month</div>
      <div class="prop-meta">
        <div class="prop-meta-item">🎓 School <strong>${h.school_proximity_km}km</strong></div>
        <div class="prop-meta-item">🏥 Hospital <strong>${h.hospital_proximity_km}km</strong></div>
        ${h.metro_access ? '<div class="prop-meta-item">🚇 <strong>Metro</strong></div>' : ''}
      </div>
      <div class="prop-tags">
        <span class="prop-tag">Family ★${h.family_rating}/5</span>
        <span class="prop-tag">Lifestyle ★${h.lifestyle_score}/5</span>
        ${amenities ? `<span class="prop-tag" style="font-size:.65rem;">${amenities.split(' · ')[0]}</span>` : ''}
      </div>
    </div>
    <div class="prop-footer"><a href="/recommendations" class="btn btn-gold btn-sm btn-block">Get AI Match →</a></div>
  </div>`;
}

// ---- QUICK RECOMMEND ----
window.quickRecommend = async function () {
  const budget      = parseInt(document.getElementById("qr_budget")?.value || 100000);
  const family_size = parseInt(document.getElementById("qr_family")?.value || 2);
  const community   = document.getElementById("qr_community")?.value || "any";
  const prop_type   = document.getElementById("qr_type")?.value || "any";
  const name        = document.getElementById("qr_name")?.value || "the client";
  const div         = document.getElementById("qr_results");

  if (div) div.innerHTML = `<div style="text-align:center;padding:3rem;color:var(--text-mid);">🤖 Generating personalized recommendations…</div>`;

  try {
    const r = await fetch("/api/quick-recommend", {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({ budget, family_size, community, property_type:prop_type, name })
    });
    const data = await r.json();
    if (div) {
      const pct = (2 * Math.PI * 46 * data.score / 100);
      const circ = 2 * Math.PI * 46;
      div.innerHTML = `
        <div class="score-block">
          <div class="score-ring">
            <svg class="score-svg" width="110" height="110" viewBox="0 0 110 110">
              <circle class="score-track" cx="55" cy="55" r="46"/>
              <circle class="score-fill" cx="55" cy="55" r="46"
                style="stroke-dasharray:${circ};stroke-dashoffset:${circ - pct};stroke:url(#scoreGrad);fill:none;stroke-width:8;stroke-linecap:round;transition:stroke-dashoffset 1.5s ease"/>
            </svg>
            <div class="score-center"><span class="score-num">${data.score}</span><span class="score-denom">/100</span></div>
          </div>
          <div class="score-info">
            <h3>Relocation Readiness</h3>
            <p>${data.score >= 85 ? "Excellent — well-positioned for Abu Dhabi." : data.score >= 70 ? "Good standing — address key items before your move." : "Preparation gaps found — our team can help."}</p>
          </div>
        </div>
        <div class="ai-box" style="margin-bottom:1.5rem;">
          <div class="ai-label"><span class="ai-label-dot"></span> AI Recommendation</div>
          <div class="ai-text">${marked(data.summary)}</div>
        </div>
        <h4 style="font-weight:800;color:var(--navy);margin-bottom:1rem;font-size:1rem;">Recommended Properties</h4>
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:1.1rem;">
          ${data.housing.map(h => propCardHTML(h)).join("")}
        </div>`;
    }
  } catch(e) { if (div) div.innerHTML = `<div style="text-align:center;padding:2rem;color:var(--danger);">Error. Please try again.</div>`; }
};

// ---- TOUR ITINERARY ----
window.generateItinerary = async function (id) {
  const container = document.getElementById("itinerary_output");
  if (!container) return;
  container.innerHTML = `<div style="text-align:center;padding:3rem;color:var(--text-mid);">🗓️ Building your itinerary…</div>`;
  container.scrollIntoView({ behavior:"smooth", block:"start" });
  try {
    const r = await fetch(`/api/tour/itinerary/${id}`);
    const data = await r.json();
    let html = `<div style="margin-bottom:1.5rem;">
      <h3 style="font-size:1.3rem;font-weight:800;color:var(--navy);letter-spacing:-.3px;">${data.tour.tour_name}</h3>
      <p style="color:var(--text-mid);font-size:.88rem;margin-top:.35rem;">${data.tour.description}</p>
      <span class="badge badge-gold" style="margin-top:.75rem;">AED ${data.tour.estimated_cost_aed?.toLocaleString()} estimated budget</span>
    </div>`;
    for (const [day, items] of Object.entries(data.itinerary)) {
      html += `<div class="itin-day"><div class="itin-day-label">📅 ${day}</div>`;
      items.forEach(item => {
        html += `<div class="itin-item"><div class="itin-time">${item.time}</div><div><div class="itin-name">${item.name}</div><div class="itin-loc">📍 ${item.location} · ${item.tip}</div></div></div>`;
      });
      html += `</div>`;
    }
    container.innerHTML = html;
  } catch(e) { container.innerHTML = `<div style="text-align:center;padding:2rem;color:var(--danger);">Error generating itinerary.</div>`; }
};

// ---- FAQ ----
window.askFAQ = async function () {
  const input  = document.getElementById("faq_input");
  const answer = document.getElementById("faq_answer");
  if (!input || !answer || !input.value.trim()) return;
  answer.classList.remove("visible");
  answer.textContent = "Searching…";
  try {
    const r = await fetch(`/api/faq?q=${encodeURIComponent(input.value.trim())}`);
    const data = await r.json();
    answer.textContent = data.answer;
    answer.classList.add("visible");
  } catch(e) { answer.textContent = "Unable to load. Please try again."; answer.classList.add("visible"); }
};
document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("faq_input")?.addEventListener("keydown", e => { if (e.key === "Enter") window.askFAQ(); });
});

// ---- ATTRACTION FILTER ----
window.filterAttractions = function (cat) {
  document.querySelectorAll(".attr-filter-btn").forEach(b => b.classList.remove("active"));
  event?.target?.classList.add("active");
  document.querySelectorAll(".attr-card[data-category]").forEach(c => {
    c.style.display = (cat === "all" || c.dataset.category === cat) ? "" : "none";
  });
};

// ---- UTILS ----
function marked(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\n\n/g, "<br><br>")
    .replace(/\n/g, "<br>");
}

window.scrollToSection = id => document.getElementById(id)?.scrollIntoView({ behavior:"smooth" });

// Toast notification
function toast(msg) {
  const el = document.createElement("div");
  el.style.cssText = "position:fixed;bottom:24px;right:24px;background:var(--navy);color:#fff;padding:.875rem 1.5rem;border-radius:12px;z-index:9999;font-size:.855rem;font-weight:600;box-shadow:0 8px 32px rgba(0,0,0,.35);border:1px solid rgba(201,168,76,.3);animation:fadeUp .4s ease;";
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => el.style.opacity = "0", 2200);
  setTimeout(() => el.remove(), 2600);
}
