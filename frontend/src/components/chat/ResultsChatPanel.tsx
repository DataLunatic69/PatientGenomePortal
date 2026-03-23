import { useMemo, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { Loader2, Send } from 'lucide-react';
import { api } from '../../lib/api';
import type { ChatMessage } from '../../types/api';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';

interface ResultsChatPanelProps {
  jobId: string;
}

export default function ResultsChatPanel({ jobId }: ResultsChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content:
        'Hi! I can answer questions about your analysis results. Ask about risk levels, genes, tissues, or variant summaries.',
    },
  ]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  const historyForApi = useMemo(
    () => messages.filter((m) => m.content.trim().length > 0),
    [messages]
  );

  const scrollToBottom = () => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  };

  const sendMessage = async (e: FormEvent) => {
    e.preventDefault();
    const text = query.trim();
    if (!text || loading) {
      return;
    }

    const nextUser: ChatMessage = { role: 'user', content: text };
    setMessages((prev) => [...prev, nextUser]);
    setQuery('');
    setError(null);
    setLoading(true);

    try {
      const response = await api.chatWithResults(jobId, text, historyForApi);
      const reply: ChatMessage = {
        role: 'assistant',
        content: response.answer || 'I could not generate a response. Please try again.',
      };
      setMessages((prev) => [...prev, reply]);
      requestAnimationFrame(scrollToBottom);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'Failed to get response from results assistant.';
      setError(message);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'I had trouble answering that. Please try again in a moment.',
        },
      ]);
    } finally {
      setLoading(false);
      requestAnimationFrame(scrollToBottom);
    }
  };

  return (
    <Card className="h-[calc(100vh-11rem)] lg:sticky lg:top-24">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg">Results Chat</CardTitle>
      </CardHeader>
      <CardContent className="flex h-[calc(100%-5rem)] flex-col gap-3">
        <div
          ref={containerRef}
          className="flex-1 overflow-y-auto rounded-md border bg-slate-50 p-3"
        >
          <div className="space-y-3">
            {messages.map((message, idx) => (
              <div
                key={`${message.role}-${idx}`}
                className={`max-w-[92%] rounded-lg px-3 py-2 text-sm leading-relaxed ${
                  message.role === 'user'
                    ? 'ml-auto bg-blue-600 text-white'
                    : 'bg-white text-slate-800 border'
                }`}
              >
                {message.content}
              </div>
            ))}
            {loading && (
              <div className="inline-flex items-center gap-2 rounded-lg border bg-white px-3 py-2 text-sm text-slate-600">
                <Loader2 className="h-4 w-4 animate-spin" />
                Thinking...
              </div>
            )}
          </div>
        </div>

        {error && <p className="text-xs text-red-600">{error}</p>}

        <form onSubmit={sendMessage} className="flex items-center gap-2">
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask about your findings..."
            disabled={loading}
          />
          <Button type="submit" disabled={loading || query.trim().length === 0}>
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
