/* Общие помощники: тосты, API, загрузка, копирование */
window.Intelli = (function () {
  function esc(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function host() {
    var el = document.getElementById("toast-host");
    if (!el) {
      el = document.createElement("div");
      el.id = "toast-host";
      el.className = "toast toast-end z-50";
      document.body.appendChild(el);
    }
    return el;
  }

  function toast(message, kind) {
    var el = document.createElement("div");
    el.className =
      "alert shadow-lg " +
      (kind === "error" ? "alert-error" : kind === "success" ? "alert-success" : "alert-info");
    el.setAttribute("role", "status");
    el.textContent = message;
    host().appendChild(el);

    el.animate(
      [{ opacity: 0, transform: "translateY(-8px) scale(0.97)" }, { opacity: 1, transform: "none" }],
      { duration: 200, easing: "cubic-bezier(0.23, 1, 0.32, 1)" }
    );

    var timer = setTimeout(close, 3800);
    el.addEventListener("mouseenter", function () {
      clearTimeout(timer);
    });
    el.addEventListener("mouseleave", function () {
      timer = setTimeout(close, 1200);
    });

    function close() {
      clearTimeout(timer);
      var anim = el.animate(
        [{ opacity: 1, transform: "none" }, { opacity: 0, transform: "translateY(6px) scale(0.97)" }],
        { duration: 160, easing: "cubic-bezier(0.23, 1, 0.32, 1)" }
      );
      anim.onfinish = function () {
        el.remove();
      };
    }
  }

  function api(url, options) {
    options = options || {};
    if (options.json && !(options.body instanceof FormData)) {
      options.body = JSON.stringify(options.json);
      options.headers = Object.assign({ "Content-Type": "application/json" }, options.headers);
    }
    return fetch(url, options).then(function (res) {
      return res.json().catch(function () {}).then(function (data) {
        if (!res.ok) {
          var err = new Error((data && (data.error || data.message)) || "Ошибка запроса");
          err.status = res.status;
          err.errors = (data && data.errors) || null;
          throw err;
        }
        return data;
      });
    });
  }

  function setLoading(button, on) {
    if (!button) return;
    if (on) {
      button.dataset.label = button.textContent;
      button.classList.add("loading");
      button.classList.add("btn-disabled");
      button.disabled = true;
      button.textContent = "";
    } else {
      button.classList.remove("loading");
      button.classList.remove("btn-disabled");
      button.disabled = false;
      if (button.dataset.label) button.textContent = button.dataset.label;
    }
  }

  function copy(text, message) {
    var done = function () {
      toast(message || "Скопировано", "success");
    };
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(done, function () {
        fallback(text, done);
      });
    } else {
      fallback(text, done);
    }
  }

  function fallback(text, done) {
    var area = document.createElement("textarea");
    area.value = text;
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    try {
      document.execCommand("copy");
      done();
    } catch (e) {
      toast("Не удалось скопировать", "error");
    }
    area.remove();
  }

  function formatSize(bytes) {
    if (!bytes && bytes !== 0) return "";
    var units = ["Б", "КБ", "МБ", "ГБ"];
    var i = 0;
    var value = bytes;
    while (value >= 1024 && i < units.length - 1) {
      value /= 1024;
      i++;
    }
    return (i === 0 ? value : value.toFixed(1)) + " " + units[i];
  }

  function initials(first, last) {
    return ((first || "").charAt(0) + (last || "").charAt(0)).toUpperCase() || "?";
  }

  return {
    esc: esc,
    toast: toast,
    api: api,
    setLoading: setLoading,
    copy: copy,
    formatSize: formatSize,
    initials: initials,
  };
})();
