import { Request, Response, NextFunction } from 'express';
import { env } from '../config/env.js';

export interface AuthenticatedRequest extends Request {
  user?: {
    id: string;
    role: string;
    district?: string;
    block?: string;
  };
}

export const authenticate = (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Missing or invalid authorization header' });
  }

  const token = authHeader.split(' ')[1];
  
  // TODO: Validate token with Supabase Auth or local JWT verification
  // For now, we mock the verification based on the token for scaffolding
  if (token === 'mock-worker-token') {
    req.user = { id: 'worker-1', role: 'field_worker', district: env.DEFAULT_DISTRICT };
    return next();
  } else if (token === 'mock-admin-token') {
    req.user = { id: 'admin-1', role: 'district_admin', district: env.DEFAULT_DISTRICT };
    return next();
  }

  return res.status(401).json({ error: 'Invalid token' });
};

export const requireRole = (allowedRoles: string[]) => {
  return (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
    if (!req.user || !allowedRoles.includes(req.user.role)) {
      return res.status(403).json({ error: 'Forbidden: Insufficient permissions' });
    }
    next();
  };
};
