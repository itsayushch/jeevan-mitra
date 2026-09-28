import { Request, Response, NextFunction } from 'express';
import { ZodError } from 'zod';
import { UnauthorizedStateTransitionError } from '../repositories/recommendationRepository.js';
import { logger } from '../utils/logger.js';

export function errorHandler(
  err: Error,
  req: Request,
  res: Response,
  next: NextFunction
): void {
  logger.error('Unhandled API Error', {
    name: err.name,
    message: err.message,
    path: req.path,
    method: req.method,
  });

  if (err instanceof ZodError) {
    res.status(400).json({
      error: 'Validation Error',
      details: err.issues.map((e: any) => ({
        path: Array.isArray(e.path) ? e.path.join('.') : String(e.path),
        message: e.message,
      })),
    });
    return;
  }

  if (err instanceof UnauthorizedStateTransitionError) {
    res.status(403).json({
      error: 'Forbidden State Machine Invariant Violation',
      message: err.message,
    });
    return;
  }

  res.status(500).json({
    error: 'Internal Server Error',
    message: process.env.NODE_ENV === 'production' ? 'An unexpected error occurred' : err.message,
  });
}
