import { defineType, defineField } from 'sanity';

// Stüdyo/Hakkında — tekil (singleton) doküman.
export default defineType({
  name: 'studio',
  title: 'Studio / About',
  type: 'document',
  fields: [
    defineField({
      name: 'body',
      title: 'Body',
      type: 'object',
      fields: [
        { name: 'en', title: 'English', type: 'text', rows: 6 },
        { name: 'tr', title: 'Türkçe', type: 'text', rows: 6 },
      ],
    }),
    defineField({
      name: 'image',
      title: 'Portrait image',
      type: 'image',
      options: { hotspot: true },
    }),
    defineField({
      name: 'team',
      title: 'Team',
      type: 'array',
      of: [
        {
          type: 'object',
          fields: [
            { name: 'name', title: 'Name', type: 'string' },
            { name: 'role', title: 'Role', type: 'string' },
          ],
        },
      ],
    }),
  ],
});
