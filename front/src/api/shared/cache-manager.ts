/**
 * API缓存管理器
 *
 * 提供智能缓存功能，支持TTL、模式匹配和缓存策略
 */

import type { CacheOptions, CacheEntry } from '../types/common';

/**
 * 缓存策略枚举
 */
export enum CacheStrategy {
  CACHE_FIRST = 'cache-first',           // 优先使用缓存
  NETWORK_FIRST = 'network-first',       // 优先使用网络
  STALE_WHILE_REVALIDATE = 'swr',        // 使用缓存并在后台更新
  NO_CACHE = 'no-cache',                 // 不使用缓存
}

/**
 * 缓存项接口
 */
interface CacheItem<T = any> extends CacheEntry<T> {
  key: string;
  tags: string[];
  accessCount: number;
  lastAccessed: number;
  strategy: CacheStrategy;
}

/**
 * 缓存统计信息
 */
export interface CacheStats {
  total: number;
  size: number;
  hits: number;
  misses: number;
  hitRate: number;
  evictions: number;
  itemsByTag: Record<string, number>;
  oldestItem?: number;
  newestItem?: number;
}

/**
 * 缓存事件监听器
 */
export interface CacheEventListeners {
  onHit?: (key: string, item: CacheItem) => void;
  onMiss?: (key: string) => void;
  onSet?: (key: string, item: CacheItem) => void;
  onDelete?: (key: string, item: CacheItem) => void;
  onEvict?: (key: string, item: CacheItem) => void;
}

/**
 * API缓存管理器
 */
export class CacheManager {
  private cache = new Map<string, CacheItem>();
  private config: Required<CacheOptions>;
  private stats: CacheStats = {
    total: 0,
    size: 0,
    hits: 0,
    misses: 0,
    hitRate: 0,
    evictions: 0,
    itemsByTag: {},
  };
  private listeners: CacheEventListeners = {};

  // 定期清理定时器
  private cleanupTimer?: NodeJS.Timeout;

  constructor(config: CacheOptions = {}) {
    this.config = {
      ttl: config.ttl || 5 * 60 * 1000, // 默认5分钟
      maxSize: config.maxSize || 100,    // 默认最多100项
      strategy: config.strategy || CacheStrategy.CACHE_FIRST,
      enableCompression: config.enableCompression || false,
      ...config,
    };

    // 启动定期清理
    this.startCleanup();
  }

  /**
   * 获取缓存项
   */
  get<T = any>(key: string): T | null {
    const item = this.cache.get(key);

    if (!item) {
      this.stats.misses++;
      this.updateHitRate();
      this.listeners.onMiss?.(key);
      return null;
    }

    // 检查是否过期
    if (this.isExpired(item)) {
      this.delete(key);
      this.stats.misses++;
      this.updateHitRate();
      this.listeners.onMiss?.(key);
      return null;
    }

    // 更新访问信息
    item.accessCount++;
    item.lastAccessed = Date.now();

    this.stats.hits++;
    this.updateHitRate();
    this.listeners.onHit?.(key, item);

    return item.data as T;
  }

  /**
   * 设置缓存项
   */
  set<T = any>(
    key: string,
    data: T,
    options: {
      ttl?: number;
      tags?: string[];
      strategy?: CacheStrategy;
    } = {}
  ): void {
    // 检查容量限制
    if (this.cache.size >= this.config.maxSize && !this.cache.has(key)) {
      this.evictLRU();
    }

    const now = Date.now();
    const ttl = options.ttl || this.config.ttl;

    const item: CacheItem<T> = {
      key,
      data,
      timestamp: now,
      ttl,
      tags: options.tags || [],
      accessCount: 0,
      lastAccessed: now,
      strategy: options.strategy || this.config.strategy,
    };

    this.cache.set(key, item);

    // 更新统计
    this.updateStats();
    this.listeners.onSet?.(key, item);
  }

  /**
   * 删除缓存项
   */
  delete(key: string): boolean {
    const item = this.cache.get(key);
    if (!item) {
      return false;
    }

    this.cache.delete(key);
    this.updateStats();
    this.listeners.onDelete?.(key, item);

    return true;
  }

  /**
   * 清除所有缓存
   */
  clear(): void {
    this.cache.clear();
    this.resetStats();
  }

