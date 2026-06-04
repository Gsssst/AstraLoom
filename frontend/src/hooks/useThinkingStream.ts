import { useState, useCallback, useRef } from 'react';

interface ThinkingState {
  reasoning: string;
  content: string;
  isThinking: boolean;
  thinkingDone: boolean;
  thinkingStartTime: number | null;
}

/**
 * Hook for consuming SSE streams that include reasoning events.
 * Parses data: lines looking for {"type": "reasoning"|"content", "content": "..."}
 */
export function useThinkingStream() {
  const [state, setState] = useState<ThinkingState>({
    reasoning: '',
    content: '',
    isThinking: false,
    thinkingDone: false,
    thinkingStartTime: null,
  });

  const stateRef = useRef(state);
  stateRef.current = state;

  const reset = useCallback(() => {
    setState({
      reasoning: '',
      content: '',
      isThinking: false,
      thinkingDone: false,
      thinkingStartTime: null,
    });
  }, []);

  /**
   * Process an SSE data line. Returns the parsed event or null.
   */
  const processLine = useCallback((line: string): { type: string; content: string } | null => {
    if (!line.startsWith('data: ')) return null;
    const data = line.slice(6);
    if (data === '[DONE]') return null;

    try {
      const event = JSON.parse(data);

      // Handle structured events from chat_stream_with_thinking
      if (event.type === 'reasoning') {
        setState(prev => ({
          ...prev,
          reasoning: prev.reasoning + event.content,
          isThinking: true,
          thinkingStartTime: prev.thinkingStartTime || Date.now(),
        }));
        return { type: 'reasoning', content: event.content };
      }

      if (event.type === 'content') {
        setState(prev => ({
          ...prev,
          content: prev.content + event.content,
          isThinking: false,
          thinkingDone: true,
        }));
        return { type: 'content', content: event.content };
      }

      // Handle legacy string tokens (no type field)
      if (typeof event === 'string') {
        setState(prev => ({
          ...prev,
          content: prev.content + event,
          isThinking: false,
          thinkingDone: true,
        }));
        return { type: 'content', content: event };
      }

      // Handle SSE events with event.content as string (old format)
      if (typeof event.content === 'string' && !event.type) {
        setState(prev => ({
          ...prev,
          content: prev.content + event.content,
          isThinking: false,
          thinkingDone: true,
        }));
        return { type: 'content', content: event.content as string };
      }
    } catch {
      // Plain text token (old format): use as content
      setState(prev => ({
        ...prev,
        content: prev.content + data,
        isThinking: false,
        thinkingDone: true,
      }));
      return { type: 'content', content: data };
    }

    return null;
  }, []);

  return {
    ...state,
    reset,
    processLine,
  };
}
