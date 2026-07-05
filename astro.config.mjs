// @ts-check
import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';

// https://astro.build/config
export default defineConfig({
  // hreflang/sitemap bunu kullanır (apex = kanonik).
  site: 'https://pusnco.com',

  i18n: {
    locales: ['en', 'tr'],
    defaultLocale: 'en',
    routing: {
      // Her iki dil de açık önekli: /en ve /tr. Kök (/) dil algılama ile yönlendirir.
      prefixDefaultLocale: true,
    },
  },

  vite: {
    plugins: [tailwindcss()],
  },
});
