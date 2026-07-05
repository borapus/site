import { defineType, defineField } from 'sanity';

// Basit alan-bazlı çeviri: her metin { en, tr } nesnesi.
const localizedString = (name: string, title: string) =>
  defineField({
    name,
    title,
    type: 'object',
    fields: [
      { name: 'en', title: 'English', type: 'string' },
      { name: 'tr', title: 'Türkçe', type: 'string' },
    ],
  });

const localizedText = (name: string, title: string) =>
  defineField({
    name,
    title,
    type: 'object',
    fields: [
      { name: 'en', title: 'English', type: 'text', rows: 4 },
      { name: 'tr', title: 'Türkçe', type: 'text', rows: 4 },
    ],
  });

export default defineType({
  name: 'project',
  title: 'Project',
  type: 'document',
  fields: [
    localizedString('title', 'Title'),
    defineField({
      name: 'slug',
      title: 'Slug',
      type: 'slug',
      options: { source: 'title.en', maxLength: 96 },
      validation: (r) => r.required(),
    }),
    defineField({ name: 'year', title: 'Year', type: 'number' }),
    localizedString('location', 'Location'),
    localizedString('typology', 'Typology'),
    defineField({ name: 'area', title: 'Area (m²)', type: 'string' }),
    defineField({ name: 'client', title: 'Client', type: 'string' }),
    defineField({ name: 'photographer', title: 'Photographer', type: 'string' }),
    defineField({
      name: 'orientation',
      title: 'Cover orientation (gallery layout)',
      type: 'string',
      options: { list: ['landscape', 'portrait'], layout: 'radio' },
      initialValue: 'landscape',
    }),
    defineField({ name: 'featured', title: 'Featured on homepage', type: 'boolean', initialValue: false }),
    defineField({
      name: 'coverImage',
      title: 'Cover image',
      type: 'image',
      options: { hotspot: true },
      validation: (r) => r.required(),
    }),
    defineField({
      name: 'gallery',
      title: 'Gallery',
      type: 'array',
      of: [{ type: 'image', options: { hotspot: true } }],
    }),
    localizedText('description', 'Description'),
  ],
  preview: {
    select: { title: 'title.en', subtitle: 'year', media: 'coverImage' },
  },
});
