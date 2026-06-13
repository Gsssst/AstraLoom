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
  const manualPauseRef = useRef(false);
  const lastScrollTopRef = useRef(0);
  const touchStartYRef = useRef<number | null>(null);
  const interactionStartScrollTopRef = useRef(0);

  const isNearBottom = useCallback(() => {
    const container = scrollContainerRef.current;
    if (!container) return true;
    const distanceToBottom = container.scrollHeight - container.scrollTop - container.clientHeight;
    return distanceToBottom <= bottomThresholdPx;
  }, [bottomThresholdPx]);

  const syncFollowState = useCallback(() => {
    const container = scrollContainerRef.current;
    if (!container) return;
    const currentScrollTop = container.scrollTop;
    const userMovedUp = currentScrollTop < lastScrollTopRef.current;
    const userMovedDown = currentScrollTop > lastScrollTopRef.current;
    const nearBottom = isNearBottom();
    lastScrollTopRef.current = currentScrollTop;

    if (userMovedUp) {
      manualPauseRef.current = true;
      followOutputRef.current = false;
      return;
    }
    if (nearBottom && (!manualPauseRef.current || userMovedDown)) {
      manualPauseRef.current = false;
      followOutputRef.current = true;
      return;
    }
    if (manualPauseRef.current) followOutputRef.current = false;
  }, [isNearBottom]);

  const resumeFollowOutput = useCallback(() => {
    manualPauseRef.current = false;
    followOutputRef.current = true;
  }, []);

  const pauseFollowOutput = useCallback(() => {
    manualPauseRef.current = true;
    followOutputRef.current = false;
  }, []);

  const settleInteractionIntent = useCallback((startingScrollTop: number) => {
    window.requestAnimationFrame(() => {
      const container = scrollContainerRef.current;
      if (!container) return;
      const movedUp = container.scrollTop < startingScrollTop;
      lastScrollTopRef.current = container.scrollTop;
      if (movedUp || !isNearBottom()) {
        pauseFollowOutput();
        return;
      }
      resumeFollowOutput();
    });
  }, [isNearBottom, pauseFollowOutput, resumeFollowOutput]);

  useEffect(() => {
    const container = scrollContainerRef.current;
    if (!container) return;
    lastScrollTopRef.current = container.scrollTop;
    syncFollowState();
    const handleWheel = (event: WheelEvent) => {
      if (!container.contains(event.target as Node | null)) return;
      const startingScrollTop = container.scrollTop;
      if (event.deltaY < 0) {
        pauseFollowOutput();
        return;
      }
      settleInteractionIntent(startingScrollTop);
    };
    const handleTouchStart = (event: TouchEvent) => {
      if (!container.contains(event.target as Node | null)) return;
      touchStartYRef.current = event.touches[0]?.clientY ?? null;
      interactionStartScrollTopRef.current = container.scrollTop;
    };
    const handleTouchMove = (event: TouchEvent) => {
      if (!container.contains(event.target as Node | null)) return;
      const startY = touchStartYRef.current;
      const currentY = event.touches[0]?.clientY;
      if (startY == null || currentY == null) return;
      if (currentY > startY) {
        pauseFollowOutput();
        return;
      }
      settleInteractionIntent(interactionStartScrollTopRef.current);
    };
    container.addEventListener('scroll', syncFollowState, { passive: true });
    window.addEventListener('wheel', handleWheel, { passive: true, capture: true });
    window.addEventListener('touchstart', handleTouchStart, { passive: true, capture: true });
    window.addEventListener('touchmove', handleTouchMove, { passive: true, capture: true });
    return () => {
      container.removeEventListener('scroll', syncFollowState);
      window.removeEventListener('wheel', handleWheel, { capture: true });
      window.removeEventListener('touchstart', handleTouchStart, { capture: true });
      window.removeEventListener('touchmove', handleTouchMove, { capture: true });
    };
  }, [pauseFollowOutput, settleInteractionIntent, syncFollowState]);

  const scrollToBottom = useCallback(() => {
    const container = scrollContainerRef.current;
    if (!container) return;
    container.scrollTop = container.scrollHeight;
    lastScrollTopRef.current = container.scrollTop;
  }, []);

  const scrollToBottomIfFollowing = useCallback(() => {
    if (!followOutputRef.current) return;
    scrollToBottom();
  }, [scrollToBottom]);

  const enableFollowOutput = useCallback(() => {
    resumeFollowOutput();
    scrollToBottom();
  }, [resumeFollowOutput, scrollToBottom]);

  return {
    scrollContainerRef,
    scrollEndRef,
    scrollToBottomIfFollowing,
    enableFollowOutput,
  };
};

export default useChatAutoScroll;
