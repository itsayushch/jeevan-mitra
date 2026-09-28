import dotenv from 'dotenv';
import path from 'path';
import { z } from 'zod';

dotenv.config();

const envSchema = z.object({
  NODE_ENV: z.enum(['development', 'test', 'production']).default('development'),
  PORT: z.coerce.number().default(4000),
  HOST: z.string().default('0.0.0.0'),
  DATABASE_URL: z.string().default('postgresql://postgres:postgres@localhost:5432/jeevanmitra?schema=public'),
  JWT_SECRET: z.string().default('supersecret_jwt_key_for_dev_only'),
  JWT_EXPIRES_IN: z.string().default('24h'),
  AI_PROVIDER: z.enum(['mock', 'openai', 'bhashini', 'sarvam', 'gemini']).default('gemini'),
  OPENAI_API_KEY: z.string().optional(),
  BHASHINI_API_KEY: z.string().optional(),
  SARVAM_API_KEY: z.string().optional(),
  GEMINI_API_KEY: z.string().optional(),
  SUPABASE_URL: z.string().default(''),
  SUPABASE_SERVICE_KEY: z.string().default(''),
  DEFAULT_DISTRICT: z.string().default('Moradabad'),
  DEFAULT_STATE: z.string().default('Uttar Pradesh'),
  CONFIDENCE_THRESHOLD: z.coerce.number().default(0.75),
});

export const env = envSchema.parse(process.env);
export type Env = z.infer<typeof envSchema>;
