import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import Database from 'better-sqlite3';
import { getDatabase } from './connection.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export function runMigrations(customDb?: Database.Database): void {
  const db = customDb || getDatabase();
  
  // Look in current directory (dist/database or src/database), then fallback to project root src/
  let schemaPath = path.resolve(__dirname, 'schema.sql');
  if (!fs.existsSync(schemaPath)) {
    schemaPath = path.resolve(process.cwd(), 'src', 'database', 'schema.sql');
  }
  if (!fs.existsSync(schemaPath)) {
    schemaPath = path.resolve(__dirname, '..', '..', 'src', 'database', 'schema.sql');
  }

  if (!fs.existsSync(schemaPath)) {
    throw new Error(`Schema file not found. Checked: ${schemaPath}`);
  }

  const schemaSql = fs.readFileSync(schemaPath, 'utf8');
  db.exec(schemaSql);
}