  /**
   * 根据模式清除缓存
   */
  clearByPattern(pattern: string): void {
    const regex = new RegExp(pattern);
    const keysToDelete: string[] = [];

    for (const [key] of this.cache) {
      if (regex.test(key)) {
        keysToDelete.push(key);
      }
    }

    keysToDelete.forEach(key => this.delete(key));
  }

  /**
   * 根据标签清除缓存
   */
  clearByTag(tag: string): void {
    const keysToDelete: string[] = [];

    for (const [key, item] of this.cache) {
      if (item.tags.includes(tag)) {
        keysToDelete.push(key);
      }
    }

    keysToDelete.forEach(key => this.delete(key));
  }

  /**
   * 清除过期缓存
   */
  clearExpired(): number {
    const keysToDelete: string[] = [];

    for (const [key, item] of this.cache) {
      if (this.isExpired(item)) {
        keysToDelete.push(key);
      }
    }

    keysToDelete.forEach(key => this.delete(key));
    return keysToDelete.length;
  }

  /**
   * 检查缓存项是否存在且未过期
   */
  has(key: string): boolean {
    const item = this.cache.get(key);
    if (!item) {
      return false;
    }

    if (this.isExpired(item)) {
      this.delete(key);
      return false;
    }

    return true;
  }

  /**
   * 获取缓存项信息（不返回数据）
   */
  getInfo(key: string): Omit<CacheItem, 'data'> | null {
    const item = this.cache.get(key);
    if (!item || this.isExpired(item)) {
      return null;
    }

    const { data, ...info } = item;
    return info;
  }

  /**
   * 获取所有缓存键
   */
  keys(): string[] {
    return Array.from(this.cache.keys());
  }

  /**
   * 获取匹配模式的所有缓存键
   */
  keysByPattern(pattern: string): string[] {
    const regex = new RegExp(pattern);
    return Array.from(this.cache.keys()).filter(key => regex.test(key));
  }

  /**
   * 获取指定标签的所有缓存键
   */
  keysByTag(tag: string): string[] {
    const keys: string[] = [];
    for (const [key, item] of this.cache) {
      if (item.tags.includes(tag)) {
        keys.push(key);
      }
    }
    return keys;
  }

  /**
   * 设置缓存事件监听器
   */
  setListeners(listeners: CacheEventListeners): void {
    this.listeners = { ...this.listeners, ...listeners };
  }

  /**
   * 获取缓存统计信息
   */
  getStats(): CacheStats {
    this.updateStats();
    return { ...this.stats };
  }

  /**
   * 更新配置
   */
  updateConfig(config: Partial<CacheOptions>): void {
    this.config = { ...this.config, ...config as Required<CacheOptions> };

    // 如果最大容量减少了，可能需要清理
    if (this.cache.size > this.config.maxSize) {
      const itemsToRemove = this.cache.size - this.config.maxSize;
      for (let i = 0; i < itemsToRemove; i++) {
        this.evictLRU();
      }
    }
  }

  /**
   * 预热缓存
   */
  async warmup<T = any>(
    entries: Array<{
      key: string;
      loader: () => Promise<T>;
      options?: { ttl?: number; tags?: string[] };
    }>
  ): Promise<void> {
    const promises = entries.map(async ({ key, loader, options }) => {
      try {
        if (!this.has(key)) {
          const data = await loader();
          this.set(key, data, options);
        }
      } catch (error) {
        console.warn(`Failed to warmup cache key ${key}:`, error);
      }
    });

    await Promise.allSettled(promises);
  }

  /**
   * 根据策略获取缓存
   */
  async getWithStrategy<T = any>(
    key: string,
    loader: () => Promise<T>,
    options: {
      strategy?: CacheStrategy;
      ttl?: number;
      tags?: string[];
    } = {}
  ): Promise<T> {
    const strategy = options.strategy || this.config.strategy;

    switch (strategy) {
      case CacheStrategy.CACHE_FIRST:
        return this.cacheFirst(key, loader, options);

      case CacheStrategy.NETWORK_FIRST:
        return this.networkFirst(key, loader, options);

      case CacheStrategy.STALE_WHILE_REVALIDATE:
        return this.staleWhileRevalidate(key, loader, options);

      case CacheStrategy.NO_CACHE:
      default:
        return loader();
    }
  }

  /**
   * 缓存优先策略
   */
  private async cacheFirst<T>(
    key: string,
    loader: () => Promise<T>,
    options: { ttl?: number; tags?: string[] }
  ): Promise<T> {
    const cached = this.get<T>(key);
    if (cached !== null) {
      return cached;
    }

    const data = await loader();
    this.set(key, data, options);
    return data;
  }

