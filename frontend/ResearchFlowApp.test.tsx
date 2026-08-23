import { describe, expect, it } from 'vitest'
import ResearchFlowApp from './ResearchFlowApp'

describe('ResearchFlowApp', () => {
  it('exports the application component', () => {
    expect(typeof ResearchFlowApp).toBe('function')
  })
})
