/**
 * Tandil Tech Week — scripts principales
 * --------------------------------------------------------------------------
 * Sin dependencias. Reemplaza dos comportamientos del sitio original
 * (Next.js + GSAP) con implementaciones nativas equivalentes:
 *
 *   1. RegistrationCountdown  → cuenta regresiva hasta la apertura de
 *                              inscripciones, con estado "abierto".
 *   2. ScrollTrigger          → revelado progresivo de las tarjetas
 *                              (.gsap-card) vía IntersectionObserver.
 *
 * Todo respeta `prefers-reduced-motion`.
 */

(function () {
  "use strict";

  var REDUCE_MOTION = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ======================================================================
     1. Contador de inscripciones
     ====================================================================== */

  var UNITS = [
    { key: "days", label: "Días", pad: false },
    { key: "hours", label: "Horas", pad: true },
    { key: "minutes", label: "Min", pad: true },
    { key: "seconds", label: "Seg", pad: true }
  ];

  /**
   * @param {HTMLElement} root  Contenedor con [data-countdown-to]
   */
  function initCountdown(root) {
    var target = new Date(root.dataset.countdownTo).getTime();

    if (Number.isNaN(target)) return;

    var valueNodes = {};
    root.querySelectorAll(".countdown__value").forEach(function (node) {
      valueNodes[node.dataset.unit] = node;
    });

    function tick() {
      var remaining = Math.max(0, Math.floor((target - Date.now()) / 1000));

      // Cuando llega a cero el contador pasa a estado "abierto".
      if (remaining === 0) {
        root.classList.add("countdown--open");
        window.clearInterval(interval);
        return;
      }

      var parts = {
        days: Math.floor(remaining / 86400),
        hours: Math.floor(remaining / 3600) % 24,
        minutes: Math.floor(remaining / 60) % 60,
        seconds: remaining % 60
      };

      UNITS.forEach(function (unit) {
        var node = valueNodes[unit.key];
        if (!node) return;
        var value = String(parts[unit.key]);
        node.textContent = unit.pad ? value.padStart(2, "0") : value;
      });
    }

    var interval = window.setInterval(tick, 1000);
    tick();
  }

  document.querySelectorAll("[data-countdown-to]").forEach(initCountdown);

  /* ======================================================================
     2. Revelado de tarjetas al hacer scroll
     ----------------------------------------------------------------------
     Equivalente al `gsap.fromTo(card, { opacity: 0, y: 20 }, { opacity: 1,
     y: 0, duration: 0.7, ease: "power2.out", scrollTrigger: { start:
     "top 88%" } })` del sitio original.
     ====================================================================== */

  function initReveal() {
    var cards = Array.prototype.slice.call(document.querySelectorAll(".gsap-card"));
    if (cards.length === 0) return;

    // Sin movimiento reducido, ni sin soporte, las tarjetas se muestran tal cual.
    if (REDUCE_MOTION || !("IntersectionObserver" in window)) return;

    cards.forEach(function (card) {
      card.style.opacity = "0";
      card.style.transform = "translateY(20px)";
      card.style.transition =
        "opacity 0.7s cubic-bezier(0.2, 0.7, 0.3, 1), transform 0.7s cubic-bezier(0.2, 0.7, 0.3, 1)";
    });

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          entry.target.style.opacity = "1";
          entry.target.style.transform = "none";
          entry.target.classList.add("is-revealed");
          observer.unobserve(entry.target);
        });
      },
      // "top 88%" → el borde superior del elemento cruza el 88% del viewport.
      { rootMargin: "0px 0px -12% 0px", threshold: 0 }
    );

    cards.forEach(function (card) {
      observer.observe(card);
    });

    // Red de seguridad: si algo falla, nunca dejamos contenido invisible.
    window.addEventListener("error", function revealAll() {
      cards.forEach(function (card) {
        card.style.opacity = "1";
        card.style.transform = "none";
      });
      window.removeEventListener("error", revealAll);
    });
  }

  initReveal();
})();
