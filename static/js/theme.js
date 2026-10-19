/* Единая тема всех страниц: auto → light → dark, localStorage */
(function () {
  var KEY = "intelligencerai:theme";
  var ORDER = ["auto", "light", "dark"];
  var LABELS = { auto: "Авто", light: "Светлая", dark: "Тёмная" };
  var ICONS = { auto: "◐", light: "☀", dark: "☾" };
  var mq = window.matchMedia("(prefers-color-scheme: dark)");

  function stored() {
    try {
      return localStorage.getItem(KEY) || "auto";
    } catch (e) {
      return "auto";
    }
  }

  function resolve(theme) {
    return theme === "auto" ? (mq.matches ? "dark" : "light") : theme;
  }

  function apply(theme) {
    var current = ORDER.indexOf(theme) === -1 ? "auto" : theme;
    var resolved = resolve(current);
    document.documentElement.setAttribute("data-theme", resolved);
    document.documentElement.style.colorScheme = resolved;
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute("content", resolved === "dark" ? "#18181b" : "#ffffff");

    var buttons = document.querySelectorAll("[data-theme-toggle]");
    for (var i = 0; i < buttons.length; i++) {
      var btn = buttons[i];
      btn.setAttribute("aria-label", "Тема: " + LABELS[current]);
      btn.setAttribute("title", "Тема: " + LABELS[current]);
      var icon = btn.querySelector("[data-theme-icon]");
      if (icon) icon.textContent = ICONS[current];
      var label = btn.querySelector("[data-theme-label]");
      if (label) label.textContent = LABELS[current];
    }
  }

  function cycle() {
    var next = ORDER[(ORDER.indexOf(stored()) + 1) % ORDER.length];
    try {
      localStorage.setItem(KEY, next);
    } catch (e) {}
    apply(next);
    return next;
  }

  // До отрисовки body — чтобы не было вспышки не той темы
  apply(stored());

  mq.addEventListener("change", function () {
    if (stored() === "auto") apply("auto");
  });

  document.addEventListener("DOMContentLoaded", function () {
    var buttons = document.querySelectorAll("[data-theme-toggle]");
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].addEventListener("click", cycle);
    }
    apply(stored());
  });

  window.IntelliTheme = { get: stored, apply: apply, cycle: cycle };
})();
