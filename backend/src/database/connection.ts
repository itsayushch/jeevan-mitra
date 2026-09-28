import { PrismaClient } from '@prisma/client';

let dbInstance: PrismaClient | null = null;

export function getDb(): PrismaClient {
  if (!dbInstance) {
    dbInstance = new PrismaClient();
  }
  return dbInstance;
}

export function closeDatabase(): void {
  if (dbInstance) {
    dbInstance.$disconnect().catch(console.error);
    dbInstance = null;
  }
}
