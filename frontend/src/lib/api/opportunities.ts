export const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchWithAuth(url: string, options: RequestInit = {}) {
    const token = localStorage.getItem("jm_jwt_token");
    const headers = new Headers(options.headers || {});
    if (token) {
        headers.set("Authorization", `Bearer ${token}`);
    }
    headers.set("Content-Type", "application/json");

    let response = await fetch(url, { ...options, headers });
    
    if (response.status === 401 && process.env.NEXT_PUBLIC_DEMO_AUTH_FALLBACK === "true") {
        const loginRes = await fetch(`${BASE_URL}/api/v1/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email_or_phone: "admin@example.com", password: "password123" })
        });
        if (loginRes.ok) {
            const data = await loginRes.json();
            localStorage.setItem("jm_jwt_token", data.access_token);
            headers.set("Authorization", `Bearer ${data.access_token}`);
            response = await fetch(url, { ...options, headers });
        }
    }
    
    if (!response.ok) {
        throw new Error(`API error: ${response.status} ${response.statusText}`);
    }
    return response.json();
}

export const opportunitiesApi = {
    async listQualifications(sector?: string) {
        let url = `${BASE_URL}/api/v1/qualifications`;
        if (sector) url += `?sector=${encodeURIComponent(sector)}`;
        return fetchWithAuth(url);
    },
    async listOpportunities() {
        return fetchWithAuth(`${BASE_URL}/api/v1/opportunities`);
    },
    async createOpportunity(data: any) {
        return fetchWithAuth(`${BASE_URL}/api/v1/staff/opportunities`, {
            method: "POST",
            body: JSON.stringify(data)
        });
    },
    async verifyOpportunity(oppId: string, action: string, data: any) {
        return fetchWithAuth(`${BASE_URL}/api/v1/staff/opportunities/${oppId}/${action}`, {
            method: "POST",
            body: JSON.stringify(data)
        });
    },
    async submitOpportunity(data: {
        input_mode: 'text' | 'voice';
        text: string;
        locale?: string;
        audio_storage_key?: string;
        transcript_confidence?: number;
    }) {
        return fetchWithAuth(`${BASE_URL}/api/v1/opportunity-submissions`, {
            method: "POST",
            body: JSON.stringify(data)
        });
    },
    async listMySubmissions() {
        return fetchWithAuth(`${BASE_URL}/api/v1/opportunity-submissions/me`);
    }
};
