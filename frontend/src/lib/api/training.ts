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
  async getMyCourses(beneficiaryId: string = "ben_rajesh_kumar") {
    const res = await fetch(`${API_BASE}/learning/me/courses?beneficiary_id=${beneficiaryId}`);
    if (!res.ok) throw new Error('Failed to fetch my courses');
    return res.json();
  },

  async startCourse(courseId: string, beneficiaryId: string = "ben_rajesh_kumar") {
    const res = await fetch(`${API_BASE}/learning/courses/${courseId}/start?beneficiary_id=${beneficiaryId}`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to start course');
    return res.json();
  },

  async updateLessonProgress(lessonId: string, isCompleted: boolean, beneficiaryId: string = "ben_rajesh_kumar") {
    const res = await fetch(`${API_BASE}/learning/lessons/${lessonId}/progress?beneficiary_id=${beneficiaryId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_completed: isCompleted, last_position: 0 })
    });
    if (!res.ok) throw new Error('Failed to update progress');
    return res.json();
  }
};
