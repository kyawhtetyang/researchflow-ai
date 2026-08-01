import React, { useEffect, useRef, useState } from 'react';

type Theme = 'light' | 'dark';
type MessageRole = 'assistant' | 'user';

type SourceNote = {
  href?: string;
  label: string;
  meta?: string;
  text: string;
};

type WorkflowNote = {
  label: string;
  text: string;
};

type ChatMessage = {
  id: string;
  role: MessageRole;
  sources?: SourceNote[];
  text: string;
  workflow?: WorkflowNote[];
};

type ResearchJobResponse = {
  id: number;
  status: string;
};

type ResearchChatResponse = {
  answer: string;
  error?: string | null;
  job_id: number;
  query: string;
  readiness_score: number;
  sources: Array<{
    quality_score?: number | null;
    snippet?: string | null;
    title: string;
    url: string;
  }>;
  status: 'queued' | 'thinking' | 'completed' | 'failed' | string;
  workflow: Array<{
    label: string;
    output: string;
    status: string;
  }>;
};

const ANSWER_MARKER = '## Answer';
const THINKING_MARKER = '## Thinking';
const DEFAULT_THEME: Theme = 'dark';
const API_BASE = import.meta.env.VITE_API_BASE_URL || '';
const POLL_INTERVAL_MS = 1800;
const MAX_POLL_ATTEMPTS = 80;
const createId = () => `${Date.now()}-${Math.random().toString(16).slice(2)}`;
const CASUAL_PATTERNS = new Set([
  'hello',
  'hi',
  'hey',
  'yo',
  'thanks',
  'thank you',
  'ok',
  'okay',
  'cool',
  'nice',
  'good morning',
  'good afternoon',
  'good evening',
]);

const readStoredTheme = (): Theme => {
  const stored = window.localStorage.getItem('theme');
  return stored === 'light' || stored === 'dark' ? stored : DEFAULT_THEME;
};

const renderInlineMarkdown = (text: string) => {
  const segments = text.split(/(\*\*.*?\*\*)/g).filter(Boolean);

  return segments.map((segment, index) => {
    const boldMatch = segment.match(/^\*\*(.*?)\*\*$/);
    if (boldMatch) {
      return <strong key={`${segment}-${index}`}>{boldMatch[1]}</strong>;
    }
    return <React.Fragment key={`${segment}-${index}`}>{segment}</React.Fragment>;
  });
};

const renderListItemContent = (item: string) => {
  const cleaned = item.trim();
  const titleMatch = cleaned.match(/^\*\*(.*?)\*\*(.*)$/);
  if (!titleMatch) {
    return <span>{renderInlineMarkdown(cleaned)}</span>;
  }

  const [, title, remainder] = titleMatch;
  const body = remainder.trim();

  return (
    <div className="answer-list-item">
      <div className="answer-list-lead">{title}</div>
      {body ? <div className="answer-list-body">{renderInlineMarkdown(body)}</div> : null}
    </div>
  );
};

