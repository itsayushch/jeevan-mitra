import type { Language } from '../../types';

const API_BASE = 'http://localhost:4000/api/v1';

export const trainingApi = {
  async getCourses(language: Language) {
    const res = await fetch(`${API_BASE}/training/courses?language=${language}`);
    if (!res.ok) throw new Error('Failed to fetch courses');
    return res.json();
  },
  
  async getCourse(courseId: string) {
    const res = await fetch(`${API_BASE}/training/courses/${courseId}`);
    if (!res.ok) throw new Error('Failed to fetch course');
    return res.json();
  },

  async getCourseModules(courseId: string) {
    const res = await fetch(`${API_BASE}/training/courses/${courseId}/modules`);
    if (!res.ok) throw new Error('Failed to fetch modules');
    return res.json();
  },

  async getModuleLessons(moduleId: string) {
    const res = await fetch(`${API_BASE}/training/modules/${moduleId}`);
    if (!res.ok) throw new Error('Failed to fetch lessons');
    return res.json();
  },

  async getLesson(lessonId: string) {
    const res = await fetch(`${API_BASE}/training/lessons/${lessonId}`);
    if (!res.ok) throw new Error('Failed to fetch lesson');
    return res.json();
  }
};

export const learningApi = {
  getAuthHeaders() {
    // Basic auth handling for Sprint 3. In a real app this hooks into the full AuthContext.
    // For now, we will assume a valid token is in localStorage, and if not, we fail gracefully or redirect.
    const token = typeof window !== 'undefined' ? localStorage.getItem('jm_jwt_token') : null;
    return token ? { 'Authorization': `Bearer ${token}` } : {};
  },

  async loginForDemo() {
    // Auto-login for demo purposes since full UI auth flow isn't in scope for this specific file,
    // but we need a valid JWT token to satisfy Sprint 3 requirements.
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email_or_phone: 'learn@example.com', password: 'SecurePassword123!' })
    });
    if (res.ok) {
      const data = await res.json();
      localStorage.setItem('jm_jwt_token', data.access_token);
      return data.access_token;
    }
    return null;
  },

  async ensureAuth(res: Response) {
    if (res.status === 401) {
      console.warn("Session expired or missing, attempting re-login for demo...");
      const token = await this.loginForDemo();
      if (!token) throw new Error("Auth failed");
      return token;
    }
    return null;
  },

  async getMyOverview() {
    let res = await fetch(`${API_BASE}/learning/me/overview`, { headers: this.getAuthHeaders() });
    if (res.status === 401) {
      await this.ensureAuth(res);
      res = await fetch(`${API_BASE}/learning/me/overview`, { headers: this.getAuthHeaders() });
    }
    if (!res.ok) throw new Error('Failed to fetch learning overview');
    return res.json();
  },

  async getCourseProgress(courseId: string) {
    let res = await fetch(`${API_BASE}/learning/me/courses/${courseId}`, { headers: this.getAuthHeaders() });
    if (res.status === 401) {
      await this.ensureAuth(res);
      res = await fetch(`${API_BASE}/learning/me/courses/${courseId}`, { headers: this.getAuthHeaders() });
    }
    if (!res.ok) throw new Error('Failed to fetch course progress');
    return res.json();
  },

  async recordLessonAccess(lessonId: string) {
    let res = await fetch(`${API_BASE}/learning/me/lessons/${lessonId}/access`, { 
      method: 'POST',
      headers: this.getAuthHeaders() 
    });
    if (res.status === 401) {
      await this.ensureAuth(res);
      res = await fetch(`${API_BASE}/learning/me/lessons/${lessonId}/access`, { method: 'POST', headers: this.getAuthHeaders() });
    }
    if (!res.ok) throw new Error('Failed to record lesson access');
    return res.json();
  },

  async updateLessonProgress(lessonId: string, isCompleted: boolean) {
    const method = isCompleted ? 'PUT' : 'DELETE';
    let res = await fetch(`${API_BASE}/learning/me/lessons/${lessonId}/completion`, {
      method,
      headers: this.getAuthHeaders()
    });
    if (res.status === 401) {
      await this.ensureAuth(res);
      res = await fetch(`${API_BASE}/learning/me/lessons/${lessonId}/completion`, { method, headers: this.getAuthHeaders() });
    }
    if (!res.ok) throw new Error('Failed to update progress');
    return res.json();
  },
  
  async toggleBookmark(lessonId: string, isBookmarked: boolean) {
    const method = isBookmarked ? 'PUT' : 'DELETE';
    let res = await fetch(`${API_BASE}/learning/me/lessons/${lessonId}/bookmark`, {
      method,
      headers: this.getAuthHeaders()
    });
    if (res.status === 401) {
      await this.ensureAuth(res);
      res = await fetch(`${API_BASE}/learning/me/lessons/${lessonId}/bookmark`, { method, headers: this.getAuthHeaders() });
    }
    if (!res.ok) throw new Error('Failed to toggle bookmark');
    return res.json();
  }
};
