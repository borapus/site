import { isPreview, SITE } from '../lib/seo';
export function GET() {
  const body = isPreview ? 'User-agent: *\nDisallow: /\n' : ['User-agent: *', 'Allow: /', 'Disallow: /admin/', 'Disallow: /api/', 'Disallow: /preview/', 'Disallow: /draft/', 'Disallow: /drafts/', `Sitemap: ${SITE}/sitemap.xml`, ''].join('\n');
  return new Response(body, { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
}
