import Database from 'better-sqlite3';
import fs from 'fs';
import path from 'path';
import { env } from '../config/env.js';

let dbInstance: Database.Database | null = null;

export function getDatabase(customPath?: string): Database.Database {
  if (dbInstance && !customPath) {
    return dbInstance;
  }

  const targetPath = customPath || env.DATABASE_PATH;
  
  if (targetPath !== ':memory:') {
    const dir = path.dirname(targetPath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  }

  const db = new Database(targetPath);
  
  // Enforce WAL mode and foreign key integrity
  db.pragma('journal_mode = WAL');
  db.pragma('foreign_keys = ON');
  db.pragma('busy_timeout = 5000');

  if (!customPath) {
    dbInstance = db;
  }
  return db;
}

export function closeDatabase(): void {
  if (dbInstance) {
    dbInstance.close();
    dbInstance = null;
  }
}
