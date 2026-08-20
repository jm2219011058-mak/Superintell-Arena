<template>
  <router-view />
</template>

<script setup>
// 使用 Vue Router 来管理页面
</script>

<style>
/* 全局样式重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: 'JetBrains Mono', 'Space Grotesk', 'Noto Sans SC', monospace;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #000000;
  background-color: #ffffff;
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
}

::-webkit-scrollbar-thumb {
  background: #000000;
}

::-webkit-scrollbar-thumb:hover {
  background: #333333;
}

/* --- Design Tokens: Motion --- */
:root {
  --ease-out: cubic-bezier(0.23, 1, 0.32, 1);
  --ease-in-out: cubic-bezier(0.77, 0, 0.175, 1);
  --duration-fast: 125ms;
  --duration-normal: 200ms;
  --duration-slow: 300ms;
}

/* 全局按钮样式 */
button {
  font-family: inherit;
  transition: transform var(--duration-fast) var(--ease-out);
}

/* Global :active press feedback — does not override buttons with custom :active */
button:active {
  transform: scale(0.97);
}

/* Only apply hover-dependent effects on devices that support hover */
@media (hover: hover) and (pointer: fine) {
  button:hover {
    /* base hover — individual components add their own overrides */
  }
}

/* --- Reduced Motion --- */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    transition-duration: 50ms !important;
    animation-duration: 50ms !important;
  }

  /* Keep opacity transitions, remove transform-based movement */
  .step-fade-enter-from,
  .step-fade-leave-to {
    transform: none !important;
  }

  .dropdown-enter-from,
  .dropdown-leave-to {
    transform: none !important;
  }
}
</style>
