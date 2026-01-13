(function () {
  // Avoid multiple injections
  if (window.__AI_WIDGET_LOADED__) return;
  window.__AI_WIDGET_LOADED__ = true;

  // Wait until Canvas UI is ready
  function onReady(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }

  onReady(function () {
    // Canvas globals
    if (!window.ENV || !ENV.current_user_id) return;

    const container = document.createElement("div");
    container.id = "ai-assistant-container";
    container.innerHTML = `
      <div id="ai-toggle">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
        </svg>
      </div>
      <iframe
        id="ai-frame"
        src="https://10.21.34.22:8001/"
        allow="microphone"
      ></iframe>
    `;

    document.body.appendChild(container);

    const style = document.createElement("style");
    style.innerHTML = `
      #ai-toggle {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 48px;
        height: 48px;
        background: var(--ic-brand-button--primary-bgd, var(--ic-brand-primary, #0374B5));
        color: white;
        border-radius: 4px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        z-index: 100;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        transition: all 0.2s;
        border: 1px solid var(--ic-brand-primary, #0374B5);
      }
      #ai-toggle:hover {
        background: var(--ic-brand-button--primary-bgd-darkened-5, var(--ic-brand-primary-darkened-5, #0374B5));
        box-shadow: 0 2px 4px rgba(0,0,0,0.15);
      }
      #ai-frame {
        position: fixed;
        top: 0;
        right: 0;
        width: 400px;
        height: 100vh;
        border: none;
        border-left: 1px solid var(--ic-border-light, #C7CDD1);
        display: none;
        z-index: 99;
        box-shadow: -1px 0 3px rgba(0,0,0,0.08);
      }
    `;
    document.head.appendChild(style);

    const frame = document.getElementById("ai-frame");
    
    function sendCanvasContext() {
      let userRole = "student";
      const roles = ENV.current_user_roles || [];
      if (roles.includes("teacher") || roles.includes("instructor")) {
        userRole = "teacher";
      } else if (roles.includes("admin")) {
        userRole = "admin";
      }

      const isDark = document.body.classList.contains('high_contrast') || 
                     document.documentElement.getAttribute('data-theme') === 'dark' ||
                     window.matchMedia('(prefers-color-scheme: dark)').matches;

      const rootStyles = getComputedStyle(document.documentElement);
      const themeColors = {
        primary: rootStyles.getPropertyValue('--ic-brand-primary').trim(),
        secondary: rootStyles.getPropertyValue('--ic-brand-button--primary-bgd').trim(),
        font: rootStyles.getPropertyValue('--ic-brand-font-color-dark').trim(),
        link: rootStyles.getPropertyValue('--ic-link-color').trim(),
        background: rootStyles.getPropertyValue('--ic-brand-global-nav-bgd').trim()
      };

      const url = window.location.pathname;
      const contextData = {
        source: "canvas",
        canvas_user_id: ENV.current_user_id,
        username: ENV.current_user?.display_name || ENV.current_user?.name || "Canvas User",
        course_id: ENV.COURSE_ID || null,
        course_name: ENV.COURSE?.name || null,
        user_role: userRole,
        roles: roles,
        locale: ENV.LOCALE,
        theme: isDark ? 'dark' : 'light',
        theme_colors: themeColors,
        current_page: url,
        assignment_id: ENV.ASSIGNMENT_ID || null,
        quiz_id: ENV.QUIZ?.id || null,
        discussion_id: ENV.DISCUSSION?.id || null,
        module_id: url.match(/\/modules\/(\d+)/)?.[1] || null,
        context_type: ENV.context_asset_string?.split('_')[0] || null
      };
      
      frame.contentWindow.postMessage(contextData, "*");
      console.log("Sent Canvas context:", contextData);
    }
    
    frame.onload = () => setTimeout(sendCanvasContext, 100);

    document.getElementById("ai-toggle").onclick = () => {
      frame.style.display = frame.style.display === "none" ? "block" : "none";
      if (frame.style.display === "block") setTimeout(sendCanvasContext, 100);
    };
  });
})();
