import path from 'path'
import { defineConfig } from 'prisma/config'
import { PrismaSQLite } from 'prisma-adapter-sqlite'

export default defineConfig({
  schema: path.join(import.meta.dirname, 'prisma', 'schema.prisma'),
  migrate: {
    adapter: async () => {
      return new PrismaSQLite({
        url: 'file:' + path.join(import.meta.dirname, 'data', 'onetag.db'),
      })
    },
  },
})
