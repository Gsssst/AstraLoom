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

  const pauseFollowOutput = useCallback(() => {
    manualPauseRef.current = true;
    followOutputRef.current = false;
  }, []);

  useEffect(() => {
    const container = scrollContainerRef.current;
    if (!container) return;
    lastScrollTopRef.current = container.scrollTop;
    syncFollowState();
    const handleWheel = (event: WheelEvent) => {
      if (event.deltaY < 0) pauseFollowOutput();
    };
    const handleTouchStart = (event: TouchEvent) => {
      touchStartYRef.current = event.touches[0]?.clientY ?? null;
    };
    const handleTouchMove = (event: TouchEvent) => {
      const startY = touchStartYRef.current;
      const currentY = event.touches[0]?.clientY;
      if (startY == null || currentY == null) return;
      if (currentY > startY) pauseFollowOutput();
    };
    container.addEventListener('scroll', syncFollowState, { passive: true });
    container.addEventListener('wheel', handleWheel, { passive: true });
    container.addEventListener('touchstart', handleTouchStart, { passive: true });
    container.addEventListener('touchmove', handleTouchMove, { passive: true });
    return () => {
      container.removeEventListener('scroll', syncFollowState);
      container.removeEventListener('wheel', handleWheel);
      container.removeEventListener('touchstart', handleTouchStart);
      container.removeEventListener('touchmove', handleTouchMove);
    };
  }, [pauseFollowOutput, syncFollowState]);

  const scrollToBottomIfFollowing = useCallback(() => {
    if (!followOutputRef.current) return;
    scrollEndRef.current?.scrollIntoView({ block: 'end', behavior: 'auto' });
  }, []);

  const enableFollowOutput = useCallback(() => {
    manualPauseRef.current = false;
    followOutputRef.current = true;
    scrollEndRef.current?.scrollIntoView({ block: 'end', behavior: 'auto' });
    const container = scrollContainerRef.current;
    if (container) lastScrollTopRef.current = container.scrollTop;
  }, []);

  return {
    scrollContainerRef,
    scrollEndRef,
    scrollToBottomIfFollowing,
    enableFollowOutput,
  };
};

export default useChatAutoScroll;
