import '@testing-library/jest-dom';
import { TextEncoder, TextDecoder } from 'util';
import React from 'react';
import { act } from 'react-dom/test-utils';

// Polyfill TextEncoder/TextDecoder for react-router-dom
global.TextEncoder = TextEncoder as any;
global.TextDecoder = TextDecoder as any;

// Polyfill React.act for React 19 compatibility
(React as any).act = act;

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock ResizeObserver
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  readyState = MockWebSocket.OPEN;
  onopen: (() => void) | null = null;
  onclose: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onerror: (() => void) | null = null;

  constructor(url: string) {
    setTimeout(() => this.onopen?.(), 0);
  }

  send(data: string) {}
  close() {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.();
  }
}

global.WebSocket = MockWebSocket as any;

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(() => null),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
  length: 0,
  key: jest.fn(),
};
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

// Mock IntersectionObserver
class MockIntersectionObserver {
  observe = jest.fn();
  unobserve = jest.fn();
  disconnect = jest.fn();
  root = null;
  rootMargin = '';
  thresholds = [];
}
global.IntersectionObserver = MockIntersectionObserver as any;

// Mock scrollTo
window.scrollTo = jest.fn();

// Suppress React 19 act warnings in tests
const originalError = console.error;
console.error = (...args: any[]) => {
  if (
    typeof args[0] === 'string' &&
    args[0].includes('ReactDOMTestUtils.act')
  ) {
    return;
  }
  originalError.call(console, ...args);
};
