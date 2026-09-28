import { Request, Response } from 'express';

export class ChatController {
  public handleChat = async (req: Request, res: Response): Promise<void> => {
    try {
      const message = req.method === 'GET' ? req.query.message : req.body.message;

      if (!message) {
        res.status(400).json({ error: 'Message is required' });
        return;
      }

      const apiKey = process.env.GEMINI_API_KEY || process.env.AI_API_KEY;

      if (!apiKey) {
        // Fallback response when external cloud service is unconfigured
        res.json({
          reply: `Thank you for your inquiry about PM-AJAY skilling programs. We have received: "${message}". Please visit /api/recommendations or contact your local district coordinator for direct enrollment.`
        });
        return;
      }

      const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key=${apiKey}`;

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          contents: [{ parts: [{ text: String(message) }] }]
        })
      });

      const data = await response.json() as any;

      if (!response.ok) {
        res.status(response.status || 500).json({ error: 'External service error', details: data });
        return;
      }

      const reply = data.candidates?.[0]?.content?.parts?.[0]?.text || "No response generated.";

      res.json({ reply });
    } catch (error) {
      res.status(500).json({ error: 'Internal server error', details: String(error) });
    }
  };
}
