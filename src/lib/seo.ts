import type { Lang } from '../i18n/ui';

export const SITE = 'https://pusnco.com';
export const absolute = (path: string) => new URL(path, SITE).href;
export const normalizedPath = (path: string) => `/${path.split('/').filter(Boolean).join('/').toLowerCase()}/`.replace(/^\/\/$/, '/');
export function shouldNoindex(environment: string | undefined, flag: string | undefined, path: string): boolean {
  return environment === 'preview' || environment === 'development' || flag === 'true' || flag === '1'
    || /^\/(?:en\/|tr\/)?(admin|api|preview|drafts?)(\/|$)/i.test(path);
}
export const isPreview = shouldNoindex(process.env.VERCEL_ENV, import.meta.env.SEO_NOINDEX, '/');
export const summary = (text: string) => {
  const clean = text.replace(/\s+/g, ' ').trim();
  if (clean.length <= 160) return clean;
  const part = clean.slice(0, 157);
  return `${part.slice(0, part.lastIndexOf(' '))}…`;
};
export function defaultDescription(lang: Lang, path: string): string {
  const tr = lang === 'tr';
  if (path.includes('/projects')) return tr
    ? 'PUS&CO’nun konut, mağaza, kültür ve kamusal alan projelerini; tasarım yaklaşımlarını, konumlarını ve mimari görsellerini keşfedin.'
    : 'Explore PUS&CO’s residential, retail, cultural and public-space projects, with architectural images, locations and the design approach behind each project.';
  if (path.includes('/studio')) return tr
    ? 'Bora Pus tarafından kurulan PUS&CO mimarlık ofisini ve peyzaj, iklim, ışık, malzeme ve amaçla biçimlenen tasarım yaklaşımını tanıyın.'
    : 'Meet PUS&CO, the architecture studio founded by Bora Pus, and discover its design approach shaped by landscape, climate, light, materials and purpose.';
  if (path.includes('/contact')) return tr
    ? 'Yeni mimari projeler, iş birlikleri ve basın talepleri için PUS&CO ile iletişime geçin. E-posta: info@pusnco.com.'
    : 'Contact PUS&CO about new architectural projects, collaborations and press enquiries. Email the studio at info@pusnco.com.';
  return '';
}
export const organization = {
  '@type': 'Organization', '@id': `${SITE}/#organization`, name: 'PUS&CO', url: SITE,
  logo: absolute('/logo-pusco.png'), email: 'info@pusnco.com',
  founder: { '@type': 'Person', name: 'Bora Pus' },
};
