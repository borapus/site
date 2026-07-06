import { defineConfig } from 'sanity';
import { structureTool } from 'sanity/structure';
import { visionTool } from '@sanity/vision';
import { schemaTypes } from './schemas';

// Bu klasör ayrı, çalıştırılabilir bir Sanity Studio'dur.
// Kurulum (bkz. sanity/README.md):
//   1) sanity.io/manage'de proje oluştur, projectId'yi al
//   2) sanity/.env içine SANITY_STUDIO_PROJECT_ID=... yaz
//   3) cd sanity && npm install && npm run dev
export default defineConfig({
  name: 'default',
  title: 'Atelier Studio',
  projectId: process.env.SANITY_STUDIO_PROJECT_ID || '9zmri994',
  dataset: process.env.SANITY_STUDIO_DATASET || 'production',
  plugins: [structureTool(), visionTool()],
  schema: { types: schemaTypes },
});
