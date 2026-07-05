// Yerel proje verisi (seed).
// Sanity yapılandırılınca (PUBLIC_SANITY_PROJECT_ID) otomatik olarak Sanity verisi
// kullanılır; bu dosya yalnızca Sanity bağlı değilken devreye girer (site boş kalmasın diye).
export type LocalProject = {
  slug: string;
  year: string;
  featured: boolean;
  orientation: 'portrait' | 'landscape';
  cover: string | null;
  gallery: string[];
  title: { en: string; tr: string };
  location: { en: string; tr: string };
  typology: { en: string; tr: string };
  area: string;
  client: string;
  photographer: string;
  description: { en: string; tr: string };
};

export const localProjects: LocalProject[] = [
  {
    slug: 'tk-house',
    year: '',
    featured: true,
    orientation: 'landscape',
    cover: '/images/projects/tk-house.jpg',
    gallery: [],
    title: { en: 'TK House', tr: 'TK House' },
    location: { en: 'Urla, İzmir', tr: 'Urla, İzmir' },
    typology: { en: 'Residential', tr: 'Konut' },
    area: '',
    client: '',
    photographer: '',
    description: {
      en: 'TK House was conceived within the constraints of an existing building envelope, using a lightweight steel structure to maximize openness and transparency. Large glazed surfaces establish a continuous relationship with the surrounding forest, transforming spatial limitations into an opportunity for light-filled living.',
      tr: 'TK House, mevcut yapının kütlesel sınırlarını koruyarak yeniden inşa edilen bir konut projesidir. Tasarım, izin verilen yapı hacmini en verimli şekilde değerlendirirken, hafif çelik strüktür ve geniş cam yüzeylerle mekânsal açıklığı ve doğayla kurulan ilişkiyi güçlendirmektedir.',
    },
  },
  {
    slug: 'uc-house',
    year: '',
    featured: true,
    orientation: 'landscape',
    cover: '/images/projects/uc-house.jpg',
    gallery: [],
    title: { en: 'UÇ House', tr: 'UÇ House' },
    location: { en: 'İstanbul / Gebze', tr: 'İstanbul / Gebze' },
    typology: { en: 'Residential', tr: 'Konut' },
    area: '',
    client: '',
    photographer: '',
    description: {
      en: 'UÇ House reinterprets multi-generational living through a composition of interconnected volumes. Shared living spaces, private rooms, and service areas are organized as independent structures, creating a balance between privacy and togetherness. The roof geometry draws inspiration from the surrounding mountain silhouettes and the changing path of the sun throughout the day, while natural stone, timber, and expansive glazing connect the house to its panoramic setting and the surrounding landscape.',
      tr: 'UÇ House, çoklu yaşamı birbirine entegre hacimler üzerinden kurgular. Ortak yaşam alanları, özel mekânlar ve servis birimleri bağımsız yapılar olarak tasarlanarak hem mahremiyet hem de birliktelik sağlanmıştır. Çatı formu, çevredeki dağ siluetleri ve gün boyunca değişen güneş hareketlerinden ilham alırken; taş, ahşap ve geniş cam yüzeyler yapıyı hâkim olduğu manzara ve doğal çevreyle bütünleştirir.',
    },
  },
  {
    slug: 'gu-house',
    year: '',
    featured: true,
    orientation: 'landscape',
    cover: '/images/projects/gu-house.jpg',
    gallery: [],
    title: { en: 'GU House', tr: 'GU House' },
    location: { en: 'Dalaman / Ortaca', tr: 'Dalaman / Ortaca' },
    typology: { en: 'Residential', tr: 'Konut' },
    area: '',
    client: '',
    photographer: '',
    description: {
      en: "GU House is designed around a sheltered inner courtyard that responds to the region's intense sunlight while creating a private living environment protected from neighboring properties. The composition balances openness and privacy, allowing natural light and outdoor spaces to become an integral part of daily life. The complexity of the architectural geometry is unified through the consistent use of board-formed concrete, creating a calm and timeless architectural expression.",
      tr: 'GU House, bölgenin yoğun güneş iklimine yanıt veren ve komşu parsellerden mahremiyet sağlayan korunaklı bir iç avlu etrafında kurgulanmıştır. Açıklık ve mahremiyet arasında dengeli bir yaşam deneyimi sunan tasarım, gün ışığını ve açık yaşam alanlarını gündelik hayatın ayrılmaz bir parçası hâline getirir. Hareketli cephe geometrisi, formwork betonun tek ve tutarlı bir malzeme olarak kullanılmasıyla dengelenerek yalın, güçlü ve zamansız bir mimari kimlik kazanır.',
    },
  },
];
