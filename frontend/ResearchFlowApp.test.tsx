// @vitest-environment jsdom

import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import ResearchFlowApp from './ResearchFlowApp'

beforeEach(() => {
  vi.stubGlobal('requestAnimationFrame', (callback: FrameRequestCallback) => {
    callback(0)
    return 1
  })
  Object.defineProperty(HTMLElement.prototype, 'scrollIntoView', {
    configurable: true,
    value: vi.fn(),
  })
})

describe('ResearchFlowApp', () => {
  it('renders the research composer and empty state', () => {
    render(<ResearchFlowApp />)

    expect(screen.getByText('Ask a research question.')).toBeTruthy()
    expect(screen.getByPlaceholderText('Ask anything')).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Send message' })).toBeTruthy()
  })

  it('handles casual prompts locally without calling the research API', async () => {
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)

    render(<ResearchFlowApp />)

    fireEvent.change(screen.getByPlaceholderText('Ask anything'), { target: { value: 'hello' } })
    fireEvent.click(screen.getByRole('button', { name: 'Send message' }))

    await waitFor(() => {
      expect(screen.getByText(/If you want a full research run/)).toBeTruthy()
    })
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('posts research questions and renders a completed response', async () => {
    const responses = [
      { ok: true, json: async () => ({ id: 42, status: 'queued' }) },
      {
        ok: true,
        json: async () => ({
          answer: '# Research Report\n\nCompleted answer.',
          error: null,
          job_id: 42,
          query: 'compare logistics routes',
          readiness_score: 1,
          sources: [],
          status: 'completed',
          workflow: [],
        }),
      },
    ]
    const fetchMock = vi.fn().mockImplementation(async () => responses.shift())
    vi.stubGlobal('fetch', fetchMock)

    render(<ResearchFlowApp />)

    fireEvent.change(screen.getByPlaceholderText('Ask anything'), {
      target: { value: 'compare logistics routes' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Send message' }))

    await waitFor(() => {
      expect(screen.getByText('Research Report')).toBeTruthy()
      expect(screen.getByText('Completed answer.')).toBeTruthy()
    })

    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(fetchMock.mock.calls[0][0]).toContain('/api/research/')
    expect(fetchMock.mock.calls[0][1]).toMatchObject({
      method: 'POST',
      body: JSON.stringify({ query: 'compare logistics routes' }),
    })
    expect(fetchMock.mock.calls[1][0]).toContain('/api/research/42/chat')
  })
})
