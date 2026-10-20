/* IntelligencerAI — слой анимаций в духе Framer Motion (WAAPI + spring).
   Даёт: пружинные входы, stagger, reveal при скролле, анимацию списков и <dialog>. */
window.Motion = (function () {
  var reduceQuery =
    window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)");
  var EASE_OUT = "cubic-bezier(0.23, 1, 0.32, 1)";

  var SPRINGS = {
    gentle: { stiffness: 380, damping: 32 },
    snappy: { stiffness: 700, damping: 45 },
    bouncy: { stiffness: 520, damping: 26 },
  };

  function reduced() {
    return !!(reduceQuery && reduceQuery.matches);
  }

  function supported() {
    return !!(window.Element && Element.prototype.animate);
  }

  function stop(el) {
    if (!el || !el.getAnimations) return;
    el.getAnimations().forEach(function (anim) {
      try {
        anim.cancel();
      } catch (e) {}
    });
  }

  /* Затухающая пружина: прогресс 0 -> 1 по времени. */
  function spring(config) {
    var opts = config || SPRINGS.snappy;
    var stiffness = opts.stiffness || 700;
    var damping = opts.damping || 45;
    var mass = opts.mass || 1;
    var w0 = Math.sqrt(stiffness / mass);
    var zeta = damping / (2 * Math.sqrt(stiffness * mass));
    var settle = -Math.log(0.001) / (zeta * w0);
    var wd = zeta < 1 ? w0 * Math.sqrt(1 - zeta * zeta) : 0;
    var steps = Math.max(12, Math.min(48, Math.round(settle * 60)));
    var frames = [];

    for (var i = 0; i <= steps; i++) {
      var t = (i / steps) * settle;
      var p;
      if (zeta < 1) {
        p =
          1 -
          Math.exp(-zeta * w0 * t) *
            (Math.cos(wd * t) + ((zeta * w0) / wd) * Math.sin(wd * t));
      } else {
        p = 1 - Math.exp(-w0 * t) * (1 + w0 * t);
      }
      frames.push({ offset: i / steps, time: t, progress: p });
    }

    return { frames: frames, duration: settle * 1000 };
  }

  /* Пружинное появление: opacity + лёгкий сдвиг/масштаб. */
  function enter(el, options) {
    if (!el || !supported()) return null;
    var opts = options || {};
    var y = opts.y == null ? 10 : opts.y;
    var scale = opts.scale == null ? 0.98 : opts.scale;
    var delay = opts.delay || 0;

    stop(el);

    if (reduced()) {
      return el.animate([{ opacity: 0 }, { opacity: 1 }], {
        duration: 160,
        delay: delay,
        easing: EASE_OUT,
        fill: "both",
      });
    }

    var s = spring(opts.spring || SPRINGS.snappy);
    var frames = s.frames.map(function (f) {
      var p = f.progress;
      var frame = {
        offset: f.offset,
        opacity: Math.min(1, f.time / 0.16),
      };
      if (y !== 0 || scale !== 1) {
        var py = (1 - p) * y;
        var ps = 1 - (1 - p) * (1 - scale);
        frame.transform =
          "translate3d(0," + py.toFixed(2) + "px,0) scale(" + ps.toFixed(4) + ")";
      }
      return frame;
    });

    return el.animate(frames, {
      duration: s.duration,
      delay: delay,
      easing: "linear",
      fill: "both",
    });
  }

  /* Последовательное появление прямых дочерних элементов. */
  function stagger(container, options) {
    if (!container) return;
    var opts = options || {};
    var step = opts.step == null ? 70 : opts.step;
    var items = Array.prototype.filter.call(container.children, function (el) {
      return (
        el.nodeType === 1 &&
        !el.hasAttribute("data-motion-ignore") &&
        ["SCRIPT", "STYLE", "TEMPLATE"].indexOf(el.tagName) === -1
      );
    });

    items.forEach(function (el, i) {
      enter(el, {
        y: opts.y == null ? 12 : opts.y,
        scale: opts.scale == null ? 1 : opts.scale,
        delay: i * step,
        spring: opts.spring,
      });
    });
  }

  /* Появление при попадании в вьюпорт. */
  function initReveal() {
    var nodes = document.querySelectorAll("[data-motion-reveal]");
    if (!nodes.length) return;

    if (!("IntersectionObserver" in window)) {
      nodes.forEach(function (el) {
        enter(el, { y: 14, scale: 1 });
      });
      return;
    }

    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          io.unobserve(entry.target);
          enter(entry.target, { y: 14, scale: 1 });
        });
      },
      { rootMargin: "0px 0px -10% 0px", threshold: 0.08 }
    );

    nodes.forEach(function (el) {
      el.style.opacity = "0";
      io.observe(el);
    });
  }

  /* Анимация элементов, добавленных в списки/таблицы. */
  function initLists() {
    var lists = document.querySelectorAll("[data-motion-list]");
    if (!lists.length || !("MutationObserver" in window)) return;

    lists.forEach(function (list) {
      var observer = new MutationObserver(function (mutations) {
        var index = 0;
        mutations.forEach(function (mutation) {
          Array.prototype.forEach.call(mutation.addedNodes, function (node) {
            if (node.nodeType !== 1) return;
            enter(node, { y: 6, scale: 1, delay: index * 30 });
            index++;
          });
        });
      });
      observer.observe(list, { childList: true });
    });
  }

  function dialogBox(dialog) {
    return (
      dialog.querySelector(".modal-box, [data-motion-dialog]") || dialog
    );
  }

  function setupDialog(dialog) {
    if (!dialog || dialog.__motionReady) return;
    dialog.__motionReady = true;

    dialog.addEventListener("cancel", function (event) {
      if (reduced()) return;
      event.preventDefault();
      dialog.close();
    });

    dialog
      .querySelectorAll('form[method="dialog"]')
      .forEach(function (form) {
        form.addEventListener("submit", function (event) {
          event.preventDefault();
          var btn = form.querySelector("button");
          dialog.close(btn ? btn.value : undefined);
        });
      });
  }

  function patchDialog() {
    if (!window.HTMLDialogElement || !supported()) return;
    var proto = HTMLDialogElement.prototype;
    if (proto.__motionPatched) return;
    proto.__motionPatched = true;

    var nativeShow = proto.showModal || proto.show;
    if (nativeShow) {
      proto.showModal = function () {
        nativeShow.apply(this, arguments);
        if (this === dialogBox(this)) stop(this);
        var box = dialogBox(this);
        stop(box);
        stop(this);
        enter(box, { y: 8, scale: 0.96, spring: SPRINGS.snappy });
        if (box !== this) {
          this.animate([{ opacity: 0 }, { opacity: 1 }], {
            duration: 160,
            easing: EASE_OUT,
            fill: "both",
          });
        }
      };
    }

    var nativeClose = proto.close;
    if (!nativeClose) return;

    proto.close = function (value) {
      var self = this;
      if (self.__motionClosing) {
        nativeClose.call(self, value);
        return;
      }
      var box = dialogBox(self);
      if (!box || reduced()) {
        nativeClose.call(self, value);
        return;
      }

      self.__motionClosing = true;
      var done = false;

      function finish() {
        if (done) return;
        done = true;
        self.__motionClosing = false;
        nativeClose.call(self, value);
      }

      var anims = [
        box.animate(
          [
            { opacity: 1, transform: "none" },
            { opacity: 0, transform: "translate3d(0,6px,0) scale(0.98)" },
          ],
          { duration: 140, easing: EASE_OUT, fill: "forwards" }
        ),
      ];

      if (box !== self) {
        anims.push(
          self.animate([{ opacity: 1 }, { opacity: 0 }], {
            duration: 140,
            easing: EASE_OUT,
            fill: "forwards",
          })
        );
      }

      anims.forEach(function (anim) {
        anim.onfinish = finish;
        anim.oncancel = finish;
      });
      setTimeout(finish, 220);
    };
  }

  function init() {
    patchDialog();
    document
      .querySelectorAll("dialog.modal, dialog[data-motion-dialog]")
      .forEach(setupDialog);

    document.querySelectorAll("[data-motion-stagger]").forEach(function (el) {
      stagger(el, {
        step: parseFloat(el.getAttribute("data-motion-stagger")) || 70,
      });
    });

    initReveal();
    initLists();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  return {
    enter: enter,
    stagger: stagger,
    spring: spring,
    reduced: reduced,
    springs: SPRINGS,
  };
})();
