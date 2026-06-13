import { useCallback, useEffect, useRef } from 'react';

const DEFAULT_BOTTOM_THRESHOLD_PX = 48;

interface UseChatAutoScrollOptions {
  bottomThresholdPx?: number;
}

export const useChatAutoScroll = (options: UseChatAutoScrollOptions = {}) => {
  const bottomThresholdPx = options.bottomThresholdPx ?? DEFAULT_BOTTOM_THRESHOLD_PX;
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const scrollEndRef = useRef<HTMLDivElement>(null);
  const followOutputRef = useRef(true);

  const isNearBottom = useCallback(() => {
    const container = scrollContainerRef.current;
    if (!container) return true;
    const distanceToBottom = container.scrollHeight - container.scrollTop - container.clientHeight;
    return distanceToBottom <= bottomThresholdPx;
  }, [bottomThresholdPx]);

  const syncFollowState = useCallback(() => {
    followOutputRef.current = isNearBottom();
  }, [isNearBottom]);

  useEffect(() => {
    const container = scrollContainerRef.current;
    if (!container) return;
    syncFollowState();
    container.addEventListener('scroll', syncFollowState, { passive: true });
    return () => container.removeEventListener('scroll', syncFollowState);
  }, [syncFollowState]);

  const scrollToBottomIfFollowing = useCallback(() => {
    if (!followOutputRef.current) return;
    scrollEndRef.current?.scrollIntoView({ block: 'end', behavior: 'auto' });
  }, []);

  const enableFollowOutput = useCallback(() => {
    followOutputRef.current = true;
    scrollEndRef.current?.scrollIntoView({ block: 'end', behavior: 'auto' });
  }, []);

  return {
    scrollContainerRef,
    scrollEndRef,
    scrollToBottomIfFollowing,
    enableFollowOutput,
  };
};

export default useChatAutoScroll;
