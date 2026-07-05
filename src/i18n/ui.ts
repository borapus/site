export const languages = { en: 'EN', tr: 'TR' } as const;
export const defaultLang = 'en';
export type Lang = keyof typeof languages;

export const ui = {
  en: {
    'site.name': 'PUS&CO',
    'nav.home': 'Index',
    'nav.projects': 'Projects',
    'nav.studio': 'Studio',
    'nav.contact': 'Contact',
    'nav.menu': 'Menu',
    'nav.close': 'Close',

    'hero.label': 'Architecture Studio — Istanbul',
    'hero.title': 'Shaped by context, not convention',
    'hero.intro': 'Pus&Co creates architecture as a unique response to landscape, climate, light, material and purpose — where nothing is arbitrary and every decision belongs.',
    'hero.scroll': 'Scroll',

    'home.selected': 'Selected Works',
    'home.selectedIndex': '01 — Works',
    'home.viewAll': 'View all projects',
    'home.philosophyLabel': '02 — Philosophy',
    'home.philosophy': 'We design in the space between things — where light meets material and restraint becomes luxury.',
    'home.philosophyBody': 'Every project begins with removal rather than addition. What remains — proportion, texture, the fall of daylight — is what endures.',
    'home.ctaLabel': '03 — Enquiry',
    'home.ctaTitle': 'Let us shape something lasting.',
    'home.ctaButton': 'Start a conversation',

    'projects.label': 'Selected Works',
    'projects.title': 'Projects',
    'projects.empty': 'Projects will appear here once they are published in the studio panel.',

    'detail.label': 'Project',
    'detail.overview': 'Overview',
    'detail.next': 'Next project',
    'detail.back': 'All projects',
    'detail.loading': 'Loading…',
    'detail.notFound': 'Project not found.',
    'detail.notConfigured': 'Connect Sanity to view this project.',
    'meta.location': 'Location',
    'meta.year': 'Year',
    'meta.area': 'Area',
    'meta.typology': 'Typology',
    'meta.client': 'Client',
    'meta.photographer': 'Photography',

    'studio.label': 'The Practice',
    'studio.title': 'Studio',
    'studio.lead': 'Pus&Co creates architecture shaped by context rather than convention.',
    'studio.body': 'Every project is a unique response to its landscape, climate, light, materials, and purpose. We combine bespoke design, technical expertise, and interdisciplinary leadership to achieve the optimum balance between vision, functionality, constructability, and investment. We believe the most enduring projects are those where nothing is arbitrary and every decision belongs.',
    'studio.founderLabel': 'Founder & Principal Architect',
    'studio.founder': 'Bora Pus',

    'contact.label': 'Enquiry',
    'contact.title': 'Contact',
    'contact.intro': 'For new projects, collaborations and press.',
    'contact.name': 'Name',
    'contact.email': 'Email',
    'contact.message': 'Message',
    'contact.send': 'Send message',
    'contact.sent': 'Thank you — we will be in touch shortly.',

    'footer.studio': 'Head Office',
    'footer.contact': 'Contact',
    'footer.social': 'Website',
    'footer.rights': 'All rights reserved.',
  },
  tr: {
    'site.name': 'PUS&CO',
    'nav.home': 'Anasayfa',
    'nav.projects': 'Projeler',
    'nav.studio': 'Stüdyo',
    'nav.contact': 'İletişim',
    'nav.menu': 'Menü',
    'nav.close': 'Kapat',

    'hero.label': 'Mimarlık Ofisi — İstanbul',
    'hero.title': 'Bağlamla biçimlenen mimari',
    'hero.intro': 'Pus&Co; peyzaja, iklime, ışığa, malzemeye ve amaca özgü bir yanıt olarak mimari üretir — hiçbir şeyin rastlantısal olmadığı, her kararın yerini bulduğu bir yaklaşım.',
    'hero.scroll': 'Kaydır',

    'home.selected': 'Seçili İşler',
    'home.selectedIndex': '01 — İşler',
    'home.viewAll': 'Tüm projeleri gör',
    'home.philosophyLabel': '02 — Felsefe',
    'home.philosophy': 'Tasarımı şeylerin arasındaki boşlukta yaparız — ışığın malzemeyle buluştuğu, sadeliğin lükse dönüştüğü yerde.',
    'home.philosophyBody': 'Her proje eklemekle değil, çıkarmakla başlar. Geriye kalan — oran, doku, gün ışığının düşüşü — kalıcı olandır.',
    'home.ctaLabel': '03 — Görüşme',
    'home.ctaTitle': 'Birlikte kalıcı bir şey tasarlayalım.',
    'home.ctaButton': 'Bir konuşma başlat',

    'projects.label': 'Seçili İşler',
    'projects.title': 'Projeler',
    'projects.empty': 'Projeler, stüdyo panelinde yayınlandıkça burada görünecek.',

    'detail.label': 'Proje',
    'detail.overview': 'Künye',
    'detail.next': 'Sonraki proje',
    'detail.back': 'Tüm projeler',
    'detail.loading': 'Yükleniyor…',
    'detail.notFound': 'Proje bulunamadı.',
    'detail.notConfigured': 'Bu projeyi görmek için Sanity’yi bağlayın.',
    'meta.location': 'Konum',
    'meta.year': 'Yıl',
    'meta.area': 'Alan',
    'meta.typology': 'Tipoloji',
    'meta.client': 'Müşteri',
    'meta.photographer': 'Fotoğraf',

    'studio.label': 'Ofis',
    'studio.title': 'Stüdyo',
    'studio.lead': 'Pus&Co, alışkanlıkların değil bağlamın biçimlendirdiği bir mimari üretir.',
    'studio.body': 'Her proje; kendi peyzajına, iklimine, ışığına, malzemesine ve amacına özgü bir yanıttır. Vizyon, işlevsellik, inşa edilebilirlik ve yatırım arasındaki en doğru dengeyi kurmak için özgün tasarımı, teknik uzmanlığı ve disiplinler arası liderliği bir araya getiririz. En kalıcı projelerin, hiçbir şeyin rastlantısal olmadığı ve her kararın yerini bulduğu projeler olduğuna inanırız.',
    'studio.founderLabel': 'Kurucu & Baş Mimar',
    'studio.founder': 'Bora Pus',

    'contact.label': 'Görüşme',
    'contact.title': 'İletişim',
    'contact.intro': 'Yeni projeler, iş birlikleri ve basın için.',
    'contact.name': 'Ad Soyad',
    'contact.email': 'E-posta',
    'contact.message': 'Mesaj',
    'contact.send': 'Mesaj gönder',
    'contact.sent': 'Teşekkürler — en kısa sürede size döneceğiz.',

    'footer.studio': 'Merkez Ofis',
    'footer.contact': 'İletişim',
    'footer.social': 'Web',
    'footer.rights': 'Tüm hakları saklıdır.',
  },
} as const;

export type UIKey = keyof (typeof ui)['en'];

export function useTranslations(lang: Lang) {
  return function t(key: UIKey): string {
    return ui[lang][key] ?? ui[defaultLang][key];
  };
}

export function getLangFromUrl(url: URL): Lang {
  const [, seg] = url.pathname.split('/');
  if (seg === 'tr' || seg === 'en') return seg;
  return defaultLang;
}

/** Verilen dil için locale önekli yol üretir: path('/projects','tr') => '/tr/projects' */
export function localizedPath(path: string, lang: Lang): string {
  const clean = path === '/' ? '' : path;
  return `/${lang}${clean}`;
}