  /**
   * 网络优先策略
   */
  private async networkFirst<T>(
    key: string,
    loader: () => Promise<T>,
    options: { ttl?: number; tags?: string[] }
  ): Promise<T> {
    try {
      const data = await loader();
      this.set(key, data, options);
      return data;
    } catch (error) {
      const cached = this.get<T>(key);
      if (cached !== null) {
        return cached;
      }
      throw error;
    }
  }

  /**
   * 过期时重新验证策略
   */
  private async staleWhileRevalidate<T>(
    key: string,
    loader: () => Promise<T>,
    options: { ttl?: number; tags?: string[] }
  ): Promise<T> {
    const cached = this.get<T>(key);
    const item = this.cache.get(key);

    // 如果有缓存（即使可能过期），先返回
    if (cached !== null || item) {
      // 在后台更新缓存
      loader().then(data => {
        this.set(key, data, options);
      }).catch(error => {
        console.warn(`Failed to revalidate cache key ${key}:`, error);
      });

      return cached || item.data;
    }

    // 没有缓存，直接加载
    const data = await loader();
    this.set(key, data, options);
    return data;
  }

  /**
   * 检查缓存项是否过期
   */
  private isExpired(item: CacheItem): boolean {
    return Date.now() - item.timestamp > item.ttl;
  }

  /**
   * 淘汰最少使用的缓存项
   */
  private evictLRU(): void {
    let oldestKey: string | null = null;
    let oldestAccess = Date.now();

    for (const [key, item] of this.cache) {
      if (item.lastAccessed < oldestAccess) {
        oldestAccess = item.lastAccessed;
        oldestKey = key;
      }
    }

    if (oldestKey) {
      const item = this.cache.get(oldestKey)!;
      this.cache.delete(oldestKey);
      this.stats.evictions++;
      this.listeners.onEvict?.(oldestKey, item);
    }
  }

  /**
   * 更新统计信息
   */
  private updateStats(): void {
    this.stats.total = this.cache.size;
    this.stats.size = this.calculateCacheSize();
    this.stats.itemsByTag = this.calculateItemsByTag();
    this.updateOldestAndNewest();
  }

  /**
   * 计算缓存大小（字节）
   */
  private calculateCacheSize(): number {
    let size = 0;
    for (const [key, item] of this.cache) {
      size += key.length * 2; // 字符串大小估算
      size += JSON.stringify(item.data).length * 2;
    }
    return size;
  }

  /**
   * 计算按标签分组的统计
   */
  private calculateItemsByTag(): Record<string, number> {
    const tagCount: Record<string, number> = {};
    for (const [, item] of this.cache) {
      for (const tag of item.tags) {
        tagCount[tag] = (tagCount[tag] || 0) + 1;
      }
    }
    return tagCount;
  }

  /**
   * 更新最新和最旧项目时间
   */
  private updateOldestAndNewest(): void {
    if (this.cache.size === 0) {
      this.stats.oldestItem = undefined;
      this.stats.newestItem = undefined;
      return;
    }

    let oldest = Date.now();
    let newest = 0;

    for (const [, item] of this.cache) {
      oldest = Math.min(oldest, item.timestamp);
      newest = Math.max(newest, item.timestamp);
    }

    this.stats.oldestItem = oldest;
    this.stats.newestItem = newest;
  }

  /**
   * 更新命中率
   */
  private updateHitRate(): void {
    const total = this.stats.hits + this.stats.misses;
    this.stats.hitRate = total > 0 ? this.stats.hits / total : 0;
  }

  /**
   * 重置统计信息
   */
  private resetStats(): void {
    this.stats = {
      total: 0,
      size: 0,
      hits: 0,
      misses: 0,
      hitRate: 0,
      evictions: 0,
      itemsByTag: {},
    };
  }

  /**
   * 启动定期清理
   */
  private startCleanup(): void {
    // 每分钟清理一次过期项
    this.cleanupTimer = setInterval(() => {
      this.clearExpired();
    }, 60 * 1000);
  }

  /**
   * 停止定期清理
   */
  stopCleanup(): void {
    if (this.cleanupTimer) {
      clearInterval(this.cleanupTimer);
      this.cleanupTimer = undefined;
    }
  }

  /**
   * 销毁缓存管理器
   */
  destroy(): void {
    this.stopCleanup();
    this.clear();
  }
}