const stripInlineSourcesSection = (text: string) => {
  return text
    .replace(/\n## Sources[\s\S]*$/i, '')
    .replace(/\nSources\s+1\.[\s\S]*$/i, '')
    .trim();
};

const domainFromUrl = (value: string) => {
  try {
    return new URL(value).hostname.replace(/^www\./, '');
  } catch {
    return value;
  }
};

const renderWorkflowStep = (label: string, text: string) => {
  const trimmed = text.trim();

  if (label === 'planner') {
    const items = trimmed.split('\n').map((line) => line.trim()).filter(Boolean);
    return (
      <ol className="workflow-list workflow-list-numbered">
        {items.map((item, index) => (
          <li key={`${label}-${index}`}>{renderInlineMarkdown(item)}</li>
        ))}
      </ol>
    );
  }

  if (label === 'search_agent') {
    const items = trimmed
      .split('\n')
      .map((line) => line.replace(/^-\s+/, '').trim())
      .filter(Boolean);

    return (
      <ul className="workflow-list">
        {items.map((item, index) => (
          <li key={`${label}-${index}`}>{renderInlineMarkdown(item)}</li>
        ))}
      </ul>
    );
  }

  if (label === 'analysis_agent') {
    const lines = trimmed.split('\n').map((line) => line.trim()).filter(Boolean);
    const blocks: Array<{ claim: string; evidence?: string }> = [];
    let current: { claim: string; evidence?: string } | null = null;

    lines.forEach((line) => {
      if (/^\d+\.\s+/.test(line)) {
        if (current) {
          blocks.push(current);
        }
        current = { claim: line.replace(/^\d+\.\s+/, '').trim() };
        return;
      }

      if (/^Evidence:\s*/i.test(line)) {
        const evidenceText = line.replace(/^Evidence:\s*/i, '').trim();
        if (current) {
          current.evidence = evidenceText;
        }
        return;
      }

      if (current) {
        current.claim = `${current.claim} ${line}`.trim();
      }
    });

    if (current) {
      blocks.push(current);
    }

    if (blocks.length > 0) {
      return (
        <ol className="workflow-analysis-list">
          {blocks.map((block, index) => (
            <li key={`${label}-${index}`} className="workflow-analysis-item">
              <div className="workflow-analysis-claim">{renderInlineMarkdown(block.claim)}</div>
              {block.evidence ? (
                <div className="workflow-analysis-evidence">
                  <span>Evidence:</span> {renderInlineMarkdown(block.evidence)}
                </div>
              ) : null}
            </li>
          ))}
        </ol>
      );
    }
  }

  return <p className="workflow-paragraph">{renderInlineMarkdown(trimmed)}</p>;
};

const normalizePrompt = (value: string) => value.trim().toLowerCase().replace(/[!?.,]+$/g, '');

const isQuickReplyPrompt = (value: string) => {
  const normalized = normalizePrompt(value);
  if (!normalized) {
    return false;
  }

  if (CASUAL_PATTERNS.has(normalized)) {
    return true;
  }

  const wordCount = normalized.split(/\s+/).filter(Boolean).length;
  if (wordCount <= 2 && /^(hello|hi|hey|thanks|thank you|ok|okay|yo)\b/.test(normalized)) {
    return true;
  }

  return false;
};

const quickReplyForPrompt = (value: string) => {
  const normalized = normalizePrompt(value);

  if (/(thanks|thank you)/.test(normalized)) {
    return 'You are welcome. If you want, I can turn your next message into a deeper research brief with sources and recommendations.';
  }

  if (/^(ok|okay|cool|nice)$/.test(normalized)) {
    return 'Understood. When you are ready, send a topic, comparison, or question and I can run the full research workflow.';
  }

  return 'Hello. If you want a full research run, send a question, topic, or comparison and I will investigate it with sources.';
};

const ResearchFlowApp: React.FC = () => {
  const [theme, setTheme] = useState<Theme>(readStoredTheme);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState('');
  const [asking, setAsking] = useState(false);
  const inputRef = useRef<HTMLTextAreaElement | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const hasMessages = messages.length > 0;
  const isDark = theme === 'dark';
  const nextTheme = isDark ? 'light' : 'dark';

  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDark);
    window.localStorage.setItem('theme', theme);
  }, [isDark, theme]);

  useEffect(() => {
    if (!asking) {
      inputRef.current?.focus();
    }
  }, [asking]);

  useEffect(() => {
    requestAnimationFrame(() => {
      messagesEndRef.current?.scrollIntoView({ block: 'end' });
    });
  }, [messages, asking]);

  const addMessage = (message: Omit<ChatMessage, 'id'>) => {
    setMessages((current) => [...current, { ...message, id: createId() }]);
  };

  const updateMessage = (id: string, patch: Partial<ChatMessage>) => {
    setMessages((current) => (
      current.map((message) => (message.id === id ? { ...message, ...patch } : message))
    ));
  };

  const requestJson = async <T,>(path: string, options?: RequestInit): Promise<T> => {
    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`ResearchFlow API request failed with HTTP ${response.status}.`);
    }

    return response.json() as Promise<T>;
  };

  const chatToMessage = (chat: ResearchChatResponse): Partial<ChatMessage> => {
    const thinkingLines = [
      chat.status === 'queued' ? 'Queued research job and waiting for the worker.' : null,
      chat.status === 'thinking' ? 'Planning, gathering sources, analyzing evidence, and preparing the report.' : null,
      chat.workflow.length > 0 ? `Recorded ${chat.workflow.length} workflow step${chat.workflow.length === 1 ? '' : 's'}.` : null,
      chat.sources.length > 0 ? `Collected ${chat.sources.length} source${chat.sources.length === 1 ? '' : 's'}.` : null,
    ].filter(Boolean);

    const answer = chat.status === 'failed'
      ? chat.error || chat.answer || 'Research job failed before a report could be created.'
      : stripInlineSourcesSection(chat.answer || 'ResearchFlow is preparing the research brief.');
    return {
      text: `${THINKING_MARKER}
${thinkingLines.map((line) => `- ${line}`).join('\n') || '- ResearchFlow started the async workflow.'}

${ANSWER_MARKER}
${answer}`,
      sources: chat.sources.map((source) => ({
        href: source.url,
        label: source.title || 'Untitled source',
        meta: `${domainFromUrl(source.url)}${source.quality_score == null ? '' : ` · quality ${source.quality_score.toFixed(2)}`}`,
        text: source.snippet || 'Open source',
      })),
      workflow: chat.workflow.map((step) => ({
        label: step.label,
        text: step.output || step.status,
      })),
    };
  };

  const pollResearchJob = async (jobId: number, assistantMessageId: string) => {
    for (let attempt = 0; attempt < MAX_POLL_ATTEMPTS; attempt += 1) {
      const chat = await requestJson<ResearchChatResponse>(`/api/research/${jobId}/chat`);
      updateMessage(assistantMessageId, chatToMessage(chat));

      if (chat.status === 'completed' || chat.status === 'failed') {
        return;
      }

      await new Promise((resolve) => window.setTimeout(resolve, POLL_INTERVAL_MS));
    }

    updateMessage(assistantMessageId, {
      text: `${THINKING_MARKER}
- The backend accepted the research job, but the UI stopped polling to avoid waiting forever.

${ANSWER_MARKER}
ResearchFlow is still working. Please try again in a moment or refresh the job later.`,
    });
  };

  const askQuestion = async () => {
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion || asking) return;

    setQuestion('');
    addMessage({ role: 'user', text: trimmedQuestion });

    if (isQuickReplyPrompt(trimmedQuestion)) {
      addMessage({
        role: 'assistant',
        text: `${ANSWER_MARKER}
${quickReplyForPrompt(trimmedQuestion)}`,
      });
      return;
    }

    setAsking(true);

    const assistantMessageId = createId();
    setMessages((current) => [
      ...current,
      {
        id: assistantMessageId,
        role: 'assistant',
        text: `${THINKING_MARKER}
- Creating an async research job.
- Waiting for the worker to begin.

${ANSWER_MARKER}
ResearchFlow is starting the research workflow...`,
      },
    ]);

    try {
      const job = await requestJson<ResearchJobResponse>('/api/research/', {
        method: 'POST',
        body: JSON.stringify({ query: trimmedQuestion }),
      });
      await pollResearchJob(job.id, assistantMessageId);
    } catch (error) {
      updateMessage(assistantMessageId, {
        text: `${THINKING_MARKER}
- The frontend could not complete the backend request.

${ANSWER_MARKER}
${error instanceof Error ? error.message : 'ResearchFlow could not reach the backend.'}`,
      });
    } finally {
      setAsking(false);
    }
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      void askQuestion();
    }
  };

  const renderMessageText = (text: string) => {
    const [thinkingPart, answerPart] = text.includes(ANSWER_MARKER)
      ? text.split(ANSWER_MARKER)
      : ['', text];
    const thinkingText = thinkingPart.replace(THINKING_MARKER, '').trim();
    const answerText = answerPart.trim();

    return (
      <>
        {thinkingText && (
          <details className="thinking-panel">
            <summary>Thought for a few seconds</summary>
            <div className="thinking-text">{thinkingText}</div>
          </details>
        )}
        <div className="answer-text">{renderAnswer(answerText)}</div>
      </>
    );
  };

  const renderAnswer = (text: string) => {
    const blocks = text.split(/\n{2,}/).map((block) => block.trim()).filter(Boolean);

    return blocks.map((block, index) => {
      if (block.startsWith('# ')) {
        return <h2 className="answer-title" key={`${block}-${index}`}>{block.replace(/^#\s+/, '')}</h2>;
      }
      if (block.startsWith('## ')) {
        return <h3 className="answer-heading" key={`${block}-${index}`}>{block.replace(/^##\s+/, '')}</h3>;
      }
      if (/^(\*|-)\s+/m.test(block)) {
        const items = block.split('\n').map((line) => line.replace(/^(\*|-)\s+/, '').trim()).filter(Boolean);
        return (
          <ul className="answer-list" key={`${block}-${index}`}>
            {items.map((item) => <li key={item}>{renderListItemContent(item)}</li>)}
          </ul>
        );
      }
      if (/^\d+\.\s+/m.test(block)) {
        const items = block.split('\n').map((line) => line.replace(/^\d+\.\s+/, '').trim()).filter(Boolean);
        return (
          <ol className="answer-list" key={`${block}-${index}`}>
            {items.map((item) => <li key={item}>{renderListItemContent(item)}</li>)}
          </ol>
        );
      }
      return <p key={`${block}-${index}`}>{renderInlineMarkdown(block)}</p>;
    });
  };

  return (
    <>
      <header className="top-toolbar glass">
        <h1>ResearchFlow AI</h1>
        <div className="toolbar-actions">
          <button
            type="button"
            onClick={() => setTheme(nextTheme)}
            aria-label={`Switch to ${nextTheme} mode`}
            title={`Switch to ${nextTheme} mode`}
            className="theme-toggle"
          >
            {isDark ? (
              <svg className="theme-icon-svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v2m0 14v2m9-9h-2M5 12H3m14.95-6.95-1.41 1.41M7.46 16.54l-1.41 1.41m0-11.31 1.41 1.41m10.08 10.08 1.41 1.41M12 7a5 5 0 100 10 5 5 0 000-10z" />
              </svg>
            ) : (
              <svg className="theme-icon-svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12.79A9 9 0 1111.21 3a7 7 0 109.79 9.79z" />
              </svg>
            )}
          </button>
        </div>
      </header>

      <main className={`chat-shell ${hasMessages ? 'chat-shell-active' : 'chat-shell-empty'}`}>
        <section className="chat-window" aria-label="ResearchFlow chat">
          <div className="message-stack">
            {!hasMessages && (
              <div className="empty-state">
                <h2>Ask a research question.</h2>
                <p>ResearchFlow will plan, analyze, and return a cited research brief.</p>
              </div>
            )}

            {messages.map((message) => (
              <div className={`message-row message-row-${message.role}`} key={message.id}>
                <div className={`message-bubble message-bubble-${message.role}`}>
                  <div className="message-text">{message.role === 'assistant' ? renderMessageText(message.text) : message.text}</div>
                  {message.sources && message.sources.length > 0 && (
                    <div className="detail-stack">
                      <div className="detail-label">Sources</div>
                      {message.sources.map((source) => (
                        <details className="detail-card" key={source.label}>
                          <summary>
                            <span>{source.label}</span>
                            <span>note</span>
                          </summary>
                          <div className="source-card-body">
                            {source.meta ? <div className="source-meta">{source.meta}</div> : null}
                            <p>{source.text}</p>
                            {source.href ? (
                              <a
                                className="source-link"
                                href={source.href}
                                target="_blank"
                                rel="noreferrer"
                              >
                                Open source
                              </a>
                            ) : null}
                          </div>
                        </details>
                      ))}
                    </div>
                  )}
                  {message.workflow && message.workflow.length > 0 && (
                    <div className="detail-stack">
                      <div className="detail-label">Workflow</div>
                      {message.workflow.map((step) => (
                        <details className="detail-card" key={step.label}>
                          <summary>
                            <span>{step.label}</span>
                            <span>step</span>
                          </summary>
                          <div className="workflow-card-body">{renderWorkflowStep(step.label, step.text)}</div>
                        </details>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {asking && (
              <div className="message-row message-row-assistant">
                <div className="message-bubble message-bubble-assistant">
                  <div className="message-text">
                    <div className="thinking-inline">
                      <span className="thinking-dot" />
                      Thinking through the research plan...
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} aria-hidden="true" />
          </div>
        </section>

        <div className={`composer-wrap ${hasMessages ? 'composer-wrap-bottom' : 'composer-wrap-center'}`}>
          <div className="composer">
            <textarea
              ref={inputRef}
              rows={1}
              placeholder="Ask anything"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={handleKeyDown}
              disabled={asking}
            />
            <button
              type="button"
              className="composer-send-button"
              onClick={() => {
                void askQuestion();
              }}
              disabled={asking || !question.trim()}
              aria-label="Send message"
              title="Send message"
            >
              <svg className="composer-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 2L11 13" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M22 2L15 22L11 13L2 9L22 2Z" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          </div>
          <p className="composer-note">
            {asking ? 'Thinking...' : 'Research briefs include sources and workflow notes when available.'}
          </p>
        </div>
      </main>
    </>
  );
};

export default ResearchFlowApp;
