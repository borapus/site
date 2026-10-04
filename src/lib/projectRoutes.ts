import { getProjects, getProject } from './projects';
import type { Lang } from '../i18n/ui';
export async function projectRoutes(lang: Lang) {
  const cards = await getProjects(lang);
  return Promise.all(cards.map(async (card, i) => {
    if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(card.slug) || card.slug === 'detail') throw new Error(`Invalid project slug: ${card.slug}`);
    const project = await getProject(card.slug, lang);
    if (!project || !project.description.trim()) throw new Error(`Missing published project content: ${card.slug}`);
    return { params: { slug: card.slug }, props: { project, next: cards.length > 1 ? cards[(i + 1) % cards.length] : undefined } };
  }));
}
