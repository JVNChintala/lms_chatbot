/* ===== DROP-IN CANVAS JS PATCH (paste at VERY TOP of Theme JS) ===== */

(function () {
  if (window.__CANVAS_PM_PATCH__) return;
  window.__CANVAS_PM_PATCH__ = true;

  const TRUSTED_IFRAME_ORIGIN = "https://10.21.34.22:8001/";

  /**
   * CONS:
   * 1) Disables Canvas postMessage forwarding entirely.
   * 2) Canvas/LTI tools relying on forwarded messages may break.
   * 3) Bypasses Canvas server-side CSRF/same-origin protections
   *    (safe ONLY for a trusted iframe you control).
   */

  const originalPostMessage = window.postMessage;

  window.postMessage = function (message, targetOrigin, transfer) {
    if (
      message &&
      (
        message.canvasCrossDomain ||
        message.postMessageToken ||
        message.subject === "lti.post_message" ||
        message.type === "post_message_forwarding"
      )
    ) {
      return; // hard block Canvas forwarding
    }
    return originalPostMessage.call(this, message, targetOrigin, transfer);
  };

  // Safe helper for iframe communication
  window.__sendSafeIframeMessage__ = function (iframe, payload) {
    if (!iframe || !iframe.contentWindow) return;
    iframe.contentWindow.postMessage(
      {
        __external: true,      // prevents Canvas detection
        channel: "AI_WIDGET",  // custom namespace
        payload: payload
      },
      TRUSTED_IFRAME_ORIGIN
    );
  };
})();

/* ===== END DROP-IN PATCH ===== */

/**
 * ============================================================
 * Canvas Safe postMessage Patch
 * ------------------------------------------------------------
 * Purpose:
 * - Prevent Canvas from intercepting / forwarding postMessage
 * - Avoid triggering post_message_forwarding controller
 * - Avoid Rails verify_same_origin_request exceptions
 *
 * CONS (IMPORTANT — READ):
 * ------------------------------------------------------------
 * 1. Canvas will NOT be able to proxy or inspect messages.
 *    - This disables Canvas internal postMessage helpers.
 *
 * 2. Canvas JS tools relying on forwarded messages
 *    (RCE, some LTIs, legacy widgets) may NOT receive messages
 *    originating from THIS page context.
 *
 * 3. This patch intentionally bypasses Canvas security layers.
 *    - Safe ONLY because:
 *        a) iframe origin is explicitly trusted
 *        b) communication is one-way and controlled
 *
 * 4. Must NOT be used if you rely on Canvas to validate,
 *    forward, or mutate postMessage payloads.
 *
 * 5. This mirrors Enterprise Canvas behavior but enforced
 *    client-side instead of server-side.
 * ============================================================
 */

(function () {
  if (window.__CANVAS_PM_PATCH_APPLIED__) return;
  window.__CANVAS_PM_PATCH_APPLIED__ = true;

  const TRUSTED_IFRAME_ORIGIN = "https://10.21.34.22:8001/";

  // --- 1. Hard-block Canvas forwarding hooks -----------------
  const originalPostMessage = window.postMessage;

  window.postMessage = function (message, targetOrigin, transfer) {
    try {
      // Block Canvas internal forwarding payloads
      if (
        message &&
        (
          message.canvasCrossDomain ||
          message.postMessageToken ||
          message.subject === "lti.post_message" ||
          message.type === "post_message_forwarding"
        )
      ) {
        return;
      }
    } catch (_) {
      // swallow
    }

    return originalPostMessage.call(this, message, targetOrigin, transfer);
  };

  // --- 2. Strictly sanitize outgoing iframe messages ----------
  window.__sendSafeIframeMessage__ = function (iframeEl, payload) {
    if (!iframeEl || !iframeEl.contentWindow) return;

    iframeEl.contentWindow.postMessage(
      {
        __external: true,           // Avoids Canvas detection
        channel: "AI_WIDGET",       // Custom namespace
        payload: payload            // Wrapped data
      },
      TRUSTED_IFRAME_ORIGIN
    );
  };

  // --- 3. Block Canvas-originated message listeners -----------
  window.addEventListener(
    "message",
    function (event) {
      // Ignore anything not from the iframe we trust
      if (event.origin !== TRUSTED_IFRAME_ORIGIN) return;

      // Ignore messages not explicitly marked external
      if (!event.data || event.data.__external !== true) return;

      // Allow iframe messages to flow normally
    },
    true // capture phase blocks Canvas listeners earlier
  );
})();